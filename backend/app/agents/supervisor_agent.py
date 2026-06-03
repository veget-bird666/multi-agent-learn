"""
Supervisor 智能体：协调多智能体协作，动态决策下一步
"""
from app.core.llm import supervisor_llm
from app.graph.state import LearningState
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, field_validator
from typing import Optional


class SupervisorOutput(BaseModel):
    """Supervisor 的输出结构"""
    next_agent: str
    # "profile_agent" / "chat_agent" / "rewrite_node" / "FINISH"
    reasoning: str = ""

    # 当 next_agent="profile_agent" 时，告诉 profile_agent 重点更新哪些维度
    profile_update_hint: Optional[str] = None

    @field_validator("profile_update_hint", mode="before")
    @classmethod
    def clean_profile_update_hint(cls, v):
        """兼容 LLM 返回 {} 空字典的情况"""
        if isinstance(v, dict):
            return None
        return v


SYSTEM_PROMPT = """你是一个学习系统的调度员（Supervisor），负责协调多个智能体协作，为学生提供个性化学习支持。

## 可用智能体
- **chat_agent**：常规对话回复，生成最终回复。**必须是最后一个被调用的智能体**，它生成回复后会清空消息状态，本轮对话结束。
- **profile_agent**：构建或更新学生画像（6个维度：知识基础、认知风格、学习节奏、兴趣领域、易错点偏好、学习目标）。当需要抽取或更新画像时调用。
- **tool_node**：调用各类工具（分析图片等）。当学生上传了图片需要分析，或需要调用外部工具时调用。
- **resource_agent**：多模态学习资源生成。可生成文档、PPT、试卷、检索图片/视频。**当学生明确要求生成或制作某种学习资源时调用**。
- **rewrite_node**：查询重写，将用户消息重写为适合搜索的查询。当学生需要系统性地学习某个知识点时调用，它会自动触发路径规划。

## 决策规则
按优先级从高到低判断：

0. **本轮资源已生成检查**：检查"已生成资源数"，如果 > 0，说明本轮已经生成过资源了，**禁止再调 resource_agent**，继续判断后续规则
1. **新消息包含图片或需要调用工具** → tool_node
2. **学生明确要求生成/制作特定资源，且资源数为0** → resource_agent
3. **画像未构建**（profile=空），且对话信息足够抽取特征 → profile_agent
4. **画像已存在，但新对话中出现与画像矛盾或明显补充的信息**（例如学生说"其实我更喜欢看公式推导"而现有画像标注为"举例型"）→ profile_agent，并填写 profile_update_hint 说明要更新的维度
5. **学生提出要学习某个知识点或需要学习路线** → rewrite_node（重写需求后自动触发路径规划）
6. **学生提出要学习某个知识点或需要学习路线，且学习路线已存在** → chat_agent（直接回复学习路线，无需重新规划）
7. **以上都不满足，只需正常回复** → chat_agent
8. **本轮交互已结束，无需后续操作** → FINISH

## 重要：区分"生成资源" vs "学习知识点"
- **生成资源**：用户说"帮我生成/制作/创建PPT/文档/资料/试卷" → resource_agent
- **学习知识点**：用户说"我想学XX/XX怎么用/帮我讲解XX" → rewrite_node
- 如果用户**既想学某个知识点，又要生成资源**（如"我想学C语言指针，帮我生成教学PPT"），优先走 resource_agent 先满足资源需求
- 如果用户明确提到"PPT/文档/试卷"等资源类型词，优先走 resource_agent


## profile_update_hint 示例与要求

###要求：
- 仅在需要更新画像时才填写
- 如果history中最后的信息已经说明了用户画像已更新，则不需要再重复调用profile_agent，直接调用其他agent

###示例：
- 场景 1：学生开局说“你好”、“你能帮我做什么”等问候语或闲聊 → 不调用profile_agent等其他智能体，直接调用chat_agent
- 场景 2：学生说"我想学C语言"，画像未建 → 调用profile_agent ，并把重点设置为更新“兴趣领域”和“学习目标”维度
- 场景 3：画像已建，学生又说"其实我更喜欢看公式推导" → profile_agent（带 update_hint）
- 场景 4：画像已建，消息是常规提问，如“什么是C语言？”、“这个题怎么做”  → 不调用profile_agent，直接调用chat_agent



## 特殊规则
- 如果 `message` 为空字符串且对话历史已经包含回复，说明本轮已处理完毕，**立即 FINISH**
- 不要因为画像未构建就去调用 profile_agent（没有新消息无法抽取特征）

## 重要原则
- 一次只调用一个智能体，该智能体执行完后会回到你这里继续判断
- **chat_agent 只应出现在最后一步**，它生成回复后系统会自动结束本轮。不要在 chat_agent 之后再调度任何其他 agent。
- 如果拿不定主意，优先选 chat_agent，让对话继续
- 系统最大运行轮次为 10，不要浪费轮次在无意义的循环上"""


def supervisor_agent(state: LearningState):
    """监督智能体：根据当前状态决策下一步"""
    history = state.get("history", [])
    profile = state.get("profile")
    latest_message = state.get("message", "")
    turn_count = state.get("operation", 1)
    learning_path = state.get("learning_path")
    source_count = len(state.get("generated_resources", []))

    # === 调试日志 ===
    print(f"\n{'='*60}")
    print(f"[Supervisor] 第 {turn_count} 轮决策")
    print(f"[Supervisor]   message: {latest_message[:60] + '...' if len(latest_message) > 60 else latest_message}")
    print(f"[Supervisor]   画像: {'已构建' if profile else '未构建'}")
    print(f"[Supervisor]   路径: {'已规划' if learning_path else '未规划'}")
    print(f"[Supervisor]   资源数: {source_count}")
    print(f"[Supervisor]   history 条数: {len(history)}")
    if state.get("profile_update_hint"):
        print(f"[Supervisor]   残留的 update_hint: {state['profile_update_hint']}")
    # ==============

    # 构建画像摘要（给 LLM 看）
    if profile:
        profile_summary = profile.model_dump_json(indent=2, exclude_none=True)
        profile_status = "✅ 已构建"
    else:
        profile_summary = "暂无"
        profile_status = "❌ 未构建"

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("system", (
            "=== 当前状态 ===\n"
            "学生画像状态：{profile_status}\n"
            "画像详情：{profile_summary}\n"
            "对话轮次：第 {turn_count} 轮\n"
            "最新用户消息：{latest_message}\n"
            "学习路径状态：{path_status}\n"
            "已生成资源数：{resource_count}（若>0 表示已经生成过，绝对不许再调用resource_agent）\n"
            "=== 提示 ===\n"
            "对话历史中可能包含各 Agent 的工作报告，格式为 [agent_name] 内容。\n"
            "如果上一个 Agent 已完成某项工作（如资源生成、画像更新、路径规划），\n"
            "请据此判断下一步，不要重复调度同一 Agent。\n"
            "=== 对话历史 ==="
        )),
        ("placeholder", "{history}"),
    ])

    path_status = f"已规划（{len(learning_path)} 个阶段）" if learning_path else "未规划"
    generated = state.get("generated_resources", [])

    chain = prompt | supervisor_llm.with_structured_output(SupervisorOutput)
    result = chain.invoke({
        "history": history,
        "profile_status": profile_status,
        "profile_summary": profile_summary,
        "turn_count": turn_count,
        "latest_message": latest_message,
        "path_status": path_status,
        "resource_count": source_count,
    })

    # === 调试日志：展示决策结果 ===
    print(f"[Supervisor] ➡️  决策: next_agent={result.next_agent}")
    if result.reasoning:
        print(f"[Supervisor]   reasoning: {result.reasoning}")
    if result.profile_update_hint:
        print(f"[Supervisor]   update_hint: {result.profile_update_hint}")
    print(f"{'='*60}")

    return_result = {
        "next_agent": result.next_agent,
        "next_reasoning": result.reasoning,
        "operation": turn_count + 1,  # 轮次自增，防止无限循环
    }

    # 如果 Supervisor 给出了画像更新提示，传给 state
    if result.profile_update_hint:
        return_result["profile_update_hint"] = result.profile_update_hint

    # === 代码层安全阀 ===
    # 防止 rewrite_node 循环：路径已规划时不再重新规划
    if result.next_agent == "rewrite_node" and learning_path:
        print(f"[Supervisor] 安全阀: 路径已规划，拦截 rewrite_node → chat_agent")
        return_result["next_agent"] = "chat_agent"

    return return_result




