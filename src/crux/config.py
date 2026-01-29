"""
Crux 框架配置模块
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import os


@dataclass
class LLMConfig:
    """LLM 配置"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "Qwen/Qwen3-32B"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY","EMPTY")
        if self.base_url is None:
            self.base_url = os.getenv("OPENAI_BASE_URL","https://aicloud.oneainexus.cn:30013/inference/aicloud-yanqiang/qwen3-32b-server/v1")


@dataclass
class SearchConfig:
    """检索配置"""
    max_iterations: int = 3
    top_k: int = 50
    use_bm25: bool = True
    use_vector: bool = True
    use_metadata_filter: bool = True


@dataclass
class CruxConfig:
    """Crux 框架主配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    
    # 数据源配置
    data_source_type: str = "json"  # json, csv, milvus, qdrant, es
    data_source_path: Optional[str] = None
    
    # Schema 配置
    schema_type: str = "paper"  # paper, news, log, custom
    
    # 调试选项
    debug: bool = False
    mock_llm: bool = False  # 是否使用 mock LLM 响应
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "CruxConfig":
        """从字典创建配置"""
        llm_config = LLMConfig(**config_dict.get("llm", {}))
        search_config = SearchConfig(**config_dict.get("search", {}))
        return cls(
            llm=llm_config,
            search=search_config,
            data_source_type=config_dict.get("data_source_type", "json"),
            data_source_path=config_dict.get("data_source_path"),
            schema_type=config_dict.get("schema_type", "paper"),
            debug=config_dict.get("debug", False),
            mock_llm=config_dict.get("mock_llm", False),
        )
