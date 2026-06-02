"""
智能体4：错误路径模拟 + 纠正
职责：故意展示典型错误 → 诊断原因 → 针对性生成纠正资源
"""
from app.graph.state import LearningState


def error_sim_agent(state: LearningState) -> dict:
    """模拟错误并生成纠正内容"""
    knowledge_point = state.get("knowledge_point", "")
    # TODO: 生成该知识点的典型错误
    # TODO: 诊断错误原因（概念问题/粗心/误解）
    # TODO: 生成针对性纠正资源
    return {
        "response": f"关于「{knowledge_point}」，很多同学会犯这样一个错误...",
    }
