"""Batch evaluation for question-only Excel datasets using LLM-as-a-judge."""

from __future__ import annotations

import copy
import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yaml

from src.crux.config import CruxConfig, load_config
from src.crux.evaluation.base import EvaluationResult, EvaluationSummary, utc_now_iso
from src.crux.evaluation.datasets import QuestionDatasetRow, load_question_dataset
from src.crux.evaluation.helpers import clean_stage_output, dimension_scores, merge_state
from src.crux.evaluation.llm_judge import LLMEvaluationJudge
from src.crux.evaluation.report import build_markdown_report
from src.crux.evaluation.trace import TraceRecorder
from src.crux.modules import GapAnalysisNode, JudgeNode, ReportNode, RetrievalNode, UnderstandingNode


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "model"


def _resolve_env_vars(value: Any) -> Any:
    """Resolve ${ENV} and ${ENV:default} strings inside model config files."""
    if isinstance(value, str):
        pattern = r"\$\{([^}:]+)(?::([^}]*))?\}"

        def replacer(match: re.Match[str]) -> str:
            env_name = match.group(1)
            default_value = match.group(2) if match.group(2) is not None else ""
            return os.getenv(env_name, default_value)

        return re.sub(pattern, replacer, value)
    if isinstance(value, dict):
        return {key: _resolve_env_vars(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def _aggregate_numeric_metrics(results: List[EvaluationResult]) -> Dict[str, Any]:
    numeric: Dict[str, List[float]] = {}
    for result in results:
        for key, value in result.metrics.items():
            if isinstance(value, bool):
                numeric.setdefault(key, []).append(1.0 if value else 0.0)
            elif isinstance(value, (int, float)):
                numeric.setdefault(key, []).append(float(value))
    return {key: mean(values) for key, values in numeric.items()}


def _apply_config_overrides(config: CruxConfig, overrides: Dict[str, Any]) -> CruxConfig:
    nested_sections = {"search", "judge", "llm", "retriever"}

    for key, value in overrides.items():
        if key in nested_sections:
            continue
        if hasattr(config, key):
            setattr(config, key, value)

    for section in nested_sections:
        if section not in overrides:
            continue
        target = getattr(config, section)
        for key, value in overrides[section].items():
            setattr(target, key, value)

    return config


@dataclass
class ModelSpec:
    """Runtime configuration for one evaluated model or one judge model."""

    name: str
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    api_key_env: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    config_overrides: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "ModelSpec":
        llm_payload = payload.get("llm", payload)
        overrides = copy.deepcopy(payload.get("config", {}))

        for section in ("search", "judge", "retriever", "llm"):
            if section in payload and section != "llm":
                overrides[section] = copy.deepcopy(payload[section])

        for key in ("data_source_type", "data_source_path", "schema_path", "debug", "mock_llm"):
            if key in payload:
                overrides[key] = payload[key]

        return cls(
            name=payload.get("name") or llm_payload.get("model") or "default",
            model=llm_payload.get("model"),
            base_url=llm_payload.get("base_url"),
            api_key=llm_payload.get("api_key"),
            api_key_env=llm_payload.get("api_key_env"),
            temperature=llm_payload.get("temperature"),
            max_tokens=llm_payload.get("max_tokens"),
            config_overrides=overrides,
        )

    def resolve_api_key(self, fallback: Optional[str]) -> Optional[str]:
        if self.api_key is not None:
            return self.api_key
        if self.api_key_env:
            return os.getenv(self.api_key_env, fallback)
        return fallback

    def to_config(self, base_config: CruxConfig) -> CruxConfig:
        config = copy.deepcopy(base_config)
        config = _apply_config_overrides(config, copy.deepcopy(self.config_overrides))

        if self.model:
            config.llm.model = self.model
        if self.base_url:
            config.llm.base_url = self.base_url

        resolved_key = self.resolve_api_key(config.llm.api_key)
        if resolved_key is not None:
            config.llm.api_key = resolved_key

        if self.temperature is not None:
            config.llm.temperature = self.temperature
        if self.max_tokens is not None:
            config.llm.max_tokens = self.max_tokens

        return config


def load_model_specs(path: str | Path) -> Tuple[Optional[ModelSpec], List[ModelSpec]]:
    """Load judge/candidate model definitions from a JSON or YAML file."""
    config_path = Path(path)
    with open(config_path, "r", encoding="utf-8") as handle:
        if config_path.suffix.lower() in {".yaml", ".yml"}:
            payload = yaml.safe_load(handle)
        else:
            payload = json.load(handle)
    payload = _resolve_env_vars(payload)

    if isinstance(payload, list):
        return None, [ModelSpec.from_dict(item) for item in payload]

    judge_spec = ModelSpec.from_dict(payload["judge_model"]) if payload.get("judge_model") else None
    models = [ModelSpec.from_dict(item) for item in payload.get("models", [])]
    return judge_spec, models


def _json_ready(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _json_ready(value.model_dump())
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, set):
        return [_json_ready(item) for item in sorted(value, key=lambda item: str(item))]
    return value


class LivePipelineRunner:
    """Run the live Crux pipeline with trace capture."""

    def __init__(self, config: CruxConfig):
        self.config = config
        self.understanding = UnderstandingNode(config)
        self.retrieval = RetrievalNode(config)
        self.judge = JudgeNode(config)
        self.strategy = GapAnalysisNode(config)
        self.report = ReportNode(config)

    def _run_stage(
        self,
        recorder: TraceRecorder,
        stage_name: str,
        node: Any,
        state: Dict[str, Any],
        iteration: int,
    ) -> Dict[str, Any]:
        state_before = copy.deepcopy(state)
        started = time.perf_counter()
        output = node.process(state)
        duration_ms = (time.perf_counter() - started) * 1000
        state_after = merge_state(state, output)

        recorder.record_stage(
            stage=stage_name,
            iteration=iteration,
            duration_ms=duration_ms,
            input_snapshot=_json_ready(state_before),
            output_snapshot=_json_ready(clean_stage_output(output)),
            state_after=_json_ready(state_after),
            logs=_json_ready(output.get("_stage_logs", [])),
        )
        return state_after

    def run(self, case_id: str, query: str) -> Dict[str, Any]:
        recorder = TraceRecorder(case_id, query)
        started = time.perf_counter()

        state: Dict[str, Any] = {
            "user_query": query,
            "verified_evidence": [],
            "rejected_docs": [],
            "candidate_docs": [],
            "search_iteration": 0,
            "satisfied_facets": set(),
            "seen_doc_ids": set(),
            "start_time": time.time(),
        }

        state = self._run_stage(recorder, "understand", self.understanding, state, 0)

        current_iteration = int(state.get("search_iteration", 0))
        while True:
            state = self._run_stage(recorder, "retrieve", self.retrieval, state, current_iteration)
            state = self._run_stage(recorder, "judge", self.judge, state, current_iteration)
            state = self._run_stage(recorder, "analyze", self.strategy, state, current_iteration)

            if state.get("gap_analysis_result") != "insufficient":
                break

            current_iteration += 1
            if current_iteration >= self.config.search.max_iterations:
                break

        state = self._run_stage(recorder, "report", self.report, state, current_iteration)
        total_duration_ms = (time.perf_counter() - started) * 1000
        trace = recorder.finalize(total_duration_ms, _json_ready(state))

        return {
            "final_state": state,
            "trace": trace.to_dict(),
            "duration_ms": total_duration_ms,
        }


def evaluate_question_dataset(
    rows: List[QuestionDatasetRow],
    model_spec: ModelSpec,
    candidate_config: CruxConfig,
    judge_config: CruxConfig,
    pass_threshold: float = 0.75,
) -> EvaluationSummary:
    """Evaluate one model across all questions in the dataset."""
    runner = LivePipelineRunner(candidate_config)
    judge = LLMEvaluationJudge(config=judge_config)
    results: List[EvaluationResult] = []

    for row in rows:
        try:
            run_result = runner.run(row.case_id, row.question)
            final_state = run_result["final_state"]
            trace = run_result["trace"]

            condensed_trace = [
                {
                    "stage": stage["stage"],
                    "iteration": stage["iteration"],
                    "duration_ms": stage["duration_ms"],
                    "gap_analysis_result": stage.get("output_snapshot", {}).get("gap_analysis_result"),
                    "output_keys": sorted(stage.get("output_snapshot", {}).keys()),
                }
                for stage in trace.get("stage_traces", [])
            ]

            verdict = judge.evaluate(
                task_name="Question-only end-to-end Crux evaluation",
                instructions=(
                    "There is no ground truth answer. Judge whether the pipeline understood the question, "
                    "retrieved relevant evidence, produced a faithful and sufficiently complete answer, and "
                    "kept a coherent multi-stage execution path. Penalize unsupported claims, missing key "
                    "aspects, poor clarity, and obviously irrelevant evidence."
                ),
                payload={
                    "question": row.question,
                    "dataset_row": row.raw,
                    "final_report": final_state.get("final_report", ""),
                    "verified_evidence": final_state.get("verified_evidence", []),
                    "gap_analysis_details": final_state.get("gap_analysis_details", {}),
                    "condensed_trace": condensed_trace,
                },
                dimensions=[
                    "query_understanding",
                    "evidence_relevance",
                    "answer_completeness",
                    "answer_faithfulness",
                    "answer_clarity",
                    "trace_coherence",
                ],
            )

            evidence = final_state.get("verified_evidence", [])
            unique_doc_ids = {
                item.get("doc_id") or item.get("id") or item.get("arxiv_id") for item in evidence
            } - {None}
            iteration_count = len(
                [stage for stage in trace.get("stage_traces", []) if stage["stage"] == "analyze"]
            )
            metrics = {
                "total_latency_ms": run_result["duration_ms"],
                "iteration_count": iteration_count,
                "trace_stage_count": len(trace.get("stage_traces", [])),
                "evidence_count": len(evidence),
                "unique_evidence_count": len(unique_doc_ids),
                "report_present": bool(final_state.get("final_report")),
                "llm_overall_score": verdict.overall_score,
                "llm_pass_recommendation": verdict.pass_recommendation,
                **dimension_scores(verdict),
            }
            passed = bool(
                metrics["report_present"]
                and verdict.overall_score >= pass_threshold
                and verdict.pass_recommendation
            )

            results.append(
                EvaluationResult(
                    case_id=row.case_id,
                    module="question_eval",
                    name=row.question,
                    passed=passed,
                    metrics=metrics,
                    duration_ms=run_result["duration_ms"],
                    actual={
                        "question": row.question,
                        "dataset_row": row.raw,
                        "final_report": final_state.get("final_report", ""),
                        "verified_evidence": evidence,
                        "gap_analysis_details": final_state.get("gap_analysis_details", {}),
                        "llm_judgement": verdict.model_dump(),
                    },
                    expected={"evaluation_mode": "question_only_llm_judge"},
                    trace=trace,
                    notes=[verdict.summary, *verdict.issues],
                )
            )
        except Exception as exc:
            results.append(
                EvaluationResult(
                    case_id=row.case_id,
                    module="question_eval",
                    name=row.question,
                    passed=False,
                    metrics={"llm_overall_score": 0.0, "report_present": False},
                    duration_ms=0.0,
                    actual={"question": row.question, "dataset_row": row.raw},
                    expected={"evaluation_mode": "question_only_llm_judge"},
                    errors=[str(exc)],
                )
            )

    passed_cases = sum(1 for result in results if result.passed)
    aggregate_metrics = {
        "model_name": model_spec.name,
        **_aggregate_numeric_metrics(results),
    }
    return EvaluationSummary(
        module=f"question_eval_{_slugify(model_spec.name)}",
        generated_at=utc_now_iso(),
        total_cases=len(results),
        passed_cases=passed_cases,
        failed_cases=len(results) - passed_cases,
        average_duration_ms=mean([item.duration_ms for item in results]) if results else 0.0,
        aggregate_metrics=aggregate_metrics,
        case_results=results,
    )


def _write_model_reports(summary: EvaluationSummary, output_dir: str | Path, model_name: str) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    slug = _slugify(model_name)
    json_path = output_path / f"{slug}_question_eval.json"
    md_path = output_path / f"{slug}_question_eval.md"
    xlsx_path = output_path / f"{slug}_question_eval.xlsx"

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(summary.to_dict(), handle, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(build_markdown_report(summary))

    summary_rows = [
        {"metric": "model_name", "value": model_name},
        {"metric": "generated_at", "value": summary.generated_at},
        {"metric": "total_cases", "value": summary.total_cases},
        {"metric": "passed_cases", "value": summary.passed_cases},
        {"metric": "failed_cases", "value": summary.failed_cases},
        {"metric": "average_duration_ms", "value": summary.average_duration_ms},
    ]
    for key, value in summary.aggregate_metrics.items():
        summary_rows.append({"metric": key, "value": value})

    case_rows = []
    for result in summary.case_results:
        verdict = result.actual.get("llm_judgement", {})
        case_rows.append(
            {
                "case_id": result.case_id,
                "question": result.actual.get("question", result.name),
                "passed": result.passed,
                "duration_ms": result.duration_ms,
                "llm_overall_score": result.metrics.get("llm_overall_score"),
                "iteration_count": result.metrics.get("iteration_count"),
                "evidence_count": result.metrics.get("evidence_count"),
                "report_present": result.metrics.get("report_present"),
                "judge_summary": verdict.get("summary", ""),
                "final_report": result.actual.get("final_report", ""),
                "errors": "\n".join(result.errors),
            }
        )

    with pd.ExcelWriter(xlsx_path) as writer:
        pd.DataFrame(summary_rows).to_excel(writer, sheet_name="summary", index=False)
        pd.DataFrame(case_rows).to_excel(writer, sheet_name="cases", index=False)


def _write_leaderboard(
    leaderboard: List[Dict[str, Any]],
    output_dir: str | Path,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "question_eval_leaderboard.json"
    md_path = output_path / "question_eval_leaderboard.md"
    xlsx_path = output_path / "question_eval_leaderboard.xlsx"

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(leaderboard, handle, ensure_ascii=False, indent=2)

    lines = ["# Question Evaluation Leaderboard", ""]
    if leaderboard:
        lines.append("| model | avg_score | pass_rate | avg_latency_ms |")
        lines.append("| --- | ---: | ---: | ---: |")
        for item in leaderboard:
            lines.append(
                f"| {item['model_name']} | {item['avg_llm_overall_score']:.4f} | "
                f"{item['pass_rate']:.4f} | {item['avg_latency_ms']:.2f} |"
            )
    else:
        lines.append("No results.")

    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    pd.DataFrame(leaderboard).to_excel(xlsx_path, index=False)


def run_question_dataset_evaluation(
    dataset_xlsx: str | Path,
    output_dir: str | Path,
    question_column: str = "question",
    limit: Optional[int] = None,
    models_config: Optional[str | Path] = None,
    default_model: Optional[ModelSpec] = None,
    default_judge_model: Optional[ModelSpec] = None,
    pass_threshold: float = 0.75,
) -> List[Dict[str, Any]]:
    """Evaluate one or more candidate models on an Excel question dataset."""
    rows = load_question_dataset(dataset_xlsx, question_column=question_column, limit=limit)
    if not rows:
        raise ValueError("No valid questions found in the dataset.")

    base_config = load_config()

    file_judge_spec: Optional[ModelSpec] = None
    model_specs: List[ModelSpec] = []
    if models_config:
        file_judge_spec, model_specs = load_model_specs(models_config)
    elif default_model is not None:
        model_specs = [default_model]
    else:
        model_specs = [ModelSpec(name=base_config.llm.model, model=base_config.llm.model)]

    if not model_specs:
        raise ValueError("No candidate models were configured for evaluation.")

    judge_spec = default_judge_model or file_judge_spec
    judge_config = judge_spec.to_config(base_config) if judge_spec else copy.deepcopy(base_config)

    leaderboard: List[Dict[str, Any]] = []
    for model_spec in model_specs:
        candidate_config = model_spec.to_config(base_config)
        summary = evaluate_question_dataset(
            rows=rows,
            model_spec=model_spec,
            candidate_config=candidate_config,
            judge_config=judge_config,
            pass_threshold=pass_threshold,
        )
        _write_model_reports(summary, output_dir, model_spec.name)
        leaderboard.append(
            {
                "model_name": model_spec.name,
                "model": candidate_config.llm.model,
                "base_url": candidate_config.llm.base_url,
                "cases": summary.total_cases,
                "passed_cases": summary.passed_cases,
                "failed_cases": summary.failed_cases,
                "pass_rate": summary.passed_cases / max(summary.total_cases, 1),
                "avg_llm_overall_score": float(summary.aggregate_metrics.get("llm_overall_score", 0.0)),
                "avg_latency_ms": summary.average_duration_ms,
                "avg_iteration_count": float(summary.aggregate_metrics.get("iteration_count", 0.0)),
                "avg_evidence_count": float(summary.aggregate_metrics.get("evidence_count", 0.0)),
            }
        )

    leaderboard.sort(key=lambda item: item["avg_llm_overall_score"], reverse=True)
    _write_leaderboard(leaderboard, output_dir)
    return leaderboard
