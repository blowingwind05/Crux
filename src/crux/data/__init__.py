"""
数据模块

提供多种数据源的加载和检索能力。
"""

from typing import Optional
from src.crux.config import get_config, CruxConfig


def get_data_loader(config: Optional[CruxConfig] = None):
    """
    根据配置获取数据加载器
    
    Args:
        config: 框架配置
        
    Returns:
        数据加载器实例
    """
    config = config or get_config()
    
    if config.data_source_type == "json":
        from src.crux.data.loaders.json_loader import JsonDataLoader
        return JsonDataLoader(config.data_source_path, config)
    
    elif config.data_source_type == "csv":
        from src.crux.data.loaders.csv_loader import CsvDataLoader
        return CsvDataLoader(config.data_source_path, config)
    
    elif config.data_source_type in ("milvus", "qdrant", "es"):
        from src.crux.data.loaders.vector_db import VectorDBLoader
        return VectorDBLoader(config)
    elif config.data_source_type == "hybrid":
        print(f"[DataModule] 使用混合检索数据加载器, 路径: {config.data_source_path}")
        from src.crux.data.loaders.hybrid_db import HybridDataLoader
        return HybridDataLoader(config)
    else:
        raise ValueError(f"不支持的数据源类型: {config.data_source_type}")


__all__ = ["get_data_loader"]
