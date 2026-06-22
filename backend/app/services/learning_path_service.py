"""
学习路径持久化服务：管理学习路径的读写和掌握度更新
"""
from datetime import datetime
from typing import List, Optional

from app.database.base import get_session
from app.database.models import LearningPathORM
from app.models.resources import LearningPathStep


class LearningPathService:
    """学习路径的持久化服务"""

    def get(self, student_id: str) -> Optional[dict]:
        """获取某个学生的最近一条学习路径"""
        with get_session() as session:
            orm = (
                session.query(LearningPathORM)
                .filter_by(student_id=student_id)
                .order_by(LearningPathORM.id.desc())
                .first()
            )
            if not orm:
                return None
            return {
                "id": orm.id,
                "student_id": orm.student_id,
                "title": orm.title,
                "steps": orm.get_steps(),
                "current_step": orm.current_step,
                "overall_mastery": orm.overall_mastery,
                "created_at": orm.created_at,
                "updated_at": orm.updated_at,
            }

    def save(self, student_id: str, title: str, steps: List[LearningPathStep]) -> dict:
        """
        保存/覆盖学习路径。每个学生只保留一条活跃路径。
        返回保存后的 dict。
        """
        now = datetime.now().isoformat(timespec="seconds")
        step_dicts = [s.model_dump() for s in steps]

        with get_session() as session:
            # 查找该学生现有的最新路径
            existing = (
                session.query(LearningPathORM)
                .filter_by(student_id=student_id)
                .order_by(LearningPathORM.id.desc())
                .first()
            )

            if existing:
                existing.title = title
                existing.set_steps(step_dicts)
                existing.current_step = 0
                existing.overall_mastery = 0
                existing.updated_at = now
                session.merge(existing)
                session.commit()
                orm = existing
            else:
                orm = LearningPathORM(
                    student_id=student_id,
                    title=title,
                    path_data="[]",
                    current_step=0,
                    overall_mastery=0,
                    created_at=now,
                    updated_at=now,
                )
                orm.set_steps(step_dicts)
                session.add(orm)
                session.commit()

        return self.get(student_id)

    def update_step_mastery(
        self, student_id: str, step_order: int, mastery: float
    ) -> Optional[dict]:
        """
        更新某个阶段的掌握度，并重新计算总体掌握度。
        掌握度是"正确增加、错误不变"的单向增长模式。
        """
        now = datetime.now().isoformat(timespec="seconds")

        with get_session() as session:
            orm = (
                session.query(LearningPathORM)
                .filter_by(student_id=student_id)
                .order_by(LearningPathORM.id.desc())
                .first()
            )
            if not orm:
                return None

            steps = orm.get_steps()
            updated = False
            for step in steps:
                if step.get("order") == step_order:
                    current = step.get("mastery", 0.0)
                    # 只涨不跌：新值 > 当前值才更新
                    if mastery > current:
                        step["mastery"] = min(round(mastery, 1), 100.0)
                        updated = True
                    break

            if updated:
                orm.set_steps(steps)
                # 重新计算总体掌握度 = 各阶段掌握度均值
                if steps:
                    avg_mastery = sum(s.get("mastery", 0.0) for s in steps) / len(steps)
                    orm.overall_mastery = round(avg_mastery)
                orm.updated_at = now
                session.merge(orm)
                session.commit()

            return self.get(student_id)

    def batch_update_mastery(
        self, student_id: str, updates: List[dict]
    ) -> Optional[dict]:
        """
        批量更新多个阶段的掌握度。
        updates: [{"step_order": 1, "mastery": 80.0}, ...]
        """
        for u in updates:
            self.update_step_mastery(student_id, u["step_order"], u["mastery"])
        return self.get(student_id)


# 全局单例
learning_path_service = LearningPathService()
