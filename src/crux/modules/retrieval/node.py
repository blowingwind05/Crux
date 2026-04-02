"""
混合检索节点 (Retrieval Node)

Per-Facet 检索流程：
  每个 FacetExpansion 独立执行：
    - BM25：facet_query + sparse_keywords
    - Dense：facet_query + hypothetical_document (HyDE)
    - RRF 融合两路结果 → 该 Facet 的 TopK 候选文档

所有 Facet 并行执行，结果 flatten 附加 facet_id 标签后存入 candidate_docs。
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

from src.crux.utils.base import BaseNode


def _rrf_merge(
    bm25_docs: List[Dict[str, Any]],
    dense_docs: List[Dict[str, Any]],
    k: int = 60,
    top_n: int = 20,
) -> List[Dict[str, Any]]:
    """
    Reciprocal Rank Fusion — 融合 BM25 和 Dense 两路检索结果。

    RRF score = Σ 1 / (k + rank_i)，rank 从 0 开始。
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    for rank, doc in enumerate(bm25_docs):
        doc_id = doc.get("id") or doc.get("arxiv_id") or str(rank)
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    for rank, doc in enumerate(dense_docs):
        doc_id = doc.get("id") or doc.get("arxiv_id") or str(rank)
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = doc

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_map[doc_id] for doc_id, _ in ranked[:top_n]]


class RetrievalNode(BaseNode):
    """
    Per-Facet 混合召回节点

    每个 Facet 独立执行 BM25 + Dense 检索并 RRF 融合，所有 Facet 并行运行。
    """

    name = "retrieve"
    name_cn = "混合召回"
    description = "Per-Facet 混合检索，召回候选文档"

    def __init__(self, config=None):
        super().__init__(config)
        self._data_loader = None

    @property
    def data_loader(self):
        if self._data_loader is None:
            from src.crux.data import get_data_loader
            self._data_loader = get_data_loader(self.config)
        return self._data_loader

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.reset_logger()

        intent = state["intent"]
        expansions: List[Dict] = intent.get("expansions", [])
        constraints: Dict = intent.get("constraints", {})
        iteration: int = state.get("search_iteration", 0)

        if iteration > 0:
            self.log(f"第 {iteration + 1} 次迭代检索", level="INFO")

        self.log(f"开始 Per-Facet 检索，共 {len(expansions)} 个 Facet...")

        # 并行：每个 Facet 独立检索 + RRF
        facet_docs: Dict[str, List[Dict]] = {}
        with ThreadPoolExecutor(max_workers=max(len(expansions), 1)) as executor:
            futures = {
                executor.submit(self._retrieve_for_facet, exp, constraints): exp["facet_id"]
                for exp in expansions
            }
            for future in as_completed(futures):
                facet_id = futures[future]
                facet_docs[facet_id] = future.result()
                self.log(f"Facet {facet_id}: 召回 {len(facet_docs[facet_id])} 篇")

        # Flatten：附加 facet_id 标签
        candidate_docs = []
        for facet_id, docs in facet_docs.items():
            for doc in docs:
                candidate_docs.append({**doc, "facet_id": facet_id})

        self.log(f"候选文档总数: {len(candidate_docs)}（含跨 Facet 重复）", level="INFO")

        return self.build_result({"candidate_docs": candidate_docs})

    def _retrieve_for_facet(
        self,
        expansion: Dict[str, Any],
        constraints: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        对单个 FacetExpansion 执行 BM25 + Dense 检索并 RRF 融合。

        BM25  : [facet_query] + sparse_keywords
        Dense : [facet_query, hypothetical_document]
        """
        top_k = self.config.search.top_k

        bm25_keywords = [expansion["facet_query"]] + expansion.get("sparse_keywords", [])
        dense_queries = [
            q for q in [
                expansion.get("facet_query"),
                expansion.get("hypothetical_document"),
            ]
            if q
        ]

        bm25_docs = self.data_loader.search(
            keywords=bm25_keywords,
            vector_queries=[],
            constraints=constraints,
            top_k=top_k,
        )
        dense_docs = self.data_loader.search(
            keywords=[],
            vector_queries=dense_queries,
            constraints=constraints,
            top_k=top_k,
        )

        return _rrf_merge(bm25_docs, dense_docs, top_n=top_k)
