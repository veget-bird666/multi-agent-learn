"""
智能体7：后悔机制 + 路径回滚
职责：记录教学决策，表现下滑时回溯并建议换方法重学
"""
from app.graph.state import LearningState


def reflection_agent(state: LearningState) -> dict:
    """评估学习效果，回溯教学决策"""
    decisions = state.get("teaching_decisions", [])
    # TODO: 评估学生近期表现
    # TODO: 如果表现下滑，回溯之前的教学决策
    # TODO: 建议是否回滚到某个知识点换方法重学
    return {
        "response": "本轮学习完成。继续加油！",
        "next_agent": None,
    }
