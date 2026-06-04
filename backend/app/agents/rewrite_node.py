"""
Graph 节点：查询重写节点
职责：将用户原始消息重写为适合 RAG 检索的搜索查询
位置：path_agent 之前，为路径规划提供精准搜索需求
"""
from app.graph.state import LearningState
from app.core.query_rewrite import rewrite_query


def rewrite_node(state: LearningState) -> dict:
    """
    读取用户消息，重写为搜索查询，存入 state.rewritten_query。
    """
    message = state.get("message", "")
    profile = state.get("profile")

    print(f"\n[RewriteNode]   开始重写查询...")
    print(f"[RewriteNode]   message: {message[:50]}...")

    # 构建上下文摘要（给 rewrite 模型参考）
    context_parts = []
    if profile:
        context_parts.append(
            f"学生画像：认知风格={profile.cognitive_style}"
            f"，知识基础={profile.knowledge_base}"
            f"，兴趣领域={profile.interest_areas}"
        )
    context = " | ".join(context_parts) if context_parts else ""

    rewritten = rewrite_query(message, context=context)

    print(f"[RewriteNode]  重写结果: {rewritten[:60] if rewritten else '(空，无需搜索)'}")

    return {
        "rewritten_query": rewritten,
    }
