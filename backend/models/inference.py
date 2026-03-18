"""
Backend Models - 模型推理请求/响应定义

兼容 OpenAI Embedding API 和 Rerank API 格式。
"""

import time
from typing import List, Optional, Union
from pydantic import BaseModel, Field


# ============================================================
# Embedding 模型
# ============================================================

class EmbeddingRequest(BaseModel):
    """Embedding 请求（兼容 OpenAI /v1/embeddings）"""
    input: Union[str, List[str]] = Field(..., description="待编码文本或文本列表")
    model: str = Field(default="bge-m3", description="模型名称")
    encoding_format: str = Field(default="float", description="编码格式")


class EmbeddingData(BaseModel):
    """单条 Embedding 结果"""
    object: str = "embedding"
    embedding: List[float]
    index: int


class EmbeddingUsage(BaseModel):
    """Token 用量统计"""
    prompt_tokens: int = 0
    total_tokens: int = 0


class EmbeddingResponse(BaseModel):
    """Embedding 响应（兼容 OpenAI 格式）"""
    object: str = "list"
    data: List[EmbeddingData]
    model: str
    usage: EmbeddingUsage = Field(default_factory=EmbeddingUsage)

    @classmethod
    def from_embeddings(cls, embeddings: List[List[float]], model: str) -> "EmbeddingResponse":
        """从 embedding 列表构建响应"""
        data = [
            EmbeddingData(embedding=emb, index=i)
            for i, emb in enumerate(embeddings)
        ]
        return cls(data=data, model=model)


# ============================================================
# Rerank 模型
# ============================================================

class RerankRequest(BaseModel):
    """Rerank 请求"""
    query: str = Field(..., description="查询文本")
    documents: List[str] = Field(..., description="待排序文档列表")
    model: str = Field(default="bge-reranker-v2-m3", description="模型名称")
    top_n: Optional[int] = Field(default=None, description="返回 top N 结果，默认全部返回")
    return_documents: bool = Field(default=False, description="是否在结果中返回文档原文")


class RerankResult(BaseModel):
    """单条 Rerank 结果"""
    index: int
    relevance_score: float
    document: Optional[str] = None


class RerankResponse(BaseModel):
    """Rerank 响应"""
    results: List[RerankResult]
    model: str

    @classmethod
    def from_scores(
        cls,
        scores: List[float],
        documents: List[str],
        model: str,
        top_n: Optional[int] = None,
        return_documents: bool = False,
    ) -> "RerankResponse":
        """从分数列表构建响应"""
        indexed_scores = list(enumerate(scores))
        indexed_scores.sort(key=lambda x: x[1], reverse=True)

        if top_n is not None:
            indexed_scores = indexed_scores[:top_n]

        results = [
            RerankResult(
                index=idx,
                relevance_score=float(score),
                document=documents[idx] if return_documents else None,
            )
            for idx, score in indexed_scores
        ]
        return cls(results=results, model=model)
