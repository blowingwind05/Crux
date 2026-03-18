"""
Crux AgenticRAG Backend API

基于 FastAPI 的 Crux AgenticRAG 框架后端服务，
支持流式返回中间处理结果。
"""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from datetime import datetime
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from backend.core import get_settings
from backend.routers import query_router, config_router, model_inference_router
from backend.services import pipeline_service, model_service

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup
    logger.info(f"🚀 Starting {settings.app_name} v{settings.app_version}")

    # 加载模型服务配置
    try:
        from src.crux.config import load_config
        config = load_config()
        model_cfg = {}
        # 从 config.yaml 的 model_service 段读取配置
        config_path = settings.config_path
        if config_path:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                raw = yaml.safe_load(f) or {}
            model_cfg = raw.get('model_service', {})
        else:
            # 尝试默认 config.yaml
            import yaml
            from pathlib import Path
            default_cfg = Path('config_arxiv_full.yaml')
            if default_cfg.exists():
                with open(default_cfg, 'r', encoding='utf-8') as f:
                    raw = yaml.safe_load(f) or {}
                model_cfg = raw.get('model_service', {})

        if model_cfg:
            model_service.configure(
                embedding_model=model_cfg.get('embedding_model', '/workspace/bge-m3'),
                reranker_model=model_cfg.get('reranker_model', '/workspace/bge-reranker-v2-m3'),
                device=model_cfg.get('device', 'cuda'),
                batch_size=model_cfg.get('batch_size', 64),
            )
        else:
            logger.info("No model_service config found, using defaults.")
            model_service.configure()
        
        # 预加载模型
        logger.info("Loading models at startup...")
        model_service.load_models()
        logger.info("Models loaded successfully.")
    except Exception as e:
        logger.warning(f"Model service configuration skipped: {e}")

    yield
    # Shutdown
    if hasattr(pipeline_service, "clear_cache"):
        pipeline_service.clear_cache()
    model_service.unload()
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

app.include_router(model_inference_router)
logger.info("Model Inference路由注册完成")


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
        reload=False,
        # log_level="info",
    )
