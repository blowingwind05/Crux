"""
Schema 基类

定义数据结构配置的通用接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseSchema(ABC):
    """
    数据结构配置抽象基类
    
    每种数据类型（论文、新闻、日志等）都应实现自己的 Schema。
    """
    
    # Schema 名称
    name: str = "base"
    
    # Schema 描述
    description: str = "Base schema"
    
    @abstractmethod
    def get_field_descriptions(self) -> str:
        """
        获取字段描述文本
        
        用于注入到 prompt 中，让 LLM 理解数据结构。
        
        Returns:
            字段描述的格式化文本
        """
        pass
    
    @abstractmethod
    def get_searchable_fields(self) -> List[str]:
        """
        获取可搜索的字段列表
        
        Returns:
            字段名列表
        """
        pass
    
    @abstractmethod
    def get_filterable_fields(self) -> List[Dict[str, Any]]:
        """
        获取可过滤的字段配置
        
        Returns:
            字段配置列表，每个包含 name, type, operators 等
        """
        pass
    
    def get_example_queries(self) -> List[str]:
        """
        获取示例查询
        
        Returns:
            示例查询列表
        """
        return []
    
    def get_schema_summary(self) -> str:
        """
        获取 Schema 摘要
        
        Returns:
            摘要文本
        """
        return f"{self.name}: {self.description}"
    
    def to_prompt_context(self) -> str:
        """
        转换为 prompt 上下文
        
        Returns:
            可嵌入 prompt 的文本
        """
        parts = [
            f"# 数据结构说明 ({self.name})",
            "",
            self.get_field_descriptions(),
            "",
            "## 可搜索字段",
            ", ".join(self.get_searchable_fields()),
            "",
            "## 可过滤字段",
        ]
        
        for field in self.get_filterable_fields():
            ops = ", ".join(field.get("operators", []))
            parts.append(f"- {field['name']} ({field['type']}): 支持 {ops}")
        
        return "\n".join(parts)
