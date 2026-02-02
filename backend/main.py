"""
Crux AgenticRAG Backend API

基于 FastAPI 的 Crux AgenticRAG 框架后端服务，
支持流式返回中间处理结果。
"""

from contextlib import asynccontextmanager
from pathlib import Path
import sys
sys.path.append('/Users/mac/Projects/Crux/')
sys.path.append('G:/Projects/Crux')
from datetime import datetime
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from backend.core import get_settings
from backend.routers import query_router, config_router
from backend.services import pipeline_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")
    yield
    # Shutdown
    if hasattr(pipeline_service, "clear_cache"):
        pipeline_service.clear_cache()
    logger.info(f"🛑 Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    description="基于意图深度感知的 AgenticRAG 框架 API 服务",
    version=settings.app_version,
    lifespan=lifespan,
)

logger.info("FastAPI应用初始化完成")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS中间件配置完成")

# Include routers
app.include_router(query_router)
logger.info("Query路由注册完成")

app.include_router(config_router)
logger.info("Config路由注册完成")


@app.get("/")
async def root():
    return {
        "message": settings.app_name,
        "version": settings.app_version,
    }


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.app_version
    }


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
