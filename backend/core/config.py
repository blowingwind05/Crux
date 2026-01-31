"""
Backend Core Configuration Module

使用 pydantic-settings 管理应用配置
"""

from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用信息
    app_name: str = "Crux AgenticRAG API"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # CORS 配置
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    
    # 数据源默认配置
    default_data_source_type: str = "json"
    default_data_source_path: str = "/Users/mac/Projects/Crux/data/ir_papers.json"
    default_schema_path: str = "/Users/mac/Projects/Crux/data/paper_schema.yaml"
    
    # LLM 配置
    mock_llm: bool = False
    
    class Config:
        env_prefix = "CRUX_"
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
