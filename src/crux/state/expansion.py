"""
Facet Expansion 定义

由 Expansion Agent 针对每个 Facet 生成的检索扩展参数。
每个 FacetExpansion 与一个 Facet 1-to-1 对应（通过 facet_id 关联）。
"""

from typing import Annotated, List

from pydantic import BaseModel, Field


class FacetExpansion(BaseModel):
    """
    分面检索扩展 —— Expansion Agent 针对单个 Facet 生成的检索参数。

    - facet_query：面向该分面的自然语言检索句，用于稠密向量检索
    - sparse_keywords：BM25 关键词列表，用于稀疏检索
    - hypothetical_document：HyDE 假设文档，生成一段假想答案以增强语义检索效果
    """
    facet_id: Annotated[str, Field(description="对应的 Facet 标识，如 F1、F2")]
    facet_query: Annotated[str, Field(description="针对该分面的自然语言检索句，用于稠密向量检索")]
    sparse_keywords: Annotated[List[str], Field(
        default_factory=list,
        description="BM25 关键词列表，用于稀疏检索"
    )]
    hypothetical_document: Annotated[str, Field(
        description="HyDE 假设文档：生成一段假想答案，以增强向量检索的语义匹配效果"
    )]
