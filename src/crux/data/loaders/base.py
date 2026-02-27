"""
数据加载器基类

定义所有数据加载器的通用接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from src.crux.config import CruxConfig


class BaseDataLoader(ABC):
    """
    数据加载器抽象基类
    
    所有数据加载器都需要实现:
    - load(): 加载全部数据
    - search(): 执行检索
    """
    
    def __init__(self, config: Optional[CruxConfig] = None):
        self.config = config or CruxConfig()
        self._data: Optional[List[Dict[str, Any]]] = None
    
    @abstractmethod
    def load(self) -> List[Dict[str, Any]]:
        """
        加载数据
        
        Returns:
            文档列表
        """
        pass
    
    @abstractmethod
    def search(
        self,
        keywords: List[str],
        vector_queries: List[str],
        constraints: Dict[str, Any],
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            keywords: BM25 关键词
            vector_queries: 向量检索查询
            constraints: 约束条件
            top_k: 返回数量
            
        Returns:
            检索结果列表
        """
        pass
    
    def get_by_id(self, doc_id: Any) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            文档对象或 None
        """
        if self._data is None:
            self._data = self.load()
        
        for doc in self._data:
            if doc.get("id") == doc_id or doc.get("arxiv_id") == doc_id:
                return doc
        return None
    
    def count(self) -> int:
        """获取文档总数"""
        if self._data is None:
            self._data = self.load()
        return len(self._data)


# ============================================================
# 约束处理工具函数
# ============================================================

def apply_constraints(
    docs: List[Dict[str, Any]],
    constraints: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """应用约束条件过滤文档"""
    filtered = docs

    metadata_constraints = constraints.get("structured_metadata", [])

    for c in metadata_constraints:
        field = c.get("field")
        op = c.get("operator")
        value = c.get("value")

        if not field or not op:
            continue

        new_filtered = []
        for doc in filtered:
            doc_value = get_field_value(doc, field)
            if check_constraint(doc_value, op, value):
                new_filtered.append(doc)
        filtered = new_filtered

    return filtered


def get_field_value(doc: Dict[str, Any], field: str) -> Any:
    """获取文档字段值，支持嵌套字段和类型转换"""
    # 特殊处理 year 字段：从 date 字符串提取年份
    if field == "year":
        date_value = doc.get("date")
        if date_value and isinstance(date_value, str):
            try:
                year = int(date_value.split("-")[0])
                return year
            except (ValueError, IndexError):
                pass
        for path in ["metadata.date", "alphaxiv_detail.publication_date"]:
            value = get_nested_value(doc, path)
            if value and isinstance(value, str):
                try:
                    year = int(value.split("-")[0])
                    return year
                except (ValueError, IndexError):
                    continue
        return None

    # 直接字段
    if field in doc:
        return doc[field]

    # 常用嵌套字段映射
    field_mappings = {
        "category": ["metadata.all_categories", "metadata.primary_category", "metadata.category"],
        "categories": ["metadata.all_categories", "alphaxiv_detail.topics"],
        "source": ["source"],
    }

    paths = field_mappings.get(field, [field])

    for path in paths:
        value = get_nested_value(doc, path)
        if value is not None:
            return value

    return None


def check_constraint(doc_value: Any, op: str, target: Any) -> bool:
    """检查约束条件"""
    if doc_value is None:
        return False

    try:
        if op == "eq":
            return doc_value == target
        elif op == "neq":
            return doc_value != target
        elif op == "gt":
            return doc_value > target
        elif op == "lt":
            return doc_value < target
        elif op == "gte":
            return doc_value >= target
        elif op == "lte":
            return doc_value <= target
        elif op == "in":
            if isinstance(target, list):
                if isinstance(doc_value, list):
                    return bool(set(doc_value) & set(target))
                return doc_value in target
            return target in str(doc_value)
        elif op == "contains":
            return target in str(doc_value)
        elif op == "range":
            if isinstance(target, list) and len(target) == 2:
                return int(target[0]) <= doc_value <= int(target[1])
        else:
            return True
    except Exception:
        return False

    return True


def get_nested_value(doc: Dict[str, Any], path: str) -> Any:
    """获取嵌套字段值"""
    parts = path.split(".")
    value = doc
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value
