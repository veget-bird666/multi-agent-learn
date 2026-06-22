"""
Supervisor 智能体：协调多智能体协作，动态决策下一步
采用 Plan-and-Execute 模式：LLM 只参与一次规划，后续按计划推进
"""
from typing import List, Optional
from app.core.llm import supervisor_llm
from app.graph.state import LearningState
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, field_validator


class SupervisorOutput(BaseModel):
    """Supervisor 的输出结构"""
    next_agent: str
    # "profile_agent" / "chat_agent" / "rewrite_node" / "path_agent" / "resource_agent" / "FINISH"
    reasoning: str = ""

    # 完整执行计划（按顺序），LLM 仅在首次规划时填写
    execution_plan: List[str] = []

    # 当 next_agent="profile_agent" 时，告诉 profile_agent 重点更新哪些维度
    profile_update_hint: Optional[str] = None

    @field_validator("profile_update_hint", mode="before")
    @classmethod
    def clean_profile_update_hint(cls, v):
        """兼容 LLM 返回 {} 空字典的情况"""
        if isinstance(v, dict):
            return None
        return v


SYSTEM_PROMPT = """你是一个学习系统的调度员（Supervisor），负责规划并协调多个智能体协作，为学生提供个性化学习支持。

## 可用智能体
- **chat_agent**：常规对话回复，生成最终回复。**必须是最后一个被调用的智能体**，它生成回复后会清空消息状态，本轮对话结束。
- **profile_agent**：构建或更新学生画像（6个维度：知识基础、认知风格、学习节奏、兴趣领域、易错点偏好、学习目标）。当需要抽取或更新画像时调用。
- **tool_node**：调用各类工具（分析图片等）。当学生上传了图片需要分析，或需要调用外部工具时调用。
- **resource_agent**：多模态学习资源生成。可生成文档、PPT、试卷、检索图片/视频。
- **path_agent**：学习路径规划。根据画像和知识点规划学习步骤。
- **rewrite_node**：查询重写，将用户原始消息重写为适合搜索的搜索查询，**为后续 RAG 检索提供精准的搜索词**。

## Plan-and-Execute 机制
1. **你参与规划和反思两个阶段**：首次分析请求创建计划，计划执行后评估结果
2. **系统自动执行**：创建计划后，系统会按顺序逐个调用计划中的智能体，执行期间不调用你
3. **计划执行完毕后进入反思阶段**：你评估执行结果，可以：
   - 如果结果已满足需求 → **chat_agent** 生成最终回复（不设 execution_plan）
   - 如果还需要补充 → 创建新计划继续执行（设 execution_plan）
4. **plan 不要包含 chat_agent**：它会由你在反思阶段选择调用

## 决策规则

### 规划阶段（execution_plan 为空）
当用户的请求需要多个步骤协作时，请创建 execution_plan 规划完整流程。
**execution_plan 中的智能体将按顺序执行，每个执行完后自动进入下一个。**

常见场景的计划示例：
- 用户想学习某个知识点，画像已建 → plan: ["rewrite_node", "path_agent"]
- 用户想学习某个知识点，画像未建且信息足够 → plan: ["profile_agent", "rewrite_node", "path_agent"]
- 用户想学习某个知识点，learning_path 已存在 → 不创建 plan，直接 chat_agent
- 用户想生成特定资源（PPT/文档/试卷），画像已建 → plan: ["rewrite_node", "resource_agent"]
- 用户想生成特定资源，画像未建 → plan: ["profile_agent", "rewrite_node", "resource_agent"]
- 用户上传了图片需要分析 → plan: ["tool_node"]
- 用户闲聊/问候/提问 → 不创建 plan，直接 chat_agent
- 用户需更新画像（新信息与现有画像矛盾）→ plan: ["profile_agent", ...后续根据消息判断]

### 反思阶段（计划刚执行完毕）
当计划中的步骤都已执行完，你会看到执行结果（如 learning_path 已规划、资源已生成等）。
此时你处于反思阶段：
1. 检查结果是否完整且满足用户需求
2. 如果结果已足够 → **chat_agent**（生成回复展示给学生，不设 execution_plan）
3. 如果还需要补充 → **创建新计划** 继续处理（设 execution_plan）
4. 如果不确定 → **chat_agent**，让对话继续

### 直接回复（无计划时）
如果不需要创建计划，按以下优先级选 next_agent：
1. 新消息包含图片或需要调用工具 → tool_node
2. 画像未构建，且对话信息足够抽取 → profile_agent
3. 画像需更新 → profile_agent（填 profile_update_hint）
4. 以上都不满足 → chat_agent
5. 本轮交互已结束 → FINISH

## 重要原则
- **创建 plan 时请考虑全面**，把需要做的步骤一次性规划好
- **chat_agent 不应出现在 plan 中**——计划执行完后系统会自动调用它
- 一次只调用一个智能体
- 系统最大运行轮次为 10，不要规划超过 5 个步骤
- 如果拿不定主意，优先选 chat_agent，让对话继续
"""


async def supervisor_agent(state: LearningState):
    """监督智能体：Plan-and-Execute 模式"""
    plan = state.get("execution_plan", [])
    plan_step = state.get("current_plan_step", -1)
    history = state.get("history", [])
    profile = state.get("profile")
    latest_message = state.get("message", "")
    turn_count = state.get("operation", 1)
    learning_path = state.get("learning_path")
    source_count = len(state.get("generated_resources", []))
    rewritten_query = state.get("rewritten_query", "")

    # === 调试日志 ===
    print(f"\n{'='*60}")
    print(f"[Supervisor] 第 {turn_count} 轮决策")
    print(f"[Supervisor]   message: {latest_message[:60] + '...' if len(latest_message) > 60 else latest_message}")
    print(f"[Supervisor]   重写请求: {rewritten_query[:60] + '...' if rewritten_query else '(无)'}")
    print(f"[Supervisor]   画像: {'已构建' if profile else '未构建'}")
    print(f"[Supervisor]   路径: {'已规划' if learning_path else '未规划'}")
    print(f"[Supervisor]   资源数: {source_count}")
    print(f"[Supervisor]   计划: {plan}")
    print(f"[Supervisor]   计划步骤: {plan_step}")
    print(f"[Supervisor]   history 条数: {len(history)}")
    if state.get("profile_update_hint"):
        print(f"[Supervisor]   残留的 update_hint: {state['profile_update_hint']}")

    # === 消息为空 = 本轮已处理完毕 ===
    if not latest_message:
        print(f"[Supervisor]   message 为空，直接 FINISH")
        print(f"{'='*60}")
        return {"next_agent": "FINISH", "operation": turn_count + 1}

    # ════════════════════════════════════════════════════════
    # Plan Execution Mode：按计划推进，不调 LLM
    # ════════════════════════════════════════════════════════
    if plan and plan_step >= 0:
        next_step = plan_step + 1
        if next_step < len(plan):
            next_agent = plan[next_step]
            print(f"[Supervisor]   执行计划步骤 {next_step+1}/{len(plan)}: {next_agent}")
            print(f"{'='*60}")
            return {
                "next_agent": next_agent,
                "current_plan_step": next_step,
                "operation": turn_count + 1,
            }
        else:
            # 计划执行完毕 → 清空计划，让代码落到下方 LLM 反思（不直接转 chat_agent）
            print(f"[Supervisor]   计划执行完毕，进入 LLM 反思阶段")
            plan = []
            plan_step = -1
            # 继续往下走，不 return

    # ════════════════════════════════════════════════════════
    # LLM Mode：规划阶段（首次） 或 反思阶段（计划执行后）
    # ════════════════════════════════════════════════════════
    llm_mode = "反思" if state.get("execution_plan") else "规划"
    print(f"[Supervisor]   LLM 模式: {llm_mode}")

    # 构建画像摘要
    if profile:
        profile_summary = profile.model_dump_json(indent=2, exclude_none=True)
        profile_status = " 已构建"
    else:
        profile_summary = "暂无"
        profile_status = " 未构建"

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
            "本轮重写后的搜索查询（可用于判断是否经过 rewrite_node）：{rewritten_query}\n"
            "=== 对话历史 ==="
        )),
        ("placeholder", "{history}"),
    ])

    path_status = f"已规划（{len(learning_path)} 个阶段）" if learning_path else "未规划"

    chain = prompt | supervisor_llm.with_structured_output(SupervisorOutput)
    result = await chain.ainvoke({
        "history": history,
        "profile_status": profile_status,
        "profile_summary": profile_summary,
        "turn_count": turn_count,
        "latest_message": latest_message,
        "path_status": path_status,
        "resource_count": source_count,
        "rewritten_query": rewritten_query or "(无)",
    })

    # === 调试日志：展示决策结果 ===
    print(f"[Supervisor]   决策: next_agent={result.next_agent}")
    if result.reasoning:
        print(f"[Supervisor]   reasoning: {result.reasoning}")
    if result.execution_plan:
        print(f"[Supervisor]   执行计划: {result.execution_plan}")
    if result.profile_update_hint:
        print(f"[Supervisor]   update_hint: {result.profile_update_hint}")
    print(f"{'='*60}")

    return_result = {
        "next_agent": result.next_agent,
        "next_reasoning": result.reasoning,
        "operation": turn_count + 1,
    }

    # 始终设置计划状态：有新计划则开始执行，否则清空（反思阶段也依赖此机制）
    return_result["execution_plan"] = result.execution_plan or []
    return_result["current_plan_step"] = 0 if result.execution_plan else -1

    # 如果 Supervisor 给出了画像更新提示
    if result.profile_update_hint:
        return_result["profile_update_hint"] = result.profile_update_hint

    return return_result
