"""
资源规划器（planner）
职责：根据学生画像 + 知识点 + 用户消息，一次决策要生成哪些类型的资源。
      通过 Send() 并行派发给各生成器，不串行调度。
"""
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

from app.core.llm import tool_llm
from app.resource_subgraph.state import ResourceSubState

# ── 结构化输出 ──────────────────────────────────────────

AVAILABLE_RESOURCES = ["document", "exam", "ppt", "image", "video", "mindmap"]


class ResourcePlan(BaseModel):
    """资源生成计划"""
    reasoning: str = Field(default="", description="决策理由")
    cleaned_topic: str = Field(
        default="",
        description=(
            "从用户消息中提取的纯净知识点/主题名称（去掉'生成/PPT/文档'等指令词）。"
            "如用户说'我想学C语言指针，帮我生成PPT'，则提取为'C语言指针'。"
            "控制在 20 字以内。"
        ),
    )
    resource_types: list[str] = Field(
        default=["document"],
        description=f"要生成的资源类型列表，可选：{', '.join(AVAILABLE_RESOURCES)}",
    )


# ── Prompt ──────────────────────────────────────────────

SYSTEM_PROMPT = """你是一个学习资源规划师，负责根据学生情况决定要生成哪些学习资源。

## 可用资源类型
- **document**：Markdown 格式的系统性讲解文档。适合任何知识点，作为主要学习材料。
- **exam**：JSON 格式的试卷（含选择题、填空题、简答题等）。适合需要检验掌握程度时。
- **ppt**：PPT 课件。适合需要系统性展示或复习时。
- **image**：从知识库检索现有图片/图表。适合需要直观理解时。
- **video**：从知识库检索现有视频。适合需要动态演示时。
- **mindmap**：Mermaid 思维导图。适合需要梳理知识结构、复习总结时。

## 决策原则
1. **document 是兜底选项** — 至少生成一份文档作为主要学习材料
2. **有知识点需要系统性学习** → document + ppt
3. **学生提到"做题"、"练习"、"测验"、"考试"** → exam（可搭配 document）
4. **知识点涉及可视化内容**（流程图、架构图等）→ image
5. **知识点涉及操作演示**（编程、实验等）→ video
6. **不要贪多** — 每次只生成 1-3 种最合适的资源，质量优先

## 输出
1. **cleaned_topic**：从用户消息中提取的纯净知识点名称。去掉"生成/制作/PPT/文档/教案/帮我"等指令词。
   例如"我想学C语言指针，帮我生成PPT" → "C语言指针"；"能帮我生成一份数据结构PPT吗" → "数据结构"
2. **resource_types**：列出要生成的资源类型列表。注意不要贪多，1-3 种最合适。"""


# ── 节点函数 ─────────────────────────────────────────────

def resource_planner(state: ResourceSubState) -> dict:
    """
    Planner 节点：读取子图 state，输出 resource_plan。
    """
    knowledge_point = state.get("knowledge_point", "")
    profile = state.get("profile")
    message = state.get("message", "")
    rewritten = state.get("rewritten_query", "")

    print(f"\n[ResourcePlanner]  开始规划...")
    print(f"[ResourcePlanner]   知识点: {knowledge_point}")
    print(f"[ResourcePlanner]   消息: {message[:60]}...")

    # 构建上下文
    profile_summary = "暂无画像"
    if profile:
        items = []
        for label, val in [
            ("认知风格", profile.cognitive_style),
            ("知识基础", profile.knowledge_base),
            ("兴趣领域", ", ".join(profile.interest_areas[:3]) if profile.interest_areas else None),
            ("学习目标", profile.goal),
        ]:
            if val:
                items.append(f"{label}={val}")
        if items:
            profile_summary = "；".join(items)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", (
            "### 学生画像\n{profile_summary}\n\n"
            "### 用户消息\n{message}\n\n"
            "### 知识点\n{knowledge_point}\n\n"
            "### 重写查询\n{rewritten}\n\n"
            "请规划本次需要生成哪些类型的资源。"
        )),
    ])

    chain = prompt | tool_llm.with_structured_output(ResourcePlan)

    try:
        result = chain.invoke({
            "profile_summary": profile_summary,
            "message": message or "（无）",
            "knowledge_point": knowledge_point or "（未指定）",
            "rewritten": rewritten or "（无）",
        })

        plan = result.resource_types
        # 去重 + 仅保留合法值 + 确保 document 兜底
        plan = list(dict.fromkeys(t for t in plan if t in AVAILABLE_RESOURCES))
        if not plan:
            plan = ["document"]

        # 提取纯净 topic
        cleaned_topic = (result.cleaned_topic or knowledge_point or "").strip()
        if not cleaned_topic or len(cleaned_topic) < 2:
            cleaned_topic = knowledge_point

        print(f"[ResourcePlanner]  规划完成: {plan}")
        print(f"[ResourcePlanner]   cleaned_topic: {cleaned_topic}")
        if result.reasoning:
            print(f"[ResourcePlanner]   reasoning: {result.reasoning}")

    except Exception as e:
        print(f"[ResourcePlanner]  LLM 调用失败: {e}，兜底为 document")
        plan = ["document"]
        cleaned_topic = knowledge_point

    return {"resource_plan": plan, "cleaned_topic": cleaned_topic}
