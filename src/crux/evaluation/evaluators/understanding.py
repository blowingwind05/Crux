"""Evaluation for the Understanding module."""

from __future__ import annotations

import time
from typing import Any, Dict

from src.crux.evaluation.base import BaseEvaluator, EvaluationCase, EvaluationResult
from src.crux.evaluation.fixtures import StubLLMClient
from src.crux.evaluation.helpers import (
    allowed_constraint_fields,
    build_config,
    build_evaluation_judge,
    constraint_set,
    dense_query_set,
    dimension_scores,
    sparse_keyword_set,
)
from src.crux.evaluation.metrics import set_match_metrics
from src.crux.modules.understanding import UnderstandingNode


class UnderstandingEvaluator(BaseEvaluator):
    module_name = "understanding"

    def evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
        config = build_config(case.metadata.get("config"))
        node = UnderstandingNode(config)
        node.llm_client = StubLLMClient(call_json_with_object=[case.stubs["intent_response"]])
        judge = build_evaluation_judge(config, case.stubs, "understanding_evaluator_judgement")

        input_state = {
            "user_query": case.input["query"],
            "verified_evidence": [],
            "search_iteration": 0,
            "start_time": time.time(),
        }

        started = time.perf_counter()
        output = node.process(input_state)
        duration_ms = (time.perf_counter() - started) * 1000

        actual_intent = output["intent"]
        expected_intent = case.expected["intent"]

        expected_constraints = constraint_set(
            expected_intent.get("constraints", {}).get("structured_metadata", [])
        )
        actual_constraints = constraint_set(
            actual_intent.get("constraints", {}).get("structured_metadata", [])
        )
        constraint_precision, constraint_recall, constraint_f1, constraints_exact = set_match_metrics(
            expected_constraints, actual_constraints
        )

        expected_sparse = sparse_keyword_set(expected_intent)
        actual_sparse = sparse_keyword_set(actual_intent)
        sparse_precision, sparse_recall, sparse_f1, _ = set_match_metrics(expected_sparse, actual_sparse)

        expected_dense = dense_query_set(expected_intent)
        actual_dense = dense_query_set(actual_intent)
        dense_precision, dense_recall, dense_f1, _ = set_match_metrics(expected_dense, actual_dense)

        allowed_fields = allowed_constraint_fields(config, case.metadata.get("allowed_constraint_fields"))
        invalid_fields = sorted(
            {
                item.get("field")
                for item in actual_intent.get("constraints", {}).get("structured_metadata", [])
                if item.get("field") not in allowed_fields
            }
        )

        actual_goal = actual_intent.get("cognitive_strategy", {}).get("user_goal")
        expected_goal = expected_intent.get("cognitive_strategy", {}).get("user_goal")
        intent_accuracy = 1.0 if actual_goal == expected_goal else 0.0

        verdict = judge.evaluate(
            task_name="Understanding module evaluation",
            instructions=(
                "Assess whether the produced intent object correctly captures the user's goal, "
                "constraints, retrieval plan, and judgement rubric. "
                "Treat semantically equivalent wording as correct. "
                "Penalize schema-invalid constraint fields heavily."
            ),
            payload={
                "query": case.input["query"],
                "allowed_constraint_fields": sorted(allowed_fields),
                "expected_intent": expected_intent,
                "actual_intent": actual_intent,
                "invalid_constraint_fields": invalid_fields,
            },
            dimensions=[
                "intent_alignment",
                "constraint_semantics",
                "retrieval_plan_quality",
                "rubric_quality",
            ],
        )

        metrics = {
            "intent_accuracy": intent_accuracy,
            "constraint_precision": constraint_precision,
            "constraint_recall": constraint_recall,
            "constraint_f1": constraint_f1,
            "constraint_exact_match": constraints_exact,
            "sparse_keyword_precision": sparse_precision,
            "sparse_keyword_recall": sparse_recall,
            "sparse_keyword_f1": sparse_f1,
            "dense_query_precision": dense_precision,
            "dense_query_recall": dense_recall,
            "dense_query_f1": dense_f1,
            "invalid_constraint_field_count": len(invalid_fields),
            "llm_overall_score": verdict.overall_score,
            "llm_pass_recommendation": verdict.pass_recommendation,
            "latency_ms": duration_ms,
            **dimension_scores(verdict),
        }

        min_llm_score = float(case.expected.get("min_llm_overall_score", 0.75))
        passed = bool(
            verdict.overall_score >= min_llm_score
            and verdict.pass_recommendation
            and not invalid_fields
        )

        return EvaluationResult(
            case_id=case.case_id,
            module=case.module,
            name=case.name,
            passed=passed,
            metrics=metrics,
            duration_ms=duration_ms,
            actual={
                "intent": actual_intent,
                "invalid_constraint_fields": invalid_fields,
                "llm_judgement": verdict.model_dump(),
            },
            expected=case.expected,
            notes=[verdict.summary, *verdict.issues],
        )
