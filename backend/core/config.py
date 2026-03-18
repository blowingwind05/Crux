"""
Backend Core Configuration Module

使用 pydantic-settings 管理应用配置，支持从 YAML 文件加载
"""

from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field
import os


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
    
    # 配置文件路径（默认使用 .config.yaml）
    config_path: Optional[str] = Field(default="/workspace/crux/Crux/config_arxiv_full.yaml")
    
    # 数据源默认配置（如果未指定 config_path 则使用）
    default_data_source_type: str = "json"
    default_data_source_path: str = "data/ir_papers.json"
    default_schema_path: str = "data/paper_schema.yaml"
    
    # LLM 配置
    mock_llm: bool = False
    
    class Config:
        env_prefix = "CRUX_"
        env_file = ".env"
    
    def get_project_root(self) -> str:
        """获取项目根目录"""
        # 尝试从环境变量获取
        root = os.getenv("CRUX_PROJECT_ROOT")
        if root:
            return root
        
        # 否则使用当前工作目录
        return os.getcwd()
    
    def get_absolute_path(self, relative_path: str) -> str:
        """将相对路径转换为绝对路径"""
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.get_project_root(), relative_path)


@lru_cache
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
