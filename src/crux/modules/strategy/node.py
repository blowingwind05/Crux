"""
策略模块节点

包含：
- GapAnalysisNode: Per-Facet 充足性研判节点
- ReportNode: 报告生成节点
"""

import datetime
import time
from collections import defaultdict
from typing import Dict, Any, List, Set

from src.crux.utils.base import BaseNode
from src.crux.utils.llm_client import LLMClient
from src.crux.modules.strategy.prompts import build_sufficiency_prompt
from src.crux.state.retrieval import FacetSufficiencyResult


def _build_facets_evidence_block(pending_facets: List[Dict], verified_evidence: List[Dict]) -> str:
    """将每个待评估 Facet 与其已收集证据拼成文本块，供充足性评估 Prompt 使用"""
    ev_by_facet: Dict[str, List[Dict]] = {}
    for e in verified_evidence:
        ev_by_facet.setdefault(e.get("facet_id", "unknown"), []).append(e)

    lines = []
    for f in pending_facets:
        fid = f["facet_id"]
        docs = ev_by_facet.get(fid, [])
        lines.append(f"### Facet {fid}: {f.get('description', '')}")
        if docs:
            for d in docs:
                lines.append(f"  - [{d.get('relevance_level', '?')}] {d.get('summary', '')}")
        else:
            lines.append("  (no evidence collected yet)")
    return "\n".join(lines)


class GapAnalysisNode(BaseNode):
    """
    Per-Facet 充足性研判节点

    1. 只评估尚未满足的 Facet
    2. LLM 根据 CompletionCriteria 逐 Facet 输出 satisfied/reason
    3. 新增满足的 Facet 写入 satisfied_facets（operator.or_ 累积）
    4. 若仍有未满足 Facet 且未达最大迭代次数 → 裁剪 intent["expansions"] 后回流
    """

    name = "analyze"
    name_cn = "充足性研判"
    description = "Per-Facet 充足性评估，决定回流或进入报告"

    def __init__(self, config=None):
        super().__init__(config)
        self.llm_client = LLMClient(config)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.reset_logger()

        iteration = state.get("search_iteration", 0) + 1
        max_iterations = self.config.search.max_iterations

        intent = state["intent"]
        criteria: Dict = intent["agent_plan"]["criteria"]
        facets_raw: List[Dict] = intent["agent_plan"]["facets"]
        satisfied_so_far: Set[str] = state.get("satisfied_facets", set())

        self.log(f"迭代 {iteration}/{max_iterations}，已满足 Facet: {satisfied_so_far}")

        # ── 1. 只评估尚未满足的 Facet ────────────────────────────────
        pending_facets = [f for f in facets_raw if f["facet_id"] not in satisfied_so_far]
        if not pending_facets:
            self.log("所有 Facet 已满足，直接进入报告", level="INFO")
            return self.build_result({
                "gap_analysis_result": "sufficient",
                "search_iteration": iteration,
                "gap_analysis_details": {
                    "coverage_score": coverage,
                    "missing_info": missing,
                    "suggested_queries": suggested_queries,
                    "raw_analysis": analysis,
                },
            })

        self.log(f"待评估 Facet: {[f['facet_id'] for f in pending_facets]}")

        # ── 2. 构建 Prompt ───────────────────────────────────────────
        facets_evidence_block = _build_facets_evidence_block(
            pending_facets, state.get("verified_evidence", [])
        )
        prompt = build_sufficiency_prompt(criteria, facets_evidence_block)

        # ── 3. LLM Per-Facet 充足性评估 ──────────────────────────────
        self.log("调用 LLM 进行 Per-Facet 充足性评估...")
        result: FacetSufficiencyResult = self.llm_client.call_object(prompt, FacetSufficiencyResult)

        # ── 4. 解析结果 ──────────────────────────────────────────────
        newly_satisfied: Set[str] = {f.facet_id for f in result.facets if f.satisfied}
        remaining = [f for f in result.facets if not f.satisfied]

        for f in result.facets:
            status = "✓" if f.satisfied else "✗"
            self.log(f"  [{status}] Facet {f.facet_id}: {f.reason}")

        overall_done = (not remaining) or (iteration >= max_iterations)

        if overall_done:
            if iteration >= max_iterations and remaining:
                self.log(f"达到最大迭代次数 ({max_iterations})，强制结束", level="INFO")
            else:
                self.log("所有 Facet 充足，进入报告生成", level="INFO")
            return self.build_result({
                "gap_analysis_result": "sufficient",
                "search_iteration": iteration,
                "gap_analysis_details": {
                    "coverage_score": coverage,
                    "missing_info": missing,
                    "suggested_queries": analysis.get("suggested_queries", []),
                    "raw_analysis": analysis,
                },
            })


class ReportNode(BaseNode):
    """
    报告生成节点

    将验证后的证据按 Facet 分组，整合为最终结构化报告。
    """

    name = "report"
    name_cn = "报告生成"
    description = "生成最终分析报告"

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.reset_logger()

        evidence = state.get("verified_evidence", [])
        query = state["user_query"]
        iterations = state.get("search_iteration", 0)
        satisfied_facets = state.get("satisfied_facets", set())

        self.log(f"原始查询: {query}")
        self.log(f"总迭代次数: {iterations}，满足 Facet: {satisfied_facets}")
        self.log(f"可用证据: {len(evidence)} 条")

        start_time = time.time()
        report = self._generate_report(query, evidence, iterations, satisfied_facets)
        gen_time = (time.time() - start_time) * 1000

        self.log(f"报告生成完成 (耗时: {gen_time:.0f}ms)")

        confidence = self._calculate_confidence(evidence, iterations)
        self.log(f"报告置信度: {confidence:.1%}")

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

        # 按 Facet 分组
        ev_by_facet: Dict[str, List[Dict]] = defaultdict(list)
        for e in evidence:
            ev_by_facet[e.get("facet_id", "general")].append(e)

        if ev_by_facet:
            for facet_id, docs in sorted(ev_by_facet.items()):
                lines.append(f"\n{'─' * 50}")
                lines.append(f"[Facet: {facet_id}]  ({len(docs)} docs)")
                lines.append(f"{'─' * 50}")
                for e in docs:
                    lines.append(f"\n  doc_id : {e.get('doc_id', 'N/A')}")
                    lines.append(f"  level  : {e.get('relevance_level', 'N/A')}")
                    lines.append(f"  summary: {e.get('summary', 'N/A')}")
                    lines.append(f"  reason : {e.get('reason', 'N/A')}")
                    title = e.get("title") or e.get("metadata", {}).get("title", "")
                    if title:
                        lines.append(f"  title  : {title}")
        else:
            lines.append("\n[WARNING] No relevant evidence found.")

        lines.extend([
            "",
            "=" * 60,
            f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
        ])
        return "\n".join(lines)

    def _calculate_confidence(self, evidence: list, iterations: int) -> float:
        if not evidence:
            return 0.3
        base = 0.6
        evidence_bonus = min(0.3, len(evidence) * 0.05)
        iteration_penalty = min(0.1, iterations * 0.03)
        return min(0.95, base + evidence_bonus - iteration_penalty)
