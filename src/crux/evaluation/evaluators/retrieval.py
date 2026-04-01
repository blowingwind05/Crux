"""Evaluation for the Retrieval module."""

from __future__ import annotations

import time

from src.crux.evaluation.base import BaseEvaluator, EvaluationCase, EvaluationResult
from src.crux.evaluation.fixtures import InMemoryDataLoader, extract_doc_id
from src.crux.evaluation.helpers import build_config
from src.crux.evaluation.metrics import mrr, ndcg_at_k, precision_at_k, recall_at_k
from src.crux.modules.retrieval import RetrievalNode


class RetrievalEvaluator(BaseEvaluator):
    module_name = "retrieval"

    def evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
        config = build_config(case.metadata.get("config"))
        top_k = int(case.metadata.get("k", case.expected.get("k", config.search.top_k)))
        config.search.top_k = top_k

        node = RetrievalNode(config)
        node._data_loader = InMemoryDataLoader(case.input["documents"], config)

        input_state = {
            "user_query": case.input["query"],
            "intent": case.input["intent"],
            "verified_evidence": [],
            "search_iteration": case.input.get("search_iteration", 0),
        }

        started = time.perf_counter()
        output = node.process(input_state)
        duration_ms = (time.perf_counter() - started) * 1000

        ranked_ids = [extract_doc_id(doc) for doc in output.get("candidate_docs", [])]
        relevant_ids = set(case.expected["relevant_doc_ids"])
        relevance_vector = [1 if doc_id in relevant_ids else 0 for doc_id in ranked_ids[:top_k]]

        metrics = {
            "recall_at_k": recall_at_k(relevant_ids, ranked_ids, top_k),
            "precision_at_k": precision_at_k(relevant_ids, ranked_ids, top_k),
            "mrr": mrr(relevant_ids, ranked_ids),
            "ndcg_at_k": ndcg_at_k(relevance_vector, top_k),
            "latency_ms": duration_ms,
            "retrieved_count": len(ranked_ids),
        }

        min_recall = float(case.expected.get("min_recall_at_k", 0.0))
        passed = bool(metrics["recall_at_k"] >= min_recall)

        return EvaluationResult(
            case_id=case.case_id,
            module=case.module,
            name=case.name,
            passed=passed,
            metrics=metrics,
            duration_ms=duration_ms,
            actual={"ranked_doc_ids": ranked_ids},
            expected=case.expected,
        )
