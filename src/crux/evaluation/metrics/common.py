"""Generic metrics shared across module evaluators."""

from __future__ import annotations

import re
from statistics import mean
from typing import Iterable, Sequence, Set


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def average(values: Iterable[float]) -> float:
    values = list(values)
    return mean(values) if values else 0.0


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def binary_accuracy(expected: Sequence[bool], actual: Sequence[bool]) -> float:
    if not expected:
        return 0.0
    correct = sum(1 for left, right in zip(expected, actual) if left == right)
    return correct / len(expected)


def set_match_metrics(expected: Set[str], actual: Set[str]) -> tuple[float, float, float, bool]:
    tp = len(expected & actual)
    fp = len(actual - expected)
    fn = len(expected - actual)
    precision, recall, f1 = precision_recall_f1(tp, fp, fn)
    return precision, recall, f1, expected == actual


def _normalize_tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def text_overlap_f1(expected_text: str, actual_text: str) -> float:
    expected_tokens = set(_normalize_tokens(expected_text))
    actual_tokens = set(_normalize_tokens(actual_text))
    if not expected_tokens and not actual_tokens:
        return 1.0
    _, _, f1, _ = set_match_metrics(expected_tokens, actual_tokens)
    return f1
