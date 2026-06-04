"""
智能体5：虚拟学习伙伴
职责：扮演一个水平略低的 AI 同学，让学生通过"教它"来巩固理解
"""
from app.graph.state import LearningState


def buddy_agent(state: LearningState) -> dict:
    """生成虚拟伙伴的提问或回应"""
    knowledge_point = state.get("knowledge_point", "")
    # TODO: 根据当前知识点生成"笨同学"的提问
    # TODO: 分析学生"教"的过程，判断是否真正掌握
    return {
        "response": f"关于「{knowledge_point}」，我这里不太懂，你能教我吗？",
    }
