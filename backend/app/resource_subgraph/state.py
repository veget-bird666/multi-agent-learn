"""
子图状态定义：ResourceSubState
子图运行期间使用的轻量状态，只包含资源生成所需字段。
运行结束后合并回主图 LearningState。
"""
from typing import TypedDict, List, Optional, Annotated
from app.models.user import StudentProfile
from app.models.resources import Resource


class ResourceSubState(TypedDict):
    """资源生成子图专用状态"""

    # 输入（来自主图）
    knowledge_point: str
    profile: Optional[StudentProfile]
    message: str
    rewritten_query: Optional[str]

    # 纯净主题（planner 从消息中提取，去掉指令词）
    cleaned_topic: str

    # 规划结果（planner 写入）
    resource_plan: List[str]         # 如 ["document", "exam", "ppt"]

    # 生成结果（各 generator 并行写入，reducer 累加）
    generated_resources: Annotated[List[Resource], lambda a, b: a + b]

    # 汇总回复（collector 写入）
    response: Optional[str]
