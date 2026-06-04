"""
AI 个性化学习多智能体系统 - 后端入口
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.config import settings
from app.database.base import engine
from app.database.models import Base


@asynccontextmanager
async def lifespan(application: FastAPI):
    """应用启动/关闭生命周期"""
    # 启动时：自动建表
    Base.metadata.create_all(engine)
    yield
    # 关闭时：释放资源（如有需要）


app = FastAPI(
    lifespan=lifespan,
    title=settings.APP_NAME,
    version="0.1.0",
    description="基于大模型的个性化资源生成与学习多智能体系统（科大讯飞 A3 赛题）",
)

# CORS 配置 - 允许 Vue 前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务 - 提供生成的 PPT / 图片等资源
GENERATED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated"))
os.makedirs(f"{GENERATED_DIR}/ppt", exist_ok=True)
app.mount("/static", StaticFiles(directory=GENERATED_DIR), name="generated")

# 注册路由
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "AI 个性化学习多智能体系统",
        "version": "0.1.0",
        "status": "running",
    }
