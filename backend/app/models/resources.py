from pydantic import BaseModel
from typing import Optional, List
from enum import Enum


class ResourceType(str, Enum):
    DOCUMENT = "document"          # 讲解文档
    MINDMAP = "mindmap"            # 思维导图
    EXERCISE = "exercise"          # 练习题
    VIDEO = "video"                # 视频/动画
    CODE_EXAMPLE = "code_example"  # 代码实操案例
    EXTRA_READING = "extra_reading"  # 拓展阅读
    PPT = "ppt"                    # PPT 课件
    EXAM = "exam"                  # 试卷
    IMAGE = "image"                # 图片


class Resource(BaseModel):
    """学习资源"""
    id: str
    type: ResourceType
    title: str
    content: str  # Markdown / JSON / 其他格式
    knowledge_point: str
    difficulty: str  # "easy" | "medium" | "hard"


class LearningPathStep(BaseModel):
    """学习路径中的单个步骤"""
    order: int
    stage_name: str                                    # 学习阶段名称，如"基础语法入门"
    knowledge_points: List[str]                        # 该阶段涵盖的核心知识点
    description: str                                   # 学习内容和要求
    duration_estimate: str = ""                        # 预估学习时长
    difficulty: str = "medium"                         # easy / medium / hard
    status: str = "pending"                            # pending / in_progress / completed


class LearningPathPlan(BaseModel):
    """学习路径规划（LLM 结构化输出用）"""
    steps: List[LearningPathStep]
    total_duration_estimate: str = ""                  # 总体预估时长
    prerequisites: List[str] = []                      # 前置知识要求
    learning_style_advice: str = ""                    # 针对该学生认知风格的建议


class LearningPath(BaseModel):
    """学习路径（持久化用）"""
    student_id: str
    steps: List[LearningPathStep]
    current_step: int = 0
    overall_progress: float = 0.0


class TeachingDecision(BaseModel):
    """教学决策记录（用于后悔机制）"""
    decision_id: str
    knowledge_point: str
    chosen_method: str        # 选用的教学方法
    alternative_method: str   # 可选的替代方法
    outcome_score: Optional[float] = None  # 后续评估得分
    student_id: str
    timestamp: str
