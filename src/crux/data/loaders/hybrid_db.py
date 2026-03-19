"""
混合检索加载器

集成 BM25 稀疏检索 + 向量稠密检索 + Rerank 重排序。
"""

import os
import gc
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from src.crux.data.loaders.base import BaseDataLoader, apply_constraints
from src.crux.config import CruxConfig, RetrieverConfig
from src.crux.utils.llm_client import APIEmbeddingModel, APIReranker
from tqdm import tqdm
from loguru import logger
import bm25s


# ============================================================
# HybridRetriever：混合检索引擎
# ============================================================

class HybridRetriever:
    """混合检索引擎（BM25 + Dense + Rerank）"""

    def __init__(self, df_papers, retriever_cfg: RetrieverConfig):

        self.df_papers = df_papers
        self.cfg = retriever_cfg

        # ---- Embedding 模型 (API) ----
        logger.info(f"Using API for embeddings ({self.cfg.model_emb})")
        self.model_emb = APIEmbeddingModel(
            model_name=self.cfg.model_emb,
            api_key=self.cfg.api_key_emb,
            base_url=self.cfg.base_url_emb,
            max_retries=self.cfg.max_retries,
        )

        # ---- Reranker 模型 (API) ----
        logger.info(f"Using API Reranker ({self.cfg.model_rerank})...")
        self.reranker = APIReranker(
            model_name=self.cfg.model_rerank,
            api_key=self.cfg.api_key_rerank,
            base_url=self.cfg.base_url_rerank,
            max_retries=self.cfg.max_retries,
        )
        self.get_papers_embeddings()
        self.get_papers_bm25()
    # ----------------------------------------------------------
    # BM25 索引
    # ----------------------------------------------------------
    def get_papers_bm25(self):
        path = self.cfg.papers_index_save_path
        if os.path.exists(path):
            logger.info("Loading existing BM25 index...")
            logger.info(path)
            self.papers_bm25 = bm25s.BM25.load(path)
        else:
            def tokenize_corpus(texts):
                return bm25s.tokenize([str(t).lower()[:2000] for t in texts], stopwords="en")

            papers_tokens = tokenize_corpus(self.df_papers["combined_text"].tolist())
            papers_bm25 = bm25s.BM25()
            papers_bm25.index(papers_tokens)
            self.papers_bm25 = papers_bm25
            logger.info("Saving BM25 index...")
            os.makedirs(path, exist_ok=True)
            self.papers_bm25.save(path)
            del papers_tokens
            gc.collect()

    # ----------------------------------------------------------
    # 向量嵌入
    # ----------------------------------------------------------
    def get_papers_embeddings(self):
        logger.info("Preparing papers embeddings...")
        path = os.path.join(self.cfg.papers_embeddings_save_path, "embeddings.npy")
        logger.info(path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            logger.info("Loading existing papers embeddings...")
            self.papers_embeddings = np.load(path)  # noqa: F821 — np imported above
            logger.info(f"papers_embeddings.shape:{self.papers_embeddings.shape}")
        else:
            logger.info("No embeddings available...")
            truncated_papers = [str(t)[:2000] for t in self.df_papers["combined_text"].tolist()]
            papers_embeddings = self.model_emb.encode(
                truncated_papers,
                batch_size=self.cfg.batch_size if not self.cfg.use_api_emb else 32,
                convert_to_tensor=False,
                normalize_embeddings=True,
                show_progress_bar=True,
            )
            self.papers_embeddings = papers_embeddings
            logger.info("Saving papers embeddings...")
            np.save(path, papers_embeddings)
        logger.info("Papers embeddings ready.")

    # ----------------------------------------------------------
    # 混合检索
    # ----------------------------------------------------------
    def hybrid_search(self, queries, query_tokens, top_k):


        logger.info(f"[HybridRetriever] Starting hybrid search for queries: {queries} with tokens: {query_tokens}")

        # Dense Search
        dense_res = {}
        if queries:
            logger.info(f"[HybridRetriever] Encoding queries: {len(queries)} queries")
            queries_emb = self.model_emb.encode(
                queries, convert_to_tensor=False, normalize_embeddings=True, show_progress_bar=True
            )
            queries_emb = np.array(queries_emb)
            logger.info(f"[HybridRetriever] Query embeddings computed. Shape: {queries_emb.shape}")

            # Numpy-based semantic search (cosine similarity on normalized vectors)
            corpus_emb = np.array(self.papers_embeddings)
            scores = queries_emb @ corpus_emb.T  # cosine similarity for normalized vectors
            n_papers = len(self.df_papers)
            hits_list = []
            for q_scores in scores:
                top_indices = np.argsort(-q_scores)[:top_k]
                hits_list.append(
                    [{"corpus_id": int(idx), "score": float(q_scores[idx])} for idx in top_indices if idx < n_papers]
                )

            dense_res_list = []
            for i, hits in enumerate(hits_list):
                dense_res_list.append(
                    {self.df_papers.iloc[h["corpus_id"]]["arxiv_id"]: h["score"] for h in hits}
                )

            logger.info(
                f"[HybridRetriever] Dense search done. Top candidate counts: {[len(res) for res in dense_res_list]}"
            )

            # First fusion (if multiple queries)
            if len(dense_res_list) > 1:
                dense_fused = {}
                for arxiv_id in set().union(*[set(res.keys()) for res in dense_res_list]):
                    r = {}
                    for i, res in enumerate(dense_res_list):
                        r[i] = list(res).index(arxiv_id) if arxiv_id in res else 2 * top_k
                    dense_fused[arxiv_id] = sum(
                        [1 / (self.cfg.fusion_k + r[i]) for i in range(len(dense_res_list))]
                    )
                dense_fused = sorted(dense_fused.items(), key=lambda x: x[1], reverse=True)
                dense_res = {arxiv_id: score for arxiv_id, score in dense_fused}
            else:
                dense_res = dense_res_list[0] if dense_res_list else {}
            logger.info(f"[HybridRetriever] Dense fusion done. Candidates after fusion: {len(dense_res)}")
        else:
            logger.info("[HybridRetriever] No queries provided, skipping dense search.")

        # Sparse Search (BM25)
        sparse_res = {}
        has_tokens = any(len(t) > 0 for t in query_tokens) if query_tokens else False

        if has_tokens:
            docs, scores = self.papers_bm25.retrieve(query_tokens, k=top_k)
            n_papers = len(self.df_papers)
            if len(docs) > 0 and len(docs[0]) > 0:
                sparse_res = {
                    self.df_papers.iloc[docs[0][i]]["arxiv_id"]: scores[0][i]
                    for i in range(len(docs[0]))
                    if docs[0][i] < n_papers
                }
            logger.info(f"[HybridRetriever] Sparse search done. Candidates: {len(sparse_res)}")
        else:
            logger.info("[HybridRetriever] No tokens provided, skipping sparse search.")

        # Fusion
        fused = {}
        for arxiv_id in set(dense_res) | set(sparse_res):
            r_dense = list(dense_res).index(arxiv_id) if arxiv_id in dense_res else 2 * top_k
            r_sparse = list(sparse_res).index(arxiv_id) if arxiv_id in sparse_res else 2 * top_k
            fused[arxiv_id] = (1 / (self.cfg.fusion_k + r_dense)) + (
                1 / (self.cfg.fusion_k + r_sparse)
            )
        logger.info(f"[HybridRetriever] Final fusion done. Total candidates: {len(fused)}")
        return sorted(fused.items(), key=lambda x: x[1], reverse=True)[:top_k]

    # ----------------------------------------------------------
    # Rerank
    # ----------------------------------------------------------
    def rerank(self, query, candidates, top_k):
        pairs = []
        valid_ids = []
        paper_map = dict(zip(self.df_papers["arxiv_id"], self.df_papers["combined_text"]))

        for arxiv_id, _ in candidates:
            text = paper_map.get(arxiv_id, "")
            if text:
                pairs.append([query, str(text)[:2000]])
                valid_ids.append(arxiv_id)

        if not pairs:
            return []

        scores = self.reranker.predict(
            pairs, batch_size=self.cfg.batch_size, show_progress_bar=False
        )
        scored = sorted(zip(valid_ids, scores), key=lambda x: x[1], reverse=True)
        return [(c[0], float(c[1])) for c in scored[:top_k]]


# ============================================================
# HybridDataLoader：混合检索加载器
# ============================================================

class HybridDataLoader(BaseDataLoader):
    """
    混合检索加载器
    目前仅支持从 JSON 文件加载数据
    """

    DEFAULT_PATH = "data/ir_papers.json"

    def __init__(self, config: Optional[CruxConfig] = None):
        super().__init__(config)
        self.file_path = (config.data_source_path if config else None) or self.DEFAULT_PATH
        self._retriever: Optional[HybridRetriever] = None
        self._full_df_papers: Optional[pd.DataFrame] = None  # 全量数据的 DataFrame 缓存

    def load(self) -> List[Dict[str, Any]]:
        """
        加载数据

        支持:
        - .json 文件 (原有逻辑)
        - .parquet 文件 (pandas + 字段映射)
        - .csv 文件 (pandas + 字段映射)
        """
        if self._data is not None:
            return self._data
        path = Path(self.file_path)
        if not path.exists():
            logger.info(f"[HybridDataLoader] 警告: 文件不存在 {path}, 使用空数据")
            self._data = []
            return self._data

        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                self._data = self._load_json(path)
            elif suffix == ".parquet":
                self._data = self._load_dataframe(pd.read_parquet(path))
            elif suffix == ".csv":
                self._data = self._load_dataframe(pd.read_csv(path))
            else:
                logger.info(f"[HybridDataLoader] 警告: 不支持的文件格式 {suffix}, 使用空数据")
                self._data = []
        except Exception as e:
            logger.info(f"[HybridDataLoader] 加载数据失败: {e}")
            self._data = []

        self._data = self._data or []
        logger.info(f"[HybridDataLoader] 成功加载 {len(self._data)} 条数据")
        return self._data

    # ----------------------------------------------------------
    # JSON 加载
    # ----------------------------------------------------------
    @staticmethod
    def _load_json(path: Path) -> List[Dict[str, Any]]:
        """从 JSON 文件加载（原有逻辑）"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get("papers", [])
        else:
            logger.info(f"[HybridDataLoader] 警告: 不支持的 JSON 数据格式 {type(data)}")
            return []

    # ----------------------------------------------------------
    # DataFrame 加载（parquet / csv）+ 字段映射
    # ----------------------------------------------------------
    @staticmethod
    def _load_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        从 DataFrame 加载数据并映射字段（简化版）

        原始 arxiv 字段 → 目标字段:
            id          → arxiv_id
            title       → title (清理换行)
            abstract    → abstract (清理换行和首尾空白)
            update_date → date
            其他字段留空
        """
        logger.info(f"DataFrame shape: {df.shape}")

        # 只取需要的列，缺失则补空字符串
        out = pd.DataFrame()
        out["arxiv_id"] = df["id"].astype(str).str.strip() if "id" in df.columns else ""
        out["title"] = (
            df["title"].fillna("").astype(str)
            .str.replace(r"\n", " ", regex=False)
            .str.replace(r"\\n", " ", regex=False)
            .str.strip()
        ) if "title" in df.columns else ""
        out["abstract"] = (
            df["abstract"].fillna("").astype(str)
            .str.replace(r"\n", " ", regex=False)
            .str.replace(r"\\n", " ", regex=False)
            .str.strip()
        ) if "abstract" in df.columns else ""
        out["date"] = df["update_date"].fillna("").astype(str).str.strip() if "update_date" in df.columns else ""
        out["arxiv_url"] = ""
        out["authors"] = [[] for _ in range(len(df))]

        records = out.to_dict(orient="records")
        logger.info(f"Loaded {len(records)} records")
        return records

    def search(
        self,
        keywords: List[str],
        vector_queries: List[str],
        constraints: Dict[str, Any],
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        混合检索接口

        Args:
            keywords: BM25 关键词列表
            vector_queries: 向量检索查询列表
            constraints: 约束条件
            top_k: 返回结果数量

        Returns:
            检索结果列表
        """
        if self._data is None:
            self.load()
        logger.info(f"[HybridDataLoader] 全量数据: {len(self._data)} 条")
        
        # 1. 应用元数据过滤（用于最终结果过滤）
        logger.info(f"[HybridDataLoader] constraints: {constraints}")
        filtered_docs = apply_constraints(self._data, constraints)
        logger.info(f"[HybridDataLoader] 过滤后剩余: {len(filtered_docs)} 条")
        
        if not filtered_docs:
            logger.info("[HybridDataLoader] 警告: 过滤后无数据")
            return []

        retriever_cfg = self.config.retriever
        
        # 2. 初始化或复用 HybridRetriever（基于全量数据，只创建一次）
        if self._retriever is None:
            logger.info(f"[HybridDataLoader] 初始化 HybridRetriever (全量数据: {len(self._data)} 条)")
            # 基于全量数据创建 DataFrame
            self._full_df_papers = pd.DataFrame(self._data)
            self._full_df_papers.fillna("", inplace=True)
            
            # 确保必要列存在
            if "title" not in self._full_df_papers.columns:
                self._full_df_papers["title"] = ""
            if "abstract" not in self._full_df_papers.columns:
                self._full_df_papers["abstract"] = ""
            
            self._full_df_papers["combined_text"] = (
                self._full_df_papers["title"].astype(str) + " " + self._full_df_papers["abstract"].astype(str)
            )
            
            self._retriever = HybridRetriever(self._full_df_papers, retriever_cfg)
        else:
            logger.info("[HybridDataLoader] 复用已缓存的 HybridRetriever")
        
        retriever = self._retriever
        query_tokens = [keywords]
        candidates = retriever.hybrid_search(
            queries=vector_queries,
            query_tokens=query_tokens,
            top_k=top_k,
        )

        # Create a lookup dict for fast access
        doc_lookup = {doc["arxiv_id"]: doc for doc in filtered_docs}
        if not retriever_cfg.rerank:
            sorted_docs = []
            for arxiv_id, score in candidates:
                if arxiv_id in doc_lookup:
                    doc = doc_lookup[arxiv_id].copy()
                    doc["score"] = float(score)
                    sorted_docs.append(doc)
            return sorted_docs
        else:
            merged_query = " ".join(vector_queries)
            tops = retriever.rerank(merged_query, candidates, top_k)
            sorted_docs = []
            for arxiv_id, score in tops:
                if arxiv_id in doc_lookup:
                    doc = doc_lookup[arxiv_id].copy()
                    doc["score"] = float(score)
                    sorted_docs.append(doc)
            return sorted_docs
