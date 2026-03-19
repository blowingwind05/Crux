"""
Model Inference Router - 模型推理路由

提供 OpenAI 兼容的 Embedding API 和 Rerank API。

- POST /v1/embeddings  → 兼容 OpenAI Embeddings 格式
- POST /v1/rerank      → 兼容 APIReranker 调用格式
"""

from fastapi import APIRouter, HTTPException
from loguru import logger

from backend.models.inference import (
    EmbeddingRequest,
    EmbeddingResponse,
    RerankRequest,
    RerankResponse,
)
from backend.services.model_service import model_service

router = APIRouter(tags=["model_inference"])


@router.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    """
    生成文本嵌入向量（兼容 OpenAI /v1/embeddings）

    APIEmbeddingModel 通过 OpenAI SDK 调用此端点。
    """
    try:
        texts = request.input if isinstance(request.input, list) else [request.input]
        embeddings = model_service.encode(texts)
        return EmbeddingResponse.from_embeddings(embeddings, model=request.model)
    except Exception as e:
        logger.error(f"Embedding inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v1/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest):
    """
    文档重排序

    APIReranker 通过 HTTP POST 调用此端点。
    """
    try:
        scores = model_service.rerank(
            query=request.query,
            documents=request.documents,
        )
        return RerankResponse.from_scores(
            scores=scores,
            documents=request.documents,
            model=request.model,
            top_n=request.top_n,
            return_documents=request.return_documents,
        )
    except Exception as e:
        logger.error(f"Rerank inference error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
