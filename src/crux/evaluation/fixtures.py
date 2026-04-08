"""Local fixtures and stubs used by evaluation runs."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from src.crux.data.loaders.base import BaseDataLoader, apply_constraints


def extract_doc_id(doc: Dict[str, Any]) -> str:
    """Extract a stable document id from a paper-like record."""
    return str(doc.get("id") or doc.get("doc_id") or doc.get("arxiv_id") or "unknown")


class InMemoryDataLoader(BaseDataLoader):
    """Simple in-memory loader used by retrieval and pipeline evaluation."""

    def __init__(self, docs: List[Dict[str, Any]], config=None):
        super().__init__(config)
        self._data = copy.deepcopy(docs)

    def load(self) -> List[Dict[str, Any]]:
        return self._data or []

    def search(
        self,
        keywords: List[str],
        vector_queries: List[str],
        constraints: Dict[str, Any],
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        docs = apply_constraints(self.load(), constraints)
        search_terms = [term.lower() for term in keywords + vector_queries if term]

        scored: List[tuple[float, Dict[str, Any]]] = []
        for doc in docs:
            score = 0.0
            title = str(doc.get("title", "")).lower()
            abstract = str(doc.get("abstract", "")).lower()
            content = str(doc.get("content", "")).lower()
            corpus = " ".join([title, abstract, content])

            for term in search_terms:
                if term in corpus:
                    score += 1.0
                if term in title:
                    score += 1.5

            if not search_terms:
                score = float(doc.get("score", 0.0))

            if score > 0 or doc.get("score") is not None:
                hydrated = copy.deepcopy(doc)
                hydrated["score"] = float(hydrated.get("score", score))
                scored.append((hydrated["score"], hydrated))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]


class StubLLMClient:
    """Deterministic LLM stub for module and pipeline evaluation."""

    def __init__(
        self,
        call_json: Optional[List[Dict[str, Any]]] = None,
        call_json_with_object: Optional[List[Dict[str, Any]]] = None,
        batch_call_json: Optional[List[List[Dict[str, Any]]]] = None,
    ):
        self._call_json = list(call_json or [])
        self._call_json_with_object = list(call_json_with_object or [])
        self._batch_call_json = list(batch_call_json or [])

    def _next(self, queue: List[Any], method_name: str) -> Any:
        if not queue:
            raise ValueError(f"No stub response configured for {method_name}")
        return copy.deepcopy(queue.pop(0))

    def call_json(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        return self._next(self._call_json, "call_json")

    def call_json_with_object(self, prompt: str, model: Optional[str] = None, response_object=None):
        payload = self._next(self._call_json_with_object, "call_json_with_object")
        if response_object is not None:
            return response_object.model_validate(payload)
        return payload

    def batch_call_json(
        self,
        prompts: List[str],
        model: Optional[str] = None,
        max_retry: int = 5,
        max_workers: int = 4,
    ) -> List[Dict[str, Any]]:
        batch = self._next(self._batch_call_json, "batch_call_json")
        if len(batch) != len(prompts):
            raise ValueError(
                f"Stub batch size mismatch: expected {len(prompts)} responses, got {len(batch)}"
            )
        return batch
