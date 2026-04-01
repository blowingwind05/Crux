"""Evaluation for the Strategy module."""

from __future__ import annotations

import time

from src.crux.evaluation.base import BaseEvaluator, EvaluationCase, EvaluationResult
from src.crux.evaluation.fixtures import StubLLMClient
from src.crux.evaluation.helpers import build_config, build_evaluation_judge, dimension_scores
from src.crux.evaluation.metrics import set_match_metrics
from src.crux.modules.strategy import GapAnalysisNode


class StrategyEvaluator(BaseEvaluator):
    module_name = "strategy"

    def evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
        config = build_config(case.metadata.get("config"))
        node = GapAnalysisNode(config)
        node.llm_client = StubLLMClient(call_json=[case.stubs["gap_response"]])
        judge = build_evaluation_judge(config, case.stubs, "strategy_evaluator_judgement")

        input_state = {
            "user_query": case.input["query"],
            "intent": case.input.get("intent", {}),
            "verified_evidence": case.input.get("verified_evidence", []),
            "search_iteration": case.input.get("search_iteration", 0),
        }

        started = time.perf_counter()
        output = node.process(input_state)
        duration_ms = (time.perf_counter() - started) * 1000

        actual_status = output.get("gap_analysis_result")
        expected_status = case.expected["status"]
        status_accuracy = 1.0 if actual_status == expected_status else 0.0

        actual_missing = set(output.get("gap_analysis_details", {}).get("missing_info", []))
        expected_missing = set(case.expected.get("missing_info", []))
        missing_precision, missing_recall, missing_f1, _ = set_match_metrics(expected_missing, actual_missing)

        actual_coverage = float(output.get("gap_analysis_details", {}).get("coverage_score", 0.0))
        expected_coverage = float(case.expected.get("coverage_score", actual_coverage))

        verdict = judge.evaluate(
            task_name="Strategy module evaluation",
            instructions=(
                "Assess whether the gap analysis made a semantically sound sufficiency decision, "
                "identified the right missing information, and proposed reasonable follow-up queries."
            ),
            payload={
                "query": case.input["query"],
                "intent": case.input.get("intent", {}),
                "expected": case.expected,
                "actual": output,
            },
            dimensions=[
                "gap_decision_quality",
                "missing_info_quality",
                "suggested_query_quality",
                "coverage_assessment_quality",
            ],
        )

        metrics = {
            "gap_detection_accuracy": status_accuracy,
            "missing_precision": missing_precision,
            "missing_recall": missing_recall,
            "missing_f1": missing_f1,
            "coverage_score": actual_coverage,
            "coverage_error": abs(actual_coverage - expected_coverage),
            "llm_overall_score": verdict.overall_score,
            "llm_pass_recommendation": verdict.pass_recommendation,
            "latency_ms": duration_ms,
            **dimension_scores(verdict),
        }

        min_llm_score = float(case.expected.get("min_llm_overall_score", 0.75))
        passed = bool(
            status_accuracy == 1.0
            and verdict.overall_score >= min_llm_score
            and verdict.pass_recommendation
        )

        return EvaluationResult(
            case_id=case.case_id,
            module=case.module,
            name=case.name,
            passed=passed,
            metrics=metrics,
            duration_ms=duration_ms,
            actual={**output, "llm_judgement": verdict.model_dump()},
            expected=case.expected,
            notes=[verdict.summary, *verdict.issues],
        )
