from app.database.base import get_session
from app.database.models import StudentProfileORM
from app.models.user import StudentProfile


class ProfileService:
    """学生画像的持久化服务"""

    def save_or_update(self, profile: StudentProfile) -> StudentProfile:
        """保存或更新画像（student_id 唯一）"""
        with get_session() as session:
            existing = (
                session.query(StudentProfileORM)
                .filter_by(student_id=profile.student_id)
                .first()
            )

            if existing:
                # 更新已有记录
                orm = StudentProfileORM.from_pydantic(profile)
                orm.id = existing.id
                session.merge(orm)
            else:
                # 新增
                session.add(StudentProfileORM.from_pydantic(profile))

            session.commit()
            return profile

    def get(self, student_id: str) -> StudentProfile | None:
        """根据 student_id 获取画像"""
        with get_session() as session:
            orm = (
                session.query(StudentProfileORM)
                .filter_by(student_id=student_id)
                .first()
            )
            return orm.to_pydantic() if orm else None


# 全局单例，方便各处调用
profile_service = ProfileService()
