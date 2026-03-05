"""FastAPI主应用"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
import sys

from app.api import chat, knowledge, monitor
from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.redis import redis_client


# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level=settings.log_level,
)
logger.add(
    settings.log_file,
    rotation="10 MB",
    retention="7 days",
    level=settings.log_level,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("Starting Kimi Customer Service API...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"LLM Provider: {settings.llm_provider}")

    # 初始化数据库
    try:
        await init_db()
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    # 初始化Redis
    try:
        await redis_client.connect()
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}")

    yield

    # 关闭
    logger.info("Shutting down...")
    await close_db()
    await redis_client.disconnect()


# 创建FastAPI应用
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI Customer Service System with RAG and Agent Orchestration",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "llm_provider": settings.llm_provider,
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Kimi Customer Service API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
        "api_prefix": settings.api_prefix,
    }


# 注册路由
app.include_router(chat.router, prefix=settings.api_prefix)
app.include_router(knowledge.router, prefix=settings.api_prefix)
app.include_router(monitor.router, prefix=settings.api_prefix)

# 提供静态文件（监控Dashboard）
from fastapi.staticfiles import StaticFiles
import os

app.mount("/dashboard", StaticFiles(directory=os.path.dirname(os.path.abspath(__file__)) + "/../", html=True), name="dashboard")


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
