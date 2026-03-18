"""
Backend Routers - 路由模块初始化
"""

from backend.routers.query import router as query_router
from backend.routers.config import router as config_router
from backend.routers.model_inference import router as model_inference_router

__all__ = [
    "query_router",
    "config_router",
    "model_inference_router",
]
