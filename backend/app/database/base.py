from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# 创建引擎（连接池）
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
)

# session 工厂
SessionLocal = sessionmaker(bind=engine, class_=Session)


def get_session() -> Session:
    """获取一个新 session（用完要 close）"""
    return SessionLocal()
