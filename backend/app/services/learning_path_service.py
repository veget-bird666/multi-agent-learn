"""
学习路径持久化服务：支持多条学习路径的 CRUD 和掌握度更新
"""
from datetime import datetime
from typing import List, Optional

from app.database.base import get_session
from app.database.models import LearningPathORM
from app.models.resources import LearningPathStep


class LearningPathService:
    """学习路径的持久化服务"""

    def list_by_student(self, student_id: str) -> List[dict]:
        """获取某个学生的所有学习路径（按创建时间倒序）"""
        with get_session() as session:
            orms = (
                session.query(LearningPathORM)
                .filter_by(student_id=student_id)
                .order_by(LearningPathORM.id.desc())
                .all()
            )
            return [self._orm_to_dict(o) for o in orms]

    def get_by_id(self, path_id: int) -> Optional[dict]:
        """根据路径 ID 获取单条路径"""
        with get_session() as session:
            orm = session.query(LearningPathORM).get(path_id)
            if not orm:
                return None
            return self._orm_to_dict(orm)

    def get_active(self, student_id: str) -> Optional[dict]:
        """获取某个学生当前选中的学习路径"""
        with get_session() as session:
            orm = (
                session.query(LearningPathORM)
                .filter_by(student_id=student_id, is_active=1)
                .order_by(LearningPathORM.id.desc())
                .first()
            )
            if not orm:
                # 兜底：取最新一条
                orm = (
                    session.query(LearningPathORM)
                    .filter_by(student_id=student_id)
                    .order_by(LearningPathORM.id.desc())
                    .first()
                )
            return self._orm_to_dict(orm) if orm else None

    def create(self, student_id: str, title: str, steps: List[LearningPathStep]) -> dict:
        """
        创建一条新的学习路径（追加，不影响已有路径）。
        返回新创建的路径 dict。
        """
        now = datetime.now().isoformat(timespec="seconds")
        step_dicts = [s.model_dump() for s in steps]

        with get_session() as session:
            orm = LearningPathORM(
                student_id=student_id,
                title=title,
                path_data="[]",
                current_step=0,
                overall_mastery=0,
                is_active=0,
                created_at=now,
                updated_at=now,
            )
            orm.set_steps(step_dicts)
            session.add(orm)
            session.commit()
            session.refresh(orm)  # 获取自增 id

        return self._orm_to_dict(orm)

    def set_active(self, path_id: int, student_id: str) -> Optional[dict]:
        """将某条路径设为当前学习的路径，同一学生其他路径取消激活"""
        with get_session() as session:
            # 取消该学生所有路径的激活
            session.query(LearningPathORM).filter_by(student_id=student_id).update(
                {"is_active": 0}
            )
            # 激活指定路径
            orm = session.query(LearningPathORM).get(path_id)
            if not orm:
                return None
            orm.is_active = 1
            orm.updated_at = datetime.now().isoformat(timespec="seconds")
            session.merge(orm)
            session.commit()

        return self.get_by_id(path_id)

    def update_step_mastery(
        self, path_id: int, step_order: int, mastery: float
    ) -> Optional[dict]:
        """
        更新某个阶段的掌握度，并重新计算总体掌握度。
        掌握度是"正确增加、错误不变"的单向增长模式。
        """
        now = datetime.now().isoformat(timespec="seconds")

        with get_session() as session:
            orm = session.query(LearningPathORM).get(path_id)
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

            return self.get_by_id(path_id)

    def batch_update_mastery(
        self, path_id: int, updates: List[dict]
    ) -> Optional[dict]:
        """
        批量更新多个阶段的掌握度。
        updates: [{"step_order": 1, "mastery": 80.0}, ...]
        """
        for u in updates:
            self.update_step_mastery(path_id, u["step_order"], u["mastery"])
        return self.get_by_id(path_id)

    def update_kp_mastery(
        self, path_id: int, step_order: int, kp_name: str, increment: float
    ) -> Optional[dict]:
        """
        更新某个知识点的熟练度（增量累加）。
        - 知识点熟练度上限 120%
        - 阶段掌握度 = 该阶段下所有知识点熟练度的均值
        - 路径总体掌握度 = 所有阶段掌握度的均值

        Args:
            path_id: 学习路径 ID
            step_order: 阶段序号
            kp_name: 知识点名称
            increment: 本次增加的熟练度（答对加分，答错不加）

        Returns:
            更新后的路径 dict，或 None（路径不存在时）
        """
        now = datetime.now().isoformat(timespec="seconds")

        with get_session() as session:
            orm = session.query(LearningPathORM).get(path_id)
            if not orm:
                return None

            steps = orm.get_steps()
            step_found = False
            for step in steps:
                if step.get("order") == step_order:
                    step_found = True
                    # 初始化/获取知识点熟练度字典
                    kp_mastery: dict = step.get("knowledge_point_mastery") or {}

                    # 如果该知识点在 step.knowledge_points 中，才允许更新
                    allowed_kps = step.get("knowledge_points", [])
                    if allowed_kps and kp_name not in allowed_kps:
                        print(f"[KPMastery]  {kp_name} 不在 {allowed_kps} 中，跳过")
                        break

                    current = kp_mastery.get(kp_name, 0.0)
                    new_val = current + increment
                    new_val = min(new_val, 120.0)  # 上限 120%

                    if new_val > current:
                        kp_mastery[kp_name] = round(new_val, 1)
                        step["knowledge_point_mastery"] = kp_mastery

                        # 重新计算阶段掌握度 = 各知识点熟练度均值
                        if kp_mastery:
                            step["mastery"] = round(
                                sum(kp_mastery.values()) / len(kp_mastery), 1
                            )

                    print(
                        f"[KPMastery]  step{step_order}/{kp_name}: "
                        f"{current} → {kp_mastery.get(kp_name, current)} "
                        f"(上限120%，增{increment})"
                    )
                    break

            if not step_found:
                print(f"[KPMastery]  未找到 step_order={step_order}，跳过")
                return self.get_by_id(path_id)

            # 重新计算总体掌握度 = 有 KP 数据的阶段掌握度均值
            steps_with_kp = [s for s in steps if s.get("knowledge_point_mastery")]
            if steps_with_kp:
                avg = sum(s.get("mastery", 0.0) for s in steps_with_kp) / len(steps_with_kp)
                orm.overall_mastery = round(avg)

            orm.set_steps(steps)
            orm.updated_at = now
            session.merge(orm)
            session.commit()

            return self.get_by_id(path_id)

    def delete(self, path_id: int) -> bool:
        """删除一条学习路径"""
        with get_session() as session:
            orm = session.query(LearningPathORM).get(path_id)
            if not orm:
                return False
            session.delete(orm)
            session.commit()
            return True

    # ── 内部方法 ──────────────────────────────────

    @staticmethod
    def _orm_to_dict(orm: LearningPathORM) -> dict:
        """ORM → dict"""
        return {
            "id": orm.id,
            "student_id": orm.student_id,
            "title": orm.title,
            "steps": orm.get_steps(),
            "current_step": orm.current_step,
            "overall_mastery": orm.overall_mastery,
            "is_active": bool(orm.is_active),
            "created_at": orm.created_at,
            "updated_at": orm.updated_at,
        }


# 全局单例
learning_path_service = LearningPathService()
