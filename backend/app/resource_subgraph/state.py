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

    # 学习路径上下文（可选，用于绑定资源到具体阶段）
    path_id: Optional[int]            # 当前选中的学习路径 ID
    step_order: Optional[int]         # 当前聚焦的学习阶段序号
    step_knowledge_points: List[str]  # 当前阶段的所有知识点列表

    # 纯净主题（planner 从消息中提取，去掉指令词）
    cleaned_topic: str

    # 规划结果（planner 写入）
    resource_plan: List[str]         # 如 ["document", "exam", "ppt"]

    # 生成结果（各 generator 并行写入，reducer 累加）
    generated_resources: Annotated[List[Resource], lambda a, b: a + b]

    # 汇总回复（collector 写入）
    response: Optional[str]

    # ── 试卷反思重试 ──
    exam_retry_count: int             # 当前已重试次数（0=首次）
    exam_error_feedback: str          # 反思节点的错误反馈，用于下次生成
    exam_invalid_resource_id: Optional[str]  # 待过滤的无效试卷资源 ID

    # ── 代码案例反思重试 ──
    code_retry_count: int
    code_error_feedback: str
    code_invalid_resource_id: Optional[str]

    # ── 内容安全检查 ──
    unsafe_resource_ids: Annotated[List[str], lambda a, b: a + b]  # safety_filter 标记的不安全资源 ID 列表
