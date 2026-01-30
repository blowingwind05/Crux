"""
上下文构建器

组合 context、超参、输入、环境变量进行 prompt 构造。
"""

import os
from typing import Optional, Dict, Any

from src.crux.config import CruxConfig
from src.crux.modules.understanding.prompts import INTENT_PARSING_TEMPLATE


class ContextBuilder:
    """
    上下文构建器
    
    负责:
    1. 根据 YAML 配置加载数据结构描述
    2. 组合环境变量、超参数和用户输入
    3. 构建完整的 prompt
    """
    
    def __init__(self, config: Optional[CruxConfig] = None):
        self.config = config or CruxConfig()
    
    def get_schema_description(self) -> str:
        """
        获取 Schema 描述文本
        
        从配置中加载 YAML schema 并生成描述文本
        
        Returns:
            Schema 描述的格式化文本
        """
        schema = self.config.get_schema_config()
        return schema.get_field_descriptions()
    
    def build_intent_prompt(
        self,
        query: str,
        current_date: str,
        extra_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建意图解析 prompt
        
        Args:
            query: 用户查询
            current_date: 当前日期
            extra_context: 额外上下文
            
        Returns:
            完整的 prompt
        """
        # 获取 schema 描述
        schema_description = self.get_schema_description()
        
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
        **kwargs
    ) -> str:
        """
        通用 prompt 构建
        
        Args:
            template: prompt 模板
            **kwargs: 模板变量
            
        Returns:
            完整的 prompt
        """
        # 添加 schema 描述
        if "{{schema_description}}" in template:
            kwargs["schema_description"] = self.get_schema_description()
        
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

