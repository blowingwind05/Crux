"""
Backend Services - 服务模块初始化
"""

from backend.services.pipeline import PipelineService, pipeline_service
from backend.services.model_service import ModelService, model_service

__all__ = [
    "PipelineService",
    "pipeline_service",
    "ModelService",
    "model_service",
]
