"""定义 LangGraph 状态：学习系统的全局状态"""
from typing import TypedDict, Optional, List, Annotated
from app.models.user import StudentProfile
from app.models.resources import Resource, TeachingDecision
from langchain_core.messages import BaseMessage

class LearningState(TypedDict):
    """多智能体学习系统的全局状态"""

    # 基础信息
    history: List[BaseMessage]  # 对话历史
    operation: int  # 当前操作步骤（如第几轮对话）

    # 学生信息
    student_id: str
    profile: Optional[StudentProfile]

    # 当前交互
    message: str
    session_id: Optional[str]

    # 智能体路由
    current_agent: Optional[str]  # 当前由哪个智能体处理
    next_agent: Optional[str]     # 下一个要调度的智能体
    next_reasoning: Optional[str]   # 下一个智能体的 reasoning（如果需要）
    profile_update_hint: Optional[str]  # Supervisor 传给 profile_agent 的更新提示
    rewritten_query: Optional[str]  # rewrite_node 重写后的搜索查询

    # Plan-and-Execute：Supervisor 规划后按计划推进
    execution_plan: List[str]  # ["rewrite_node", "path_agent"] 等，空列表表示无计划
    current_plan_step: int     # -1 表示无计划，0+ 表示当前执行到的步骤索引

    # 工具调用
    tool_result: Optional[str]       # 工具执行结果
    image_base64: Optional[str]      # 前端上传的图片（base64，不含前缀）

    # 学习过程
    knowledge_point: Optional[str]
    learning_path: Optional[List[dict]]
    current_path_id: Optional[int]     # 当前选中的学习路径 ID（存数据库的 id）
    current_step: int
    focused_step_order: Optional[int]  # 用户聚焦的学习阶段（可空）

    # 生成资源
    generated_resources: Annotated[List[Resource], lambda a, b: a + b]

    # 教学决策记录（用于后悔机制）
    teaching_decisions: Annotated[List[TeachingDecision], lambda a, b: a + b]

    # 好奇心 / 卡壳检测
    interaction_pattern: Optional[dict]  # 停留时间、追问次数等

    # 用户开关：控制是否允许生成学习路径和资源（None=启用）
    enable_path_planning: Optional[bool]
    enable_resource_generation: Optional[bool]

    # 学习评估
    evaluation: Optional[dict]  # reflection_agent 生成的评估报告

    # 输出
    response: Optional[str]
