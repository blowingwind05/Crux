"""
Model Service - 本地 Embedding & Reranker 模型服务

加载 SentenceTransformer（Embedding）和 CrossEncoder（Reranker），
提供推理接口供 router 调用。
"""

import os
from typing import List, Optional, Dict, Any
from loguru import logger


class ModelService:
    """本地模型服务 — 管理 Embedding 和 Reranker 模型的生命周期"""

    def __init__(self):
        self._embedding_model = None
        self._reranker_model = None
        self._embedding_model_name: str = ""
        self._reranker_model_name: str = ""
        self._device: str = "cuda"
        self._batch_size: int = 64

    # ----------------------------------------------------------
    # 初始化 / 配置
    # ----------------------------------------------------------
    def configure(
        self,
        embedding_model: str = "/workspace/bge-m3",
        reranker_model: str = "/workspace/bge-reranker-v2-m3",
        device: str = "cuda",
        batch_size: int = 64,
    ):
        """从配置参数设定模型路径等，不立即加载"""
        self._embedding_model_name = embedding_model
        self._reranker_model_name = reranker_model
        self._device = device
        self._batch_size = batch_size
        logger.info(
            f"ModelService configured: emb={embedding_model}, "
            f"rerank={reranker_model}, device={device}"
        )

    def load_models(self):
        """预加载所有模型（在应用启动时调用）"""
        self._load_embedding_model()
        self._load_reranker_model()

    # ----------------------------------------------------------
    # Embedding
    # ----------------------------------------------------------
    def _load_embedding_model(self):
        if self._embedding_model is not None:
            return
        from sentence_transformers import SentenceTransformer

        logger.info(f"Loading embedding model: {self._embedding_model_name} ...")
        self._embedding_model = SentenceTransformer(
            self._embedding_model_name, device=self._device
        )
        logger.info("Embedding model loaded.")

    def encode(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
        normalize: bool = True,
    ) -> List[List[float]]:
        """
        编码文本为向量

        Args:
            texts: 待编码文本列表
            batch_size: 批大小
            normalize: 是否 L2 归一化

        Returns:
            嵌入向量列表 (每个元素为 float 列表)
        """
        self._load_embedding_model()
        bs = batch_size or self._batch_size
        embeddings = self._embedding_model.encode(
            texts,
            batch_size=bs,
            show_progress_bar=False,
            normalize_embeddings=normalize,
        )
        return embeddings.tolist()

    # ----------------------------------------------------------
    # Reranker
    # ----------------------------------------------------------
    def _load_reranker_model(self):
        if self._reranker_model is not None:
            return
        from sentence_transformers import CrossEncoder

        logger.info(f"Loading reranker model: {self._reranker_model_name} ...")
        self._reranker_model = CrossEncoder(
            self._reranker_model_name, device=self._device
        )
        logger.info("Reranker model loaded.")

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_n: Optional[int] = None,
    ) -> List[float]:
        """
        对文档进行重排序

        Args:
            query: 查询文本
            documents: 待排序文档列表
            top_n: 只返回排序后的 top_n 个（此处返回全部分数，排序在 router 层做）

        Returns:
            每个文档对应的相关性分数列表（顺序与 documents 一致）
        """
        self._load_reranker_model()
        pairs = [[query, doc] for doc in documents]
        scores = self._reranker_model.predict(pairs)
        return [float(s) for s in scores]

    # ----------------------------------------------------------
    # 清理
    # ----------------------------------------------------------
    def unload(self):
        """释放模型资源"""
        import gc
        import torch

        self._embedding_model = None
        self._reranker_model = None
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        logger.info("Models unloaded.")


# 服务单例
model_service = ModelService()
