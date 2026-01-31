"""
Backend Routers - 路由模块初始化
"""

from backend.routers.query import router as query_router
from backend.routers.config import router as config_router

__all__ = [
    "query_router",
    "config_router",
]
