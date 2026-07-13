"""
资源持久化服务：管理已生成的学习资源的读写
"""
from datetime import datetime
from typing import List, Optional

from app.database.base import get_session
from app.database.models import ResourceORM
from app.models.resources import Resource


class ResourceService:
    """学习资源的持久化服务"""

    def save(self, resource: Resource, student_id: str) -> Resource:
        """保存一条资源记录"""
        now = datetime.now().isoformat(timespec="seconds")
        orm = ResourceORM.from_resource(resource, student_id, created_at=now)
        with get_session() as session:
            session.add(orm)
            session.commit()
            return resource

    def save_batch(self, resources: List[Resource], student_id: str) -> List[Resource]:
        """批量保存资源"""
        now = datetime.now().isoformat(timespec="seconds")
        orms = [ResourceORM.from_resource(r, student_id, created_at=now) for r in resources]
        with get_session() as session:
            for orm in orms:
                session.add(orm)
            session.commit()
        return resources

    def list_by_student(self, student_id: str) -> List[Resource]:
        """查询某学生的全部资源，按创建时间降序"""
        with get_session() as session:
            orms = (
                session.query(ResourceORM)
                .filter_by(student_id=student_id)
                .order_by(ResourceORM.id.desc())
                .all()
            )
            return [orm.to_pydantic() for orm in orms]

    def list_with_orm_ids(self, student_id: str) -> List[dict]:
        """查询资源列表，每项包含 Resource dict + orm_id"""
        with get_session() as session:
            orms = (
                session.query(ResourceORM)
                .filter_by(student_id=student_id)
                .order_by(ResourceORM.id.desc())
                .all()
            )
            items = []
            for orm in orms:
                r = orm.to_pydantic()
                d = r.model_dump()
                d["orm_id"] = orm.id
                items.append(d)
            return items

    def get_by_orm_id(self, orm_id: int) -> Optional[dict]:
        """按 ORM 主键查询单条资源，返回 dict（含 orm_id）。"""
        with get_session() as session:
            orm = session.query(ResourceORM).filter_by(id=orm_id).first()
            if orm is None:
                return None
            r = orm.to_pydantic()
            d = r.model_dump()
            d["orm_id"] = orm.id
            return d

    def delete(self, resource_id: int) -> bool:
        """按 ORM 主键删除"""
        with get_session() as session:
            orm = session.query(ResourceORM).filter_by(id=resource_id).first()
            if orm is None:
                return False
            session.delete(orm)
            session.commit()
            return True


# 全局单例
resource_service = ResourceService()
