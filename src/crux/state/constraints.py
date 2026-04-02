"""
检索约束条件定义

结构化元数据过滤（字段/运算符/值）与非结构化文本模式匹配。
"""

from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class StructuredConstraint(BaseModel):
    """结构化元数据约束，用于数据库字段级过滤"""
    field: Annotated[
        Literal["year", "category", "source"],
        Field(description="字段名，例如 year、category、source")
    ]
    operator: Annotated[
        Literal["eq", "neq", "gt", "lt", "in", "range"],
        Field(description="比较操作符：eq(等于)、neq(不等于)、gt(大于)、lt(小于)、in(集合包含)、range(区间)")
    ]
    value: Annotated[
        Union[str, int, list[str], list[int]],
        Field(description="约束值，例如 2020、['AI','ML']、[2010,2020]")
    ]
    rationale: Annotated[
        Optional[str],
        Field(default=None, description="设置该约束的原因（用于调试或解释）")
    ]


class ContentConstraint(BaseModel):
    """非结构化文本模式约束，用于全文检索过滤或增强"""
    pattern: Annotated[
        str,
        Field(description="匹配模式，精确短语或正则表达式，例如 'climate change' 或 r'^F\\d+$'")
    ]
    pattern_type: Annotated[
        Literal["regex", "exact_phrase", "wildcard"],
        Field(description="匹配类型：regex(正则)、exact_phrase(精确短语)、wildcard(通配符)")
    ]
    scope: Annotated[
        Literal["full_text", "title"],
        Field(description="匹配范围：full_text(全文)、title(标题)")
    ]
    is_negative: Annotated[
        bool,
        Field(description="是否为排除条件：True 表示排除匹配该模式的文档")
    ]
    rationale: Annotated[
        Optional[str],
        Field(default=None, description="设置该约束的原因（用于调试或解释）")
    ]


class Constraints(BaseModel):
    """约束条件容器"""
    structured_metadata: Annotated[
        List[StructuredConstraint],
        Field(default_factory=list, description="结构化元数据约束列表")
    ]
    unstructured_content_patterns: Annotated[
        List[ContentConstraint],
        Field(default_factory=list, description="非结构化文本匹配约束列表")
    ]
