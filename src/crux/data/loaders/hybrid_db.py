"""
混合检索加载器

集成 BM25 稀疏检索 + 向量稠密检索 + Rerank 重排序。
"""

import os
import gc
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.crux.data.loaders.base import BaseDataLoader, apply_constraints
from src.crux.config import CruxConfig, RetrieverConfig
from src.crux.utils.llm_client import APIEmbeddingModel, APIReranker


# ============================================================
# HybridRetriever：混合检索引擎
# ============================================================

class HybridRetriever:
    """混合检索引擎（BM25 + Dense + Rerank）"""

    def __init__(self, df_papers, retriever_cfg: RetrieverConfig):

        self.df_papers = df_papers
        self.cfg = retriever_cfg

        # ---- Embedding 模型 (API) ----
        print(f"Using API for embeddings ({self.cfg.model_emb})")
        self.model_emb = APIEmbeddingModel(
            model_name=self.cfg.model_emb,
            api_key=self.cfg.api_key_emb,
            base_url=self.cfg.base_url_emb,
            max_retries=self.cfg.max_retries,
        )

        # ---- Reranker 模型 (API) ----
        print(f"Using API Reranker ({self.cfg.model_rerank})...")
        self.reranker = APIReranker(
            model_name=self.cfg.model_rerank,
            api_key=self.cfg.api_key_rerank,
            base_url=self.cfg.base_url_rerank,
            max_retries=self.cfg.max_retries,
        )

    # ----------------------------------------------------------
    # BM25 索引
    # ----------------------------------------------------------
    def get_papers_bm25(self):
        import bm25s

        path = self.cfg.papers_index_save_path
        if os.path.exists(path):
            print("Loading existing BM25 index...")
            self.papers_bm25 = bm25s.BM25.load(path)
        else:
            def tokenize_corpus(texts):
                return bm25s.tokenize([str(t).lower()[:2000] for t in texts], stopwords="en")

            papers_tokens = tokenize_corpus(self.df_papers["combined_text"].tolist())
            papers_bm25 = bm25s.BM25()
            papers_bm25.index(papers_tokens)
            self.papers_bm25 = papers_bm25
            print("Saving BM25 index...")
            os.makedirs(path, exist_ok=True)
            self.papers_bm25.save(path)
            del papers_tokens
            gc.collect()

    # ----------------------------------------------------------
    # 向量嵌入
    # ----------------------------------------------------------
    def get_papers_embeddings(self):
        import numpy as np

        print("Preparing papers embeddings...")
        path = os.path.join(self.cfg.papers_embeddings_save_path, "embeddings.npy")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if os.path.exists(path):
            print("Loading existing papers embeddings...")
            self.papers_embeddings = np.load(path)  # noqa: F821 — np imported above
        else:
            truncated_papers = [str(t)[:2000] for t in self.df_papers["combined_text"].tolist()]
            papers_embeddings = self.model_emb.encode(
                truncated_papers,
                batch_size=self.cfg.batch_size if not self.cfg.use_api_emb else 32,
                convert_to_tensor=False,
                normalize_embeddings=True,
                show_progress_bar=True,
            )
            self.papers_embeddings = papers_embeddings
            print("Saving papers embeddings...")
            np.save(path, papers_embeddings)
        print("Papers embeddings ready.")

    # ----------------------------------------------------------
    # 混合检索
    # ----------------------------------------------------------
    def hybrid_search(self, queries, query_tokens, top_k):
        import numpy as np

        self.get_papers_embeddings()
        self.get_papers_bm25()
        print(f"[HybridRetriever] Starting hybrid search for queries: {queries} with tokens: {query_tokens}")

        # Dense Search
        dense_res = {}
        if queries:
            print(f"[HybridRetriever] Encoding queries: {len(queries)} queries")
            queries_emb = self.model_emb.encode(
                queries, convert_to_tensor=False, normalize_embeddings=True, show_progress_bar=True
            )
            queries_emb = np.array(queries_emb)
            print(f"[HybridRetriever] Query embeddings computed. Shape: {queries_emb.shape}")

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

            print(
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
            print(f"[HybridRetriever] Dense fusion done. Candidates after fusion: {len(dense_res)}")
        else:
            print("[HybridRetriever] No queries provided, skipping dense search.")

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
            print(f"[HybridRetriever] Sparse search done. Candidates: {len(sparse_res)}")
        else:
            print("[HybridRetriever] No tokens provided, skipping sparse search.")

        # Fusion
        fused = {}
        for arxiv_id in set(dense_res) | set(sparse_res):
            r_dense = list(dense_res).index(arxiv_id) if arxiv_id in dense_res else 2 * top_k
            r_sparse = list(sparse_res).index(arxiv_id) if arxiv_id in sparse_res else 2 * top_k
            fused[arxiv_id] = (1 / (self.cfg.fusion_k + r_dense)) + (
                1 / (self.cfg.fusion_k + r_sparse)
            )
        print(f"[HybridRetriever] Final fusion done. Total candidates: {len(fused)}")
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
        return [c[0] for c in scored[:top_k]]


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

    def load(self) -> List[Dict[str, Any]]:
        """加载数据"""
        if self._data is not None:
            return self._data
        path = Path(self.file_path)
        if not path.exists():
            print(f"[HybridDataLoader] 警告: 文件不存在 {path}, 使用空数据")
            self._data = []
            return self._data

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                self._data = data
            elif isinstance(data, dict):
                self._data = data.get("papers", [])
            else:
                print(f"[HybridDataLoader] 警告: 不支持的数据格式 {type(data)}, 使用空数据")
        except Exception as e:
            print(f"[HybridDataLoader] 加载数据失败: {e}")
        self._data = self._data or []
        return self._data

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

        # 1. 应用元数据过滤
        filtered_docs = apply_constraints(self._data, constraints)
        print(f"[HybridDataLoader] 过滤后剩余: {len(filtered_docs)} 条")

        import pandas as pd

        df_papers = pd.DataFrame(filtered_docs)
        df_papers.fillna("", inplace=True)
        df_papers["combined_text"] = df_papers.apply(
            lambda x: f"{x['title']} {x['abstract']}", axis=1
        )

        retriever_cfg = self.config.retriever
        retriever = HybridRetriever(df_papers, retriever_cfg)
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
            for arxiv_id, _ in candidates:
                if arxiv_id in doc_lookup:
                    sorted_docs.append(doc_lookup[arxiv_id])
            return sorted_docs
        else:
            merged_query = " ".join(vector_queries)
            tops = retriever.rerank(merged_query, candidates, top_k)
            sorted_docs = []
            for arxiv_id in tops:
                if arxiv_id in doc_lookup:
                    sorted_docs.append(doc_lookup[arxiv_id])
            return sorted_docs
