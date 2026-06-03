"""
智能体2：多智能体协同资源生成（子图入口）
从原来包含所有生成逻辑的函数，重构为子图包装器。

职责：
  1. 从主图 LearningState 提取子图所需字段
  2. 调用 resource_subgraph 运行完整的生成流程
  3. 将子图结果映射回主图 LearningState

子图内部（resource_subgraph/）：
  planner → Send() → doc_generator / exam_generator / ppt_generator / image_retriever / video_retriever → collector
"""
import time

from app.graph.state import LearningState
from app.resource_subgraph.subgraph import resource_subgraph
from app.models.resources import Resource
from langchain_core.messages import AIMessage


def resource_agent(state: LearningState) -> dict:
    """
    资源生成智能体 — 子图包装器。

    从主图 state 中提取字段，调用子图，将结果合并回主图。
    """
    knowledge_point = state.get("knowledge_point", "")
    rewritten_query = state.get("rewritten_query", "")
    raw_message = state.get("message", "")

    # 主题提取：rewritten_query > knowledge_point > 原始消息
    topic = rewritten_query or knowledge_point
    if not topic:
        # 从原始消息中提取主题：去掉"生成/制作/创建PPT/文档"等指令词
        topic = _extract_topic_from_message(raw_message)

    if not topic:
        print(f"[ResourceAgent] ⚠️ 未指定知识点，跳过资源生成")
        return {
            "generated_resources": [],
            "response": "请先指定要学习的内容或知识点。",
        }

    print(f"\n{'='*60}")
    print(f"[ResourceAgent] 🚀 启动资源生成子图")
    print(f"[ResourceAgent]   知识点: {knowledge_point}")
    print(f"[ResourceAgent]   重写查询: {rewritten_query}")
    print(f"[ResourceAgent]   提取主题: {topic}")
    print(f"{'='*60}")

    # ── 1. 准备子图输入 ──────────────────────────────
    sub_state = {
        "knowledge_point": topic,        # 用 topic 填充，让子图知道生成什么
        "profile": state.get("profile"),
        "message": state.get("message", ""),
        "rewritten_query": rewritten_query,
        "resource_plan": [],
        "generated_resources": [],
        "response": None,
    }

    # ── 2. 运行子图 ──────────────────────────────────
    try:
        result = resource_subgraph.invoke(sub_state)
    except Exception as e:
        print(f"[ResourceAgent] ❌ 子图运行异常: {e}")
        return {
            "generated_resources": [],
            "response": f"资源生成过程出现异常：{str(e)}",
        }

    # ── 3. 结果映射回主图 ────────────────────────────
    new_resources = result.get("generated_resources", [])
    sub_response = result.get("response")

    print(f"\n[ResourceAgent] ✅ 子图完成，共生成 {len(new_resources)} 项资源")
    for r in new_resources:
        print(f"   - {r.type}: {r.title}")

    # 为每个资源补上 timestamp 后缀避免 id 冲突
    for r in new_resources:
        if not r.id.endswith(str(int(time.time()))):
            r.id = f"{r.id}_{int(time.time())}"

    # 构建 AIMessage 摘要加入对话历史
    type_labels = {
        "document": "📄 文档", "exam": "📝 试卷", "ppt": "📊 PPT",
        "image": "🖼️ 图片", "video": "🎬 视频",
    }
    if new_resources:
        resource_summary = "，".join(
            f"{type_labels.get(r.type.value if hasattr(r.type, 'value') else r.type, r.type)}「{r.title}」"
            for r in new_resources
        )
        agent_msg = AIMessage(
            content=(
                f"[resource_agent] 已为知识点「{topic}」完成资源生成。"
                f"共 {len(new_resources)} 项：{resource_summary}"
            )
        )
        updated_history = list(state.get("history") or []) + [agent_msg]
    else:
        updated_history = state.get("history") or []

    return {
        "generated_resources": new_resources,
        "history": updated_history,
        "response": sub_response or f"已生成 {len(new_resources)} 项学习资源。",
    }


def _extract_topic_from_message(message: str) -> str:
    """从原始消息中提取学习主题。

    简单策略：去标点取前 60 个字作为主题。
    planner 中的 LLM 会自动从上下文中理解实际的知识点。
    """
    if not message or len(message.strip()) < 3:
        return ""
    import re
    cleaned = re.sub(r"[，。！？、；：""''【】《》（）\-\+\.,\/\\#!?~]", "", message)
    return cleaned[:60].strip()
