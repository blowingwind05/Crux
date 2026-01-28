"""
Schema 模块

定义数据结构配置，支持动态 Schema 传入。
"""

from src.crux.schemas.base import BaseSchema
from src.crux.schemas.paper_schema import PaperSchema

__all__ = ["BaseSchema", "PaperSchema"]
