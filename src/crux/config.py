"""
Crux 框架配置模块
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import os
import yaml


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
    top_k: int = 2
    use_bm25: bool = True
    use_vector: bool = True
    use_metadata_filter: bool = True


@dataclass 
class SchemaConfig:
    """Schema 配置 - 从 YAML 加载"""
    name: str = "default"
    description: str = ""
    fields: List[Dict[str, Any]] = field(default_factory=list)
    example_queries: List[str] = field(default_factory=list)
    
    def get_field_descriptions(self) -> str:
        """生成字段描述文本"""
        if not self.fields:
            return ""
        
        lines = [f"## {self.name} 数据结构", "", self.description, "", "### 字段说明"]
        for f in self.fields:
            field_type = f.get("type", "string")
            desc = f.get("description", "")
            lines.append(f"- `{f['name']}` ({field_type}): {desc}")
        
        return "\n".join(lines)
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SchemaConfig":
        """从 YAML 文件加载配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return cls(
            name=data.get("name", "default"),
            description=data.get("description", ""),
            fields=data.get("fields", []),
            example_queries=data.get("example_queries", [])
        )


@dataclass
class CruxConfig:
    """Crux 框架主配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    
    # 数据源配置
    data_source_type: str = "json"  # json, csv, milvus, qdrant, es
    data_source_path: Optional[str] = None
    
    # Schema 配置 - 支持 YAML 文件路径
    schema_path: Optional[str] = None  # YAML schema 文件路径
    
    # 调试选项
    debug: bool = False
    mock_llm: bool = False  # 是否使用 mock LLM 响应
    
    # 缓存的 schema 配置
    _schema_config: Optional[SchemaConfig] = field(default=None, repr=False)
    
    def get_schema_config(self) -> SchemaConfig:
        """获取 Schema 配置"""
        if self._schema_config is None:
            if self.schema_path and os.path.exists(self.schema_path):
                self._schema_config = SchemaConfig.from_yaml(self.schema_path)
            else:
                # 返回空的默认配置
                self._schema_config = SchemaConfig()
        return self._schema_config
    
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
            schema_path=config_dict.get("schema_path"),
            debug=config_dict.get("debug", False),
            mock_llm=config_dict.get("mock_llm", True),
        )

