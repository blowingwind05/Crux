"""
Crux 框架配置模块

支持从 YAML 文件加载配置，环境变量覆盖，以及默认值回退。
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import os
import re
import yaml
from pathlib import Path


def _resolve_env_vars(value: Any) -> Any:
    """
    递归解析配置值中的环境变量引用
    
    支持格式:
    - ${VAR_NAME} - 如果环境变量不存在则返回空字符串
    - ${VAR_NAME:default} - 如果环境变量不存在则使用默认值
    """
    if isinstance(value, str):
        # 匹配 ${VAR_NAME} 或 ${VAR_NAME:default}
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        
        def replacer(match):
            var_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.getenv(var_name, default_value)
        
        return re.sub(pattern, replacer, value)
    
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    
    return value


@dataclass
class LLMConfig:
    """LLM 配置"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "Qwen/Qwen3-32B"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    def __post_init__(self):
        if self.api_key is None or self.api_key == "":
            self.api_key = os.getenv("OPENAI_API_KEY", "EMPTY")
        if self.base_url is None or self.base_url == "":
            self.base_url = os.getenv(
                "OPENAI_BASE_URL",
                "https://aicloud.oneainexus.cn:30013/inference/aicloud-yanqiang/qwen3-32b-server/v1"
            )


@dataclass
class JudgeConfig:
    """研判配置"""
    use_parallel: bool = True
    max_retry: int = 5
    max_workers: int = 4
    batch_size: int = 4


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
    def from_dict(cls, data: Dict[str, Any]) -> "SchemaConfig":
        """从字典创建配置"""
        return cls(
            name=data.get("name", "default"),
            description=data.get("description", ""),
            fields=data.get("fields", []),
            example_queries=data.get("example_queries", [])
        )
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SchemaConfig":
        """从 YAML 文件加载配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


@dataclass
class CruxConfig:
    """Crux 框架主配置"""
    llm: LLMConfig = field(default_factory=LLMConfig)
    judge: JudgeConfig = field(default_factory=JudgeConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    
    # 数据源配置
    data_source_type: str = "json"  # json, csv, milvus, qdrant, es
    data_source_path: Optional[str] = None
    
    # Schema 配置 - 支持 YAML 文件路径（向后兼容）
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
    
    def set_schema_config(self, schema_config: SchemaConfig):
        """设置 Schema 配置"""
        self._schema_config = schema_config
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "CruxConfig":
        """从字典创建配置"""
        # 处理 LLM 配置
        llm_data = config_dict.get("llm", {})
        llm_config = LLMConfig(
            api_key=llm_data.get("api_key"),
            base_url=llm_data.get("base_url"),
            model=llm_data.get("model", "Qwen/Qwen3-32B"),
            temperature=llm_data.get("temperature", 0.7),
            max_tokens=llm_data.get("max_tokens", 4096),
        )
        
        # 处理研判配置
        judge_data = config_dict.get("judge", {})
        judge_config = JudgeConfig(
            use_parallel=judge_data.get("use_parallel", True),
            max_retry=judge_data.get("max_retry", 5),
            max_workers=judge_data.get("max_workers", 4),
            batch_size=judge_data.get("batch_size", 4),
        )
        
        # 处理检索配置
        search_data = config_dict.get("search", {})
        search_config = SearchConfig(
            max_iterations=search_data.get("max_iterations", 3),
            top_k=search_data.get("top_k", 2),
            use_bm25=search_data.get("use_bm25", True),
            use_vector=search_data.get("use_vector", True),
            use_metadata_filter=search_data.get("use_metadata_filter", True),
        )
        
        # 处理数据源配置
        data_source = config_dict.get("data_source", {})
        data_source_type = data_source.get("type", config_dict.get("data_source_type", "json"))
        data_source_path = data_source.get("path", config_dict.get("data_source_path"))
        
        # 创建 CruxConfig 实例
        crux_config = cls(
            llm=llm_config,
            judge=judge_config,
            search=search_config,
            data_source_type=data_source_type,
            data_source_path=data_source_path,
            schema_path=config_dict.get("schema_path"),
            debug=config_dict.get("debug", False),
            mock_llm=config_dict.get("mock_llm", False),
        )
        
        # 处理内嵌的 schema 配置
        schema_data = config_dict.get("schema", {})
        if schema_data:
            crux_config._schema_config = SchemaConfig.from_dict(schema_data)
        
        return crux_config
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "CruxConfig":
        """
        从 YAML 文件加载完整配置
        
        Args:
            yaml_path: YAML 配置文件路径
            
        Returns:
            CruxConfig 实例
        """
        with open(yaml_path, 'r', encoding='utf-8') as f:
            raw_data = yaml.safe_load(f)
        
        # 解析环境变量
        config_dict = _resolve_env_vars(raw_data)
        
        return cls.from_dict(config_dict)


def find_config_file(config_path: Optional[str] = None) -> Optional[str]:
    """
    查找配置文件
    
    搜索顺序:
    1. 指定的路径
    2. CRUX_CONFIG_PATH 环境变量
    3. 当前目录的 config.yaml
    4. 项目根目录的 config.yaml
    
    Returns:
        配置文件路径，如果未找到返回 None
    """
    # 1. 检查指定路径
    if config_path and os.path.exists(config_path):
        return config_path
    
    # 2. 检查环境变量
    env_path = os.getenv("CRUX_CONFIG_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # 3. 检查当前目录
    cwd_config = Path.cwd() / "config.yaml"
    if cwd_config.exists():
        return str(cwd_config)
    
    # 4. 尝试查找项目根目录（通过向上查找包含特征文件的目录）
    current = Path.cwd()
    while current != current.parent:
        config_file = current / "config.yaml"
        if config_file.exists():
            return str(config_file)
        
        # 检查是否是项目根目录（包含特定文件）
        if (current / "requirements.txt").exists() or (current / "pyproject.toml").exists():
            break
        
        current = current.parent
    
    return None


def load_config(config_path: Optional[str] = None) -> CruxConfig:
    """
    加载配置
    
    如果找到配置文件则从文件加载，否则返回默认配置。
    
    Args:
        config_path: 可选的配置文件路径
        
    Returns:
        CruxConfig 实例
    """
    found_path = find_config_file(config_path)
    
    if found_path:
        print(f"加载配置文件: {found_path}")
        return CruxConfig.from_yaml(found_path)
    else: 
        print("未找到配置文件，使用默认配置")
    # 返回默认配置
    return CruxConfig()


# 全局配置实例（延迟初始化）
_global_config: Optional[CruxConfig] = None


def get_config() -> CruxConfig:
    """获取全局配置实例"""
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config


def set_config(config: CruxConfig):
    """设置全局配置实例"""
    global _global_config
    _global_config = config
