from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "AI个性化学习多智能体系统"
    DEBUG: bool = True

    # 讯飞星火 API（原生 SDK）
    SPARK_API_KEY: Optional[str] = None
    SPARK_API_SECRET: Optional[str] = None
    SPARK_APP_ID: Optional[str] = None

    # 讯飞星火模型广场 MaaS（OpenAI 兼容）
    SPARK_MAAS_BASE_URL: str = "https://maas-api.cn-huabei-1.xf-yun.com/v2"
    SPARK_MAAS_API_KEY: Optional[str] = None

    # 关系型数据库（SQLite 开发，可无缝切换 MySQL）
    DATABASE_URL: str = "sqlite:///./learning.db"

    # 向量数据库
    CHROMA_PERSIST_DIR: str = "chroma_data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
