"""Evaluation for the Adjudication module."""

from __future__ import annotations

import time

from src.crux.evaluation.base import BaseEvaluator, EvaluationCase, EvaluationResult
from src.crux.evaluation.fixtures import StubLLMClient, extract_doc_id
from src.crux.evaluation.helpers import build_config, build_evaluation_judge, dimension_scores
from src.crux.evaluation.metrics import precision_recall_f1, text_overlap_f1
from src.crux.modules.adjudication import AdjudicationNode


class AdjudicationEvaluator(BaseEvaluator):
    module_name = "adjudication"

    def evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
        config = build_config(case.metadata.get("config"))
        config.judge.use_parallel = True
        judge = build_evaluation_judge(config, case.stubs, "adjudication_evaluator_judgement")

        node = AdjudicationNode(config)
        node.llm_client = StubLLMClient(batch_call_json=[case.stubs["judgement_batch"]])

        input_state = {
            "user_query": case.input["query"],
            "intent": case.input["intent"],
            "candidate_docs": case.input["candidate_docs"],
            "verified_evidence": [],
            "search_iteration": case.input.get("search_iteration", 0),
        }

        started = time.perf_counter()
        output = node.process(input_state)
        duration_ms = (time.perf_counter() - started) * 1000

        actual_positive = {extract_doc_id(item) for item in output.get("verified_evidence", [])}
        expected_positive = set(case.expected["relevant_doc_ids"])

        tp = len(actual_positive & expected_positive)
        fp = len(actual_positive - expected_positive)
        fn = len(expected_positive - actual_positive)
        tn = len(case.input["candidate_docs"]) - tp - fp - fn

        precision, recall, f1 = precision_recall_f1(tp, fp, fn)
        relevance_accuracy = (tp + tn) / max(len(case.input["candidate_docs"]), 1)

        gold_evidence = case.expected.get("evidence_by_doc", {})
        predicted_evidence = {
            extract_doc_id(item): str(item.get("content", ""))
            for item in output.get("verified_evidence", [])
        }
        evidence_scores = [
            text_overlap_f1(gold_evidence[doc_id], predicted_evidence.get(doc_id, ""))
            for doc_id in expected_positive
            if doc_id in gold_evidence
        ]
        evidence_quality = sum(evidence_scores) / len(evidence_scores) if evidence_scores else 0.0

        verdict = judge.evaluate(
            task_name="Adjudication module evaluation",
            instructions=(
                "Assess whether the module made semantically sound accept/reject decisions and extracted "
                "useful evidence. Treat paraphrased evidence as valid if it preserves meaning."
            ),
            payload={
                "query": case.input["query"],
                "rubric": case.input["intent"],
                "candidate_docs": case.input["candidate_docs"],
                "expected": case.expected,
                "actual_verified_evidence": output.get("verified_evidence", []),
                "actual_rejected_docs": output.get("rejected_docs", []),
            },
            dimensions=[
                "relevance_decision_quality",
                "evidence_quality",
                "rejection_quality",
                "rubric_alignment",
            ],
        )

        metrics = {
            "relevance_accuracy": relevance_accuracy,
            "relevance_precision": precision,
            "relevance_recall": recall,
            "relevance_f1": f1,
            "evidence_quality": evidence_quality,
            "acceptance_rate": len(actual_positive) / max(len(case.input["candidate_docs"]), 1),
            "llm_overall_score": verdict.overall_score,
            "llm_pass_recommendation": verdict.pass_recommendation,
            "latency_ms": duration_ms,
            **dimension_scores(verdict),
        }

        min_llm_score = float(case.expected.get("min_llm_overall_score", 0.75))
        passed = bool(
            verdict.overall_score >= min_llm_score
            and verdict.pass_recommendation
            and relevance_accuracy >= float(case.expected.get("min_relevance_accuracy", 0.0))
        )

        return EvaluationResult(
            case_id=case.case_id,
            module=case.module,
            name=case.name,
            passed=passed,
            metrics=metrics,
            duration_ms=duration_ms,
            actual={
                "accepted_doc_ids": sorted(actual_positive),
                "rejected_doc_ids": [item.get("doc_id") for item in output.get("rejected_docs", [])],
                "llm_judgement": verdict.model_dump(),
            },
            expected=case.expected,
            notes=[verdict.summary, *verdict.issues],
        )
