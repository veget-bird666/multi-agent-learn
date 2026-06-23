"""
虚拟学伴 — 结构化输入/输出定义
"""
from pydantic import BaseModel, Field
from typing import Optional


class BuddyQuestion(BaseModel):
    """学伴提问的结构化输出"""
    question: str = Field(description="学伴提出的问题，以'小问'口吻，谦虚好奇")
    knowledge_point: str = Field(description="关联的知识点名称")
    difficulty: str = Field(description="难度 easy | medium | hard")


class BuddyEvaluation(BaseModel):
    """学伴评估的结构化输出（双层输出 + 跟进追问）"""
    response: str = Field(description="学伴的角色扮演回复，语气含糊似懂非懂，不要直接说对错")
    learning_note: str = Field(description="学习笔记，Markdown格式，包含知识点概述、正确理解、常见误区、关键要点")
    is_correct: bool = Field(description="学生回答是否正确，核心概念对了就算对，宽松标准")
    difficulty: str = Field(description="本题难度 easy | medium | hard")
    follow_up_question: Optional[str] = Field(default=None, description="如果还需要继续追问，这里填写跟进问题。无需追问时留空")
    follow_up_kp: Optional[str] = Field(default=None, description="跟进问题对应的知识点名称，默认和当前知识点相同")


class QuestionRequest(BaseModel):
    """生成问题的请求"""
    student_id: str
    path_id: int
    focused_step_order: Optional[int] = Field(default=None, description="聚焦的学习阶段序号，为空时从全部阶段中选择")


class EvaluateRequest(BaseModel):
    """评估答案的请求"""
    student_id: str
    path_id: int
    step_order: Optional[int] = None
    knowledge_point: str = ""
    question: str
    answer: str
    focused_step_order: Optional[int] = None
