"""
Backend Models - 请求模型定义
"""

from typing import Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str = Field(..., description="用户查询文本", min_length=1)
    data_source_type: str = Field(default="json", description="数据源类型")
    data_source_path: Optional[str] = Field(default=None, description="数据源路径")
    schema_path: Optional[str] = Field(default=None, description="YAML schema 配置文件路径")
    mock_llm: bool = Field(default=False, description="是否使用 mock LLM")
    debug: bool = Field(default=False, description="调试模式")


class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    data_source_type: Optional[str] = None
    data_source_path: Optional[str] = None
    schema_path: Optional[str] = None
    mock_llm: Optional[bool] = None
    debug: Optional[bool] = None
