"""Execution trace capture for pipeline evaluation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import copy


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class StageTrace:
    stage: str
    iteration: int
    started_at: str
    ended_at: str
    duration_ms: float
    input_snapshot: Dict[str, Any]
    output_snapshot: Dict[str, Any]
    state_after: Dict[str, Any]
    logs: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


@dataclass
class PipelineTrace:
    case_id: str
    query: str
    started_at: str = field(default_factory=_now)
    ended_at: Optional[str] = None
    total_duration_ms: float = 0.0
    stage_traces: List[StageTrace] = field(default_factory=list)
    final_state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TraceRecorder:
    """Collect per-stage execution details for the full pipeline."""

    def __init__(self, case_id: str, query: str):
        self._trace = PipelineTrace(case_id=case_id, query=query)

    def record_stage(
        self,
        stage: str,
        iteration: int,
        duration_ms: float,
        input_snapshot: Dict[str, Any],
        output_snapshot: Dict[str, Any],
        state_after: Dict[str, Any],
        logs: Optional[List[Dict[str, Any]]] = None,
        error: Optional[str] = None,
    ) -> None:
        trace = StageTrace(
            stage=stage,
            iteration=iteration,
            started_at=_now(),
            ended_at=_now(),
            duration_ms=duration_ms,
            input_snapshot=copy.deepcopy(input_snapshot),
            output_snapshot=copy.deepcopy(output_snapshot),
            state_after=copy.deepcopy(state_after),
            logs=copy.deepcopy(logs or []),
            error=error,
        )
        self._trace.stage_traces.append(trace)

    def finalize(self, total_duration_ms: float, final_state: Dict[str, Any]) -> PipelineTrace:
        self._trace.ended_at = _now()
        self._trace.total_duration_ms = total_duration_ms
        self._trace.final_state = copy.deepcopy(final_state)
        return self._trace
