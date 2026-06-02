"""
智能体2：多智能体协同资源生成
职责：生成5+种个性化学习资源（文档、思维导图、习题、视频/动画、代码案例、拓展阅读）
"""
from app.graph.state import LearningState


def resource_agent(state: LearningState) -> dict:
    """根据学生画像和知识点生成多模态学习资源"""
    knowledge_point = state.get("knowledge_point", "")
    profile = state.get("profile", {})
    # TODO: 调用 LLM 根据画像和知识点生成个性化资源
    # TODO: 生成多种类型资源
    return {
        "generated_resources": [],
        "response": f"正在为知识点「{knowledge_point}」生成个性化学习资源...",
    }
