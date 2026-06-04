"""
智能体3：个性化学习路径规划
职责：根据学生画像和知识点，规划科学、动态的学习路径
"""
from app.graph.state import LearningState
from app.core.llm import path_llm
from app.models.resources import LearningPathPlan, LearningPathStep
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

SYSTEM_PROMPT = """你是一个专业的学习路径规划师，负责为学生制定个性化学习路径。

## 输入信息
- **学生画像**：包含知识基础、认知风格、学习节奏、兴趣领域、易错点偏好、学习目标
- **学习知识点/需求**：学生想要学习的主题或知识点

## 输出要求
规划一个科学、合理的学习路径，需满足：
1. **由浅入深**：从基础到进阶，循序渐进
2. **适配画像**：根据学生的认知风格和学习节奏调整每阶段的深度和节奏
   - 举例型 vs 公式型：举例型学生多给案例，公式型学生多给原理推导
   - 慢节奏学生：拆分更细，每阶段内容更少
   - 实践型学生：尽早安排实操环节
3. **目标导向**：路径终点要能达成学生的学习目标
4. **每阶段明确**：每个阶段名称、知识点、学习内容和要求都要具体

## 步骤拆分原则
- 将知识点拆分为 3-7 个阶段
- 每个阶段聚焦 2-4 个核心知识点
- 每个阶段标注难度等级，从 easy 逐步过渡到 hard"""


def path_agent(state: LearningState) -> dict:
    """根据画像和知识点规划学习路径"""
    profile = state.get("profile")
    message = state.get("message", "")
    knowledge_point = state.get("knowledge_point")
    rewritten_query = state.get("rewritten_query", "")

    print(f"\n[PathAgent]   开始规划学习路径...")
    print(f"[PathAgent]   knowledge_point: {knowledge_point}")
    print(f"[PathAgent]   原始消息: {message[:40]}...")
    if rewritten_query:
        print(f"[PathAgent]   重写查询: {rewritten_query[:60]}...")

    # 构建画像摘要（给 LLM 参考）
    profile_summary = "暂无画像数据"
    if profile:
        profile_summary = profile.model_dump_json(indent=2, exclude_none=True)

    # 学习需求：优先使用重写后的查询，其次用原始消息
    search_query = rewritten_query or knowledge_point or message

    # === RAG 检索：从知识库获取相关上下文 ===
    try:
        from app.rag.retriever import search_knowledge, format_rag_results
        rag_results = search_knowledge(search_query, k=5)
        rag_context = format_rag_results(rag_results)
    except Exception as e:
        print(f"[PathAgent]  RAG 检索异常（跳过）: {e}")
        rag_context = ""

    # 当有检索结果时，添加标题引导 LLM 参考
    rag_context_header = ""
    if rag_context:
        rag_context_header = "=== 知识库参考内容（请据此制定路径）==="

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("system", (
            "=== 学生画像 ===\n"
            "{profile_summary}\n\n"
            "=== 学习需求 ===\n"
            "用户消息：{message}\n"
            "提取的知识点：{knowledge_point}\n"
            "{rag_context_header}\n"
            "{rag_context}"
        )),
        ("user", "请根据以上信息，为学生制定一份个性化的学习路径规划。"),
    ])

    chain = prompt | path_llm.with_structured_output(LearningPathPlan)
    result = chain.invoke({
        "profile_summary": profile_summary,
        "message": message,
        "knowledge_point": search_query,
        "rag_context": rag_context,
        "rag_context_header": rag_context_header,
    })

    print(f"[PathAgent]  路径规划完成，共 {len(result.steps)} 个阶段")
    for step in result.steps:
        print(f"[PathAgent]   阶段{step.order}: {step.stage_name} ({step.difficulty})")

    # 构造回复摘要
    steps_summary = "\n".join(
        f"{s.order}. **{s.stage_name}**（{s.difficulty}）：{s.description}"
        for s in result.steps
    )
    response = (
        f"我已根据你的情况规划了学习路径，共 {len(result.steps)} 个阶段：\n\n"
        f"{steps_summary}\n\n"
        f"**预估总时长**：{result.total_duration_estimate or '视个人情况而定'}\n"
    )
    if result.learning_style_advice:
        response += f"\n**学习建议**：{result.learning_style_advice}"

    # 构造路径摘要（给后续 chat_agent 看）
    path_summary_lines = "\n".join(
        f"  阶段{s.order}：{s.stage_name}（{s.difficulty}）"
        f" - {s.description}。知识点：{', '.join(s.knowledge_points)}"
        for s in result.steps
    )
    path_system_msg = AIMessage(
        content=(
            f"[path_agent] 系统：已生成个性化学习路径，共 {len(result.steps)} 个阶段：\n"
            f"{path_summary_lines}"
        )
    )

    updated_history = list(state.get("history") or []) + [path_system_msg]

    return {
        "learning_path": [s.model_dump() for s in result.steps],
        "current_step": 0,
        "knowledge_point": knowledge_point or message,
        "response": response,
        "history": updated_history,
    }
