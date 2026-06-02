"""
智能体6：好奇心驱动探索
职责：监测学生停留与追问，区分好奇 vs 卡壳，触发不同响应
"""
from app.graph.state import LearningState


def curiosity_agent(state: LearningState) -> dict:
    """分析交互模式，判断学生状态"""
    # TODO: 分析停留时间、追问次数、提问类型等
    # TODO: 区分"好奇"（感兴趣）和"卡壳"（不理解）
    return {
        "interaction_pattern": {
            "is_curious": False,
            "is_stuck": False,
            "details": {},
        },
    }
