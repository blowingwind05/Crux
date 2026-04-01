"""End-to-end pipeline evaluation with full execution trace capture."""

from __future__ import annotations

import copy
import time
from typing import Dict, List

from src.crux.evaluation.base import BaseEvaluator, EvaluationCase, EvaluationResult
from src.crux.evaluation.fixtures import InMemoryDataLoader, StubLLMClient, extract_doc_id
from src.crux.evaluation.helpers import build_config, clean_stage_output, merge_state
from src.crux.evaluation.metrics import recall_at_k
from src.crux.evaluation.trace import TraceRecorder
from src.crux.modules.adjudication import AdjudicationNode
from src.crux.modules.retrieval import RetrievalNode
from src.crux.modules.strategy import GapAnalysisNode, ReportNode
from src.crux.modules.understanding import UnderstandingNode


class TraceablePipelineRunner:
    """Run the Crux module chain while collecting stage-level trace artifacts."""

    def __init__(self, case: EvaluationCase):
        self.case = case
        self.config = build_config(case.metadata.get("config"))
        self.config.search.max_iterations = int(
            case.metadata.get("max_iterations", self.config.search.max_iterations)
        )

        self.understanding = UnderstandingNode(self.config)
        self.retrieval = RetrievalNode(self.config)
        self.adjudication = AdjudicationNode(self.config)
        self.strategy = GapAnalysisNode(self.config)
        self.report = ReportNode(self.config)

        self.understanding.llm_client = StubLLMClient(
            call_json_with_object=[case.stubs["intent_response"]]
        )
        self.retrieval._data_loader = InMemoryDataLoader(case.input["documents"], self.config)
        self.adjudication_batches = list(case.stubs["judgement_batches"])
        self.strategy_responses = list(case.stubs["gap_responses"])

    def _run_stage(
        self,
        recorder: TraceRecorder,
        stage_name: str,
        node,
        state: Dict,
        iteration: int,
    ) -> Dict:
        state_before = copy.deepcopy(state)
        started = time.perf_counter()
        output = node.process(state)
        duration_ms = (time.perf_counter() - started) * 1000
        state_after = merge_state(state, output)

        recorder.record_stage(
            stage=stage_name,
            iteration=iteration,
            duration_ms=duration_ms,
            input_snapshot=state_before,
            output_snapshot=clean_stage_output(output),
            state_after=state_after,
            logs=output.get("_stage_logs", []),
        )
        return state_after

    def run(self) -> Dict:
        query = self.case.input["query"]
        recorder = TraceRecorder(self.case.case_id, query)
        started = time.perf_counter()

        state: Dict = {
            "user_query": query,
            "verified_evidence": [],
            "rejected_docs": [],
            "candidate_docs": [],
            "search_iteration": 0,
            "start_time": time.time(),
        }

        state = self._run_stage(recorder, "understand", self.understanding, state, 0)

        current_iteration = 0
        while True:
            state = self._run_stage(recorder, "retrieve", self.retrieval, state, current_iteration)

            self.adjudication.llm_client = StubLLMClient(
                batch_call_json=[self.adjudication_batches.pop(0)]
            )
            state = self._run_stage(recorder, "judge", self.adjudication, state, current_iteration)

            self.strategy.llm_client = StubLLMClient(call_json=[self.strategy_responses.pop(0)])
            state = self._run_stage(recorder, "analyze", self.strategy, state, current_iteration)

            if state.get("gap_analysis_result") != "insufficient":
                break

            current_iteration += 1
            if current_iteration >= self.config.search.max_iterations:
                break

        state = self._run_stage(recorder, "report", self.report, state, current_iteration)
        trace = recorder.finalize((time.perf_counter() - started) * 1000, state)

        return {
            "final_state": state,
            "trace": trace.to_dict(),
        }


class PipelineEvaluator(BaseEvaluator):
    module_name = "pipeline"

    def evaluate_case(self, case: EvaluationCase) -> EvaluationResult:
        started = time.perf_counter()
        runner = TraceablePipelineRunner(case)
        run_result = runner.run()
        duration_ms = (time.perf_counter() - started) * 1000

        final_state = run_result["final_state"]
        trace = run_result["trace"]
        final_doc_ids = {
            extract_doc_id(item) for item in final_state.get("verified_evidence", [])
        }
        expected_doc_ids = set(case.expected.get("final_evidence_doc_ids", []))
        expected_statuses = case.expected.get("gap_statuses", [])
        actual_statuses = [
            stage["output_snapshot"].get("gap_analysis_result")
            for stage in trace["stage_traces"]
            if stage["stage"] == "analyze"
        ]

        metrics = {
            "total_latency_ms": duration_ms,
            "iteration_count": len(actual_statuses),
            "trace_stage_count": len(trace["stage_traces"]),
            "trace_completeness": self._trace_completeness(trace["stage_traces"]),
            "final_evidence_recall": recall_at_k(
                expected_doc_ids, list(final_doc_ids), max(len(expected_doc_ids), 1)
            ),
            "report_present": bool(final_state.get("final_report")),
            "gap_path_accuracy": 1.0 if actual_statuses == expected_statuses else 0.0,
        }

        passed = bool(metrics["report_present"] and metrics["gap_path_accuracy"] == 1.0)

        return EvaluationResult(
            case_id=case.case_id,
            module=case.module,
            name=case.name,
            passed=passed,
            metrics=metrics,
            duration_ms=duration_ms,
            actual={
                "final_gap_statuses": actual_statuses,
                "final_evidence_doc_ids": sorted(final_doc_ids),
            },
            expected=case.expected,
            trace=trace,
        )

    def _trace_completeness(self, stage_traces: List[Dict]) -> float:
        if not stage_traces:
            return 0.0

        complete = 0
        for stage in stage_traces:
            if stage.get("input_snapshot") and stage.get("output_snapshot") and "duration_ms" in stage:
                complete += 1
        return complete / len(stage_traces)
