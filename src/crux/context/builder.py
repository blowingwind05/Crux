"""
上下文构建器

组合 context、超参、输入、环境变量进行 prompt 构造。
"""

import os
from typing import Optional, Dict, Any

from src.crux.config import CruxConfig
from src.crux.schemas.base import BaseSchema
from src.crux.schemas.paper_schema import PaperSchema
from src.crux.prompts.templates import INTENT_PARSING_TEMPLATE


class ContextBuilder:
    """
    上下文构建器
    
    负责:
    1. 根据 schema 类型加载对应的数据结构配置
    2. 组合环境变量、超参数和用户输入
    3. 构建完整的 prompt
    """
    
    # Schema 注册表
    SCHEMA_REGISTRY: Dict[str, type] = {
        "paper": PaperSchema,
    }
    
    def __init__(self, config: Optional[CruxConfig] = None):
        self.config = config or CruxConfig()
        self._schema_cache: Dict[str, BaseSchema] = {}
    
    def get_schema(self, schema_type: str) -> BaseSchema:
        """
        获取 Schema 实例
        
        Args:
            schema_type: schema 类型名称
            
        Returns:
            Schema 实例
        """
        if schema_type not in self._schema_cache:
            schema_class = self.SCHEMA_REGISTRY.get(schema_type)
            if schema_class is None:
                raise ValueError(f"未知的 schema 类型: {schema_type}")
            self._schema_cache[schema_type] = schema_class()
        
        return self._schema_cache[schema_type]
    
    def register_schema(self, name: str, schema_class: type):
        """
        注册新的 Schema 类型
        
        Args:
            name: schema 名称
            schema_class: schema 类
        """
        self.SCHEMA_REGISTRY[name] = schema_class
    
    def build_intent_prompt(
        self,
        query: str,
        current_date: str,
        schema_type: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建意图解析 prompt
        
        Args:
            query: 用户查询
            current_date: 当前日期
            schema_type: schema 类型
            extra_context: 额外上下文
            
        Returns:
            完整的 prompt
        """
        schema_type = schema_type or self.config.schema_type
        schema = self.get_schema(schema_type)
        
        # 获取 schema 描述
        schema_description = schema.to_prompt_context()
        
        # 获取环境变量
        env_context = self._build_env_context()
        
        # 构建 prompt
        prompt = INTENT_PARSING_TEMPLATE
        prompt = prompt.replace("{{current_date}}", current_date)
        prompt = prompt.replace("{{user_query}}", query)
        prompt = prompt.replace("{{schema_description}}", schema_description)
        prompt = prompt.replace("{{env_context}}", env_context)
        
        # 添加额外上下文
        if extra_context:
            extra_text = "\n".join([f"- {k}: {v}" for k, v in extra_context.items()])
            prompt = prompt.replace("{{extra_context}}", extra_text)
        else:
            prompt = prompt.replace("{{extra_context}}", "")
        
        return prompt
    
    def build_prompt(
        self,
        template: str,
        schema_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        通用 prompt 构建
        
        Args:
            template: prompt 模板
            schema_type: schema 类型
            **kwargs: 模板变量
            
        Returns:
            完整的 prompt
        """
        schema_type = schema_type or self.config.schema_type
        
        # 添加 schema 描述
        if "{{schema_description}}" in template and schema_type:
            schema = self.get_schema(schema_type)
            kwargs["schema_description"] = schema.to_prompt_context()
        
        # 添加环境上下文
        if "{{env_context}}" in template:
            kwargs["env_context"] = self._build_env_context()
        
        # 替换模板变量
        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        
        return result
    
    def _build_env_context(self) -> str:
        """构建环境上下文"""
        env_vars = {
            "DEBUG": os.getenv("CRUX_DEBUG", "false"),
            "MAX_ITERATIONS": str(self.config.search.max_iterations),
            "TOP_K": str(self.config.search.top_k),
        }
        
        lines = ["## 环境配置"]
        for k, v in env_vars.items():
            lines.append(f"- {k}: {v}")
        
        return "\n".join(lines)
