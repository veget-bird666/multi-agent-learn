from pydantic import BaseModel, field_validator
from typing import Optional, List
import json


class StudentProfile(BaseModel):
    """学生画像 - 竞赛要求至少6个维度"""
    student_id: str
    name: Optional[str] = None
    major: Optional[str] = None                     # 专业
    knowledge_base: Optional[str] = None             # 知识基础
    cognitive_style: Optional[str] = None             # 认知风格（举例型/公式型/实践型）
    learning_pace: Optional[str] = None               # 学习节奏
    interest_areas: Optional[List[str]] = None        # 兴趣领域
    common_mistakes: Optional[List[str]] = None       # 易错点偏好
    goal: Optional[str] = None                        # 学习目标

    @field_validator("interest_areas", "common_mistakes", mode="before")
    @classmethod
    def parse_json_list(cls, v):
        """兼容 LLM 返回 JSON 字符串或纯字符串的情况"""
        if isinstance(v, str):
            if not v.strip():
                return None
            # 尝试解析 JSON 数组
            if v.strip().startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # 纯字符串 → 包装为单元素列表
            return [v.strip().strip('"').strip("'")]
        return v


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str


class ChatRequest(BaseModel):
    student_id: str
    message: str
    session_id: Optional[str] = None
    focused_step_order: Optional[int] = None   # 用户聚焦的学习阶段
    current_path_id: Optional[int] = None      # 前端当前选中的路径 ID
    include_path_context: bool = True           # 是否将学习路径上下文发给模型
