"""Shared abstractions for module and pipeline evaluation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional


def utc_now_iso() -> str:
    """Return a stable UTC timestamp for reports."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EvaluationCase:
    """A single evaluation case loaded from JSON fixtures."""

    case_id: str
    module: str
    name: str
    input: Dict[str, Any]
    expected: Dict[str, Any]
    stubs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Result for a single evaluation case."""

    case_id: str
    module: str
    name: str
    passed: bool
    metrics: Dict[str, Any]
    duration_ms: float
    actual: Dict[str, Any] = field(default_factory=dict)
    expected: Dict[str, Any] = field(default_factory=dict)
    trace: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "case_id": self.case_id,
            "module": self.module,
            "name": self.name,
            "passed": self.passed,
            "metrics": self.metrics,
            "duration_ms": self.duration_ms,
            "actual": self.actual,
            "expected": self.expected,
            "trace": self.trace,
            "errors": self.errors,
            "notes": self.notes,
        }


@dataclass
class EvaluationSummary:
    """Aggregated report for one evaluator run."""

    module: str
    generated_at: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    average_duration_ms: float
    aggregate_metrics: Dict[str, Any]
    case_results: List[EvaluationResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module,
            "generated_at": self.generated_at,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "average_duration_ms": self.average_duration_ms,
            "aggregate_metrics": self.aggregate_metrics,
            "case_results": [result.to_dict() for result in self.case_results],
        }


class BaseEvaluator(ABC):
    """Base class for all module and pipeline evaluators."""

    module_name: str = "base"

    def run(self, cases: Iterable[EvaluationCase]) -> EvaluationSummary:
        results: List[EvaluationResult] = []

        for case in cases:
            if case.module != self.module_name:
                continue

            try:
                result = self.evaluate_case(case)
            except Exception as exc:  # pragma: no cover - defensive aggregation
                result = EvaluationResult(
                    case_id=case.case_id,
                    module=case.module,
                    name=case.name,
                    passed=False,
                    metrics={},
                    duration_ms=0.0,
                    actual={},
                    expected=case.expected,
                    errors=[str(exc)],
                )
            results.append(result)

        passed_cases = sum(1 for result in results if result.passed)
        failed_cases = len(results) - passed_cases
        average_duration_ms = mean([result.duration_ms for result in results]) if results else 0.0

        return EvaluationSummary(
            module=self.module_name,
            generated_at=utc_now_iso(),
            total_cases=len(results),
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            average_duration_ms=average_duration_ms,
            aggregate_metrics=self.aggregate_metrics(results),
            case_results=results,
        )

    def aggregate_metrics(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        numeric: Dict[str, List[float]] = {}

        for result in results:
            for key, value in result.metrics.items():
                if isinstance(value, bool):
                    numeric.setdefault(key, []).append(1.0 if value else 0.0)
                elif isinstance(value, (int, float)):
                    numeric.setdefault(key, []).append(float(value))

        return {key: mean(values) for key, values in numeric.items()}

    @abstractmethod
    def evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
        """Evaluate a single case."""
