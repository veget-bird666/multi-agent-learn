import json
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.orm import declarative_base

from app.database.base import engine

Base = declarative_base()


class StudentProfileORM(Base):
    """学生画像 ORM 模型 — 对应 student_profiles 表"""

    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(64), unique=True, index=True, nullable=False)

    # 画像维度（至少 6 个）
    name = Column(String(128), default="")
    major = Column(String(128), default="")                      # 专业
    knowledge_base = Column(Text, default="")                     # 知识基础
    cognitive_style = Column(String(64), default="")              # 认知风格
    learning_pace = Column(String(64), default="")                # 学习节奏
    interest_areas = Column(Text, default="[]")                   # 兴趣领域（JSON 列表）
    common_mistakes = Column(Text, default="[]")                  # 易错点（JSON 列表）
    goal = Column(Text, default="")                               # 学习目标

    def to_pydantic(self):
        """ORM → Pydantic，供 API 和 Agent 使用"""
        from app.models.user import StudentProfile

        return StudentProfile(
            student_id=self.student_id,
            name=self.name or None,
            major=self.major or None,
            knowledge_base=self.knowledge_base or None,
            cognitive_style=self.cognitive_style or None,
            learning_pace=self.learning_pace or None,
            interest_areas=json.loads(self.interest_areas) if self.interest_areas else None,
            common_mistakes=json.loads(self.common_mistakes) if self.common_mistakes else None,
            goal=self.goal or None,
        )

    @classmethod
    def from_pydantic(cls, profile: "StudentProfile") -> "StudentProfileORM":
        """Pydantic → ORM"""
        return cls(
            student_id=profile.student_id,
            name=profile.name or "",
            major=profile.major or "",
            knowledge_base=profile.knowledge_base or "",
            cognitive_style=profile.cognitive_style or "",
            learning_pace=profile.learning_pace or "",
            interest_areas=json.dumps(profile.interest_areas or [], ensure_ascii=False),
            common_mistakes=json.dumps(profile.common_mistakes or [], ensure_ascii=False),
            goal=profile.goal or "",
        )


class ResourceORM(Base):
    """学习资源 ORM 模型 — 对应 resources 表"""

    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    resource_id = Column(String(128), index=True, nullable=False)   # 生成时的唯一 ID
    student_id = Column(String(64), index=True, nullable=False)     # 所属学生
    type = Column(String(32), nullable=False)                       # document / exam / ppt / image / video
    title = Column(String(256), default="")
    content = Column(Text, default="")                               # Markdown / JSON / URL
    knowledge_point = Column(String(256), default="")
    difficulty = Column(String(16), default="medium")
    created_at = Column(String(32), default="")                      # ISO 时间戳

    def to_pydantic(self):
        from app.models.resources import Resource, ResourceType
        try:
            res_type = ResourceType(self.type)
        except ValueError:
            res_type = ResourceType.DOCUMENT
        return Resource(
            id=self.resource_id,
            type=res_type,
            title=self.title or "",
            content=self.content or "",
            knowledge_point=self.knowledge_point or "",
            difficulty=self.difficulty or "medium",
        )

    @classmethod
    def from_resource(cls, resource: "Resource", student_id: str, created_at: str = "") -> "ResourceORM":
        return cls(
            resource_id=resource.id,
            student_id=student_id,
            type=resource.type.value if hasattr(resource.type, "value") else str(resource.type),
            title=resource.title,
            content=resource.content,
            knowledge_point=resource.knowledge_point,
            difficulty=resource.difficulty,
            created_at=created_at,
        )


# 导入模块时自动建表（无论从 main.py 启动还是测试都会执行）
Base.metadata.create_all(engine)
