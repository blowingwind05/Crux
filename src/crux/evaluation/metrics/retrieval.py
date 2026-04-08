"""Ranking metrics for retrieval evaluation."""

from __future__ import annotations

import math
from typing import Sequence, Set


def recall_at_k(relevant_ids: Set[str], ranked_ids: Sequence[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    return len(relevant_ids & set(ranked_ids[:k])) / len(relevant_ids)


def precision_at_k(relevant_ids: Set[str], ranked_ids: Sequence[str], k: int) -> float:
    if k <= 0:
        return 0.0
    window = ranked_ids[:k]
    return len(relevant_ids & set(window)) / max(len(window), 1)


def mrr(relevant_ids: Set[str], ranked_ids: Sequence[str]) -> float:
    for index, doc_id in enumerate(ranked_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / index
    return 0.0


def ndcg_at_k(relevance: Sequence[int], k: int) -> float:
    clipped = list(relevance[:k])
    if not clipped:
        return 0.0

    dcg = sum((2 ** rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(clipped))
    ideal = sorted(clipped, reverse=True)
    idcg = sum((2 ** rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(ideal))
    return dcg / idcg if idcg else 0.0
