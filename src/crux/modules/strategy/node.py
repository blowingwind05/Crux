"""Strategy nodes for gap analysis and final report generation."""

from __future__ import annotations

import copy
import datetime
import time
from collections import defaultdict
from typing import Any, Dict, List, Set

from src.crux.modules.strategy.prompts import build_sufficiency_prompt
from src.crux.state.retrieval import FacetSufficiencyResult
from src.crux.utils.base import BaseNode
from src.crux.utils.llm_client import LLMClient


def _build_facets_evidence_block(
    pending_facets: List[Dict[str, Any]],
    verified_evidence: List[Dict[str, Any]],
) -> str:
    """Format pending facets and collected evidence for the sufficiency prompt."""
    evidence_by_facet: Dict[str, List[Dict[str, Any]]] = {}
    for item in verified_evidence:
        evidence_by_facet.setdefault(item.get("facet_id", "unknown"), []).append(item)

    lines: List[str] = []
    for facet in pending_facets:
        facet_id = facet["facet_id"]
        lines.append(f"### Facet {facet_id}: {facet.get('description', '')}")
        docs = evidence_by_facet.get(facet_id, [])
        if not docs:
            lines.append("  (no evidence collected yet)")
            continue
        for doc in docs:
            lines.append(f"  - [{doc.get('relevance_level', '?')}] {doc.get('summary', '')}")
    return "\n".join(lines)


class GapAnalysisNode(BaseNode):
    """Decide whether the current evidence is sufficient or another round is needed."""

    name = "analyze"
    name_cn = "充分性研判"
    description = "Assess per-facet sufficiency and decide whether to continue retrieval"

    def __init__(self, config=None):
        super().__init__(config)
        self.llm_client = LLMClient(config)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.reset_logger()

        iteration = state.get("search_iteration", 0) + 1
        max_iterations = self.config.search.max_iterations

        intent = state["intent"]
        criteria: Dict[str, Any] = intent["agent_plan"]["criteria"]
        facets_raw: List[Dict[str, Any]] = intent["agent_plan"]["facets"]
        expansions: List[Dict[str, Any]] = intent.get("expansions", [])
        satisfied_so_far: Set[str] = set(state.get("satisfied_facets", set()))

        self.log(f"迭代 {iteration}/{max_iterations}，已满足 Facet: {sorted(satisfied_so_far)}")

        pending_facets = [facet for facet in facets_raw if facet["facet_id"] not in satisfied_so_far]
        if not pending_facets:
            analysis = {
                "overall_sufficient": True,
                "newly_satisfied_facets": [],
                "remaining_facets": [],
                "suggested_queries": [],
            }
            return self.build_result(
                {
                    "gap_analysis_result": "sufficient",
                    "search_iteration": iteration,
                    "satisfied_facets": satisfied_so_far,
                    "gap_analysis_details": {
                        "coverage_score": 1.0,
                        "missing_info": [],
                        "suggested_queries": [],
                        "raw_analysis": analysis,
                    },
                }
            )

        self.log(f"待评估 Facet: {[facet['facet_id'] for facet in pending_facets]}")

        facets_evidence_block = _build_facets_evidence_block(
            pending_facets,
            state.get("verified_evidence", []),
        )
        prompt = build_sufficiency_prompt(criteria, facets_evidence_block)

        self.log("调用 LLM 进行 Per-Facet 充分性评估...")
        result: FacetSufficiencyResult = self.llm_client.call_object(prompt, FacetSufficiencyResult)

        newly_satisfied = {item.facet_id for item in result.facets if item.satisfied}
        combined_satisfied = satisfied_so_far | newly_satisfied
        remaining_items = [item for item in result.facets if not item.satisfied]
        remaining_ids = {item.facet_id for item in remaining_items}

        facet_by_id = {facet["facet_id"]: facet for facet in facets_raw}
        missing_info = [
            facet_by_id[item.facet_id].get("description", item.facet_id)
            for item in remaining_items
            if item.facet_id in facet_by_id
        ]
        suggested_queries = [
            expansion.get("facet_query", "")
            for expansion in expansions
            if expansion.get("facet_id") in remaining_ids and expansion.get("facet_query")
        ]

        coverage_score = len(combined_satisfied) / max(len(facets_raw), 1)
        analysis = {
            "overall_sufficient": result.overall_sufficient and not remaining_items,
            "newly_satisfied_facets": sorted(newly_satisfied),
            "remaining_facets": [
                {
                    "facet_id": item.facet_id,
                    "reason": item.reason,
                }
                for item in remaining_items
            ],
            "suggested_queries": suggested_queries,
        }

        for item in result.facets:
            status = "OK" if item.satisfied else "MISS"
            self.log(f"[{status}] Facet {item.facet_id}: {item.reason}")

        if not remaining_items or iteration >= max_iterations:
            if remaining_items:
                self.log(f"达到最大迭代次数 ({max_iterations})，结束检索", level="INFO")
            else:
                self.log("所有 Facet 充足，进入报告生成", level="INFO")
            return self.build_result(
                {
                    "gap_analysis_result": "sufficient",
                    "search_iteration": iteration,
                    "satisfied_facets": combined_satisfied,
                    "gap_analysis_details": {
                        "coverage_score": coverage_score,
                        "missing_info": missing_info,
                        "suggested_queries": suggested_queries,
                        "raw_analysis": analysis,
                    },
                }
            )

        next_intent = copy.deepcopy(intent)
        next_intent["expansions"] = [
            expansion
            for expansion in expansions
            if expansion.get("facet_id") in remaining_ids
        ]

        self.log("仍有未满足 Facet，继续下一轮检索", level="INFO")
        return self.build_result(
            {
                "intent": next_intent,
                "gap_analysis_result": "insufficient",
                "search_iteration": iteration,
                "satisfied_facets": combined_satisfied,
                "gap_analysis_details": {
                    "coverage_score": coverage_score,
                    "missing_info": missing_info,
                    "suggested_queries": suggested_queries,
                    "raw_analysis": analysis,
                },
            }
        )


class ReportNode(BaseNode):
    """Generate the final textual report from verified evidence."""

    name = "report"
    name_cn = "报告生成"
    description = "Generate the final analysis report"

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.reset_logger()

        evidence = state.get("verified_evidence", [])
        query = state["user_query"]
        iterations = state.get("search_iteration", 0)
        satisfied_facets = set(state.get("satisfied_facets", set()))

        self.log(f"原始查询: {query}")
        self.log(f"总迭代次数: {iterations}，满足 Facet: {sorted(satisfied_facets)}")
        self.log(f"可用证据: {len(evidence)} 条")

        start_time = time.time()
        report = self._generate_report(query, evidence, iterations, satisfied_facets)
        generation_ms = (time.time() - start_time) * 1000

        self.log(f"报告生成完成 (耗时: {generation_ms:.0f}ms)")
        self.log(f"报告置信度: {self._calculate_confidence(evidence, iterations):.1%}")

        return self.build_result({"final_report": report})

    def _generate_report(
        self,
        query: str,
        evidence: List[Dict[str, Any]],
        iterations: int,
        satisfied_facets: Set[str],
    ) -> str:
        lines = [
            "=" * 60,
            "[REPORT] Crux AgenticRAG Analysis Report",
            "=" * 60,
            "",
            f"[Query]      {query}",
            f"[Iterations] {iterations}",
            f"[Evidence]   {len(evidence)} docs",
            f"[Facets]     {', '.join(sorted(satisfied_facets)) if satisfied_facets else 'N/A'}",
            "",
        ]

        evidence_by_facet: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for item in evidence:
            evidence_by_facet[item.get("facet_id", "general")].append(item)

        if evidence_by_facet:
            for facet_id, docs in sorted(evidence_by_facet.items()):
                lines.append(f"\n{'-' * 50}")
                lines.append(f"[Facet: {facet_id}] ({len(docs)} docs)")
                lines.append(f"{'-' * 50}")
                for item in docs:
                    lines.append(f"\n  doc_id : {item.get('doc_id', 'N/A')}")
                    lines.append(f"  level  : {item.get('relevance_level', 'N/A')}")
                    lines.append(f"  summary: {item.get('summary', 'N/A')}")
                    lines.append(f"  reason : {item.get('reason', 'N/A')}")
                    title = item.get("title") or item.get("metadata", {}).get("title", "")
                    if title:
                        lines.append(f"  title  : {title}")
        else:
            lines.append("\n[WARNING] No relevant evidence found.")

        lines.extend(
            [
                "",
                "=" * 60,
                f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "=" * 60,
            ]
        )
        return "\n".join(lines)

    def _calculate_confidence(self, evidence: List[Dict[str, Any]], iterations: int) -> float:
        if not evidence:
            return 0.3
        base = 0.6
        evidence_bonus = min(0.3, len(evidence) * 0.05)
        iteration_penalty = min(0.1, iterations * 0.03)
        return min(0.95, base + evidence_bonus - iteration_penalty)
