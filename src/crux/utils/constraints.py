"""
约束处理工具模块

提供文档过滤和约束检查的通用功能。
"""

from typing import List, Dict, Any


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
        # 尝试从 date 字段提取年份
        date_value = doc.get("date")
        if date_value and isinstance(date_value, str):
            try:
                # 格式如 "2025-12-29"
                year = int(date_value.split("-")[0])
                return year
            except (ValueError, IndexError):
                pass
        # 也检查嵌套路径
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