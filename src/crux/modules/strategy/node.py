"""
策略模块节点

包含：
- GapAnalysisNode: 缺口分析节点
- ReportNode: 报告生成节点
"""

import datetime
import time
from typing import Dict, Any, List

from src.crux.utils.base import BaseNode
from src.crux.utils.llm_client import LLMClient
from src.crux.modules.strategy.prompts import get_gap_analysis_prompt


class GapAnalysisNode(BaseNode):
    """
    信息缺口识别节点
    
    分析已验证证据是否覆盖原始意图:
    - 有缺口：生成新查询，回流到检索阶段
    - 覆盖足够：进入报告生成阶段
    """
    
    name = "analyze"
    name_cn = "缺口分析"
    description = "分析信息覆盖度，识别信息缺口"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.llm_client = LLMClient(config)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析信息缺口
        
        Args:
            state: 包含 verified_evidence, user_query, search_iteration 的状态
            
        Returns:
            包含 gap_analysis_result, search_iteration 的更新
        """
        self.reset_logger()
        
        evidence = state.get("verified_evidence", [])
        query = state["user_query"]
        intent = state.get("intent", {})
        iteration = state.get("search_iteration", 0) + 1
        max_iterations = self.config.search.max_iterations
        
        self.log("开始信息缺口分析...")
        self.log(f"当前迭代: {iteration}/{max_iterations}")
        self.log(f"已收集证据: {len(evidence)} 条")
        
        # 获取信息面要求
        facets = intent.get("information_facets", [])
        if facets:
            self.log(f"需满足信息面: {len(facets)} 个", details={
                "facets": [f.get("facet_id", str(f)) for f in facets]
            })
        
        # 格式化证据供 LLM 分析
        evidence_text = self._format_evidence(evidence)
        
        # 构建 prompt 并调用 LLM
        self.log("调用 LLM 进行覆盖度分析...")
        prompt = get_gap_analysis_prompt(query=query, evidence=evidence_text, facets=facets)
        analysis = self.llm_client.call_json(prompt)
        
        # 解析分析结果
        status = analysis.get("status", "sufficient")
        coverage = analysis.get("coverage_score", 0.8)
        missing = analysis.get("missing_info", [])
        if isinstance(missing, str):
            missing = [missing] if missing else []
        
        self.log(f"覆盖度评分: {coverage:.1%}")
        
        # 判断是否需要回流
        if status == "insufficient" and iteration < max_iterations:
            self.log(f"[WARNING] 发现信息缺口", level="WARN", details={
                "missing": missing,
                "coverage": coverage,
            })
            
            for gap in missing[:3]:
                self.log(f"  - 缺失: {gap}", level="WARN")
            
            suggested_queries = analysis.get("suggested_queries", [])
            if suggested_queries:
                self.log(f"建议补充查询: {len(suggested_queries)} 条")
                for sq in suggested_queries[:2]:
                    self.log(f"  → {sq}")
            
            self.log(f"决策: 回流到检索阶段 (迭代 {iteration}/{max_iterations})")
            
            return self.build_result({
                "gap_analysis_result": "insufficient",
                "search_iteration": iteration,
                "gap_analysis_details": {
                    "coverage_score": coverage,
                    "missing_info": missing,
                    "suggested_queries": suggested_queries,
                    "raw_analysis": analysis,
                },
            })
        else:
            if iteration >= max_iterations:
                self.log(f"达到最大迭代次数 ({max_iterations})，结束检索", level="INFO")
            else:
                self.log("[SUCCESS] 信息覆盖充足", level="INFO")
            
            self.log(f"决策: 进入报告生成阶段")
            
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
    
    def _format_evidence(self, evidence: list) -> str:
        """格式化证据列表为文本"""
        if not evidence:
            return "暂无收集到的证据。"
        
        lines = []
        for idx, e in enumerate(evidence, 1):
            lines.append(f"{idx}. {e.get('content', str(e))}")
        return "\n".join(lines)


class ReportNode(BaseNode):
    """
    报告生成节点
    
    将验证后的证据整合为最终报告。
    """
    
    name = "report"
    name_cn = "报告生成"
    description = "生成最终分析报告"
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终报告
        
        Args:
            state: 包含 verified_evidence, user_query 的状态
            
        Returns:
            包含 final_report 的更新
        """
        self.reset_logger()
        
        evidence = state.get("verified_evidence", [])
        query = state["user_query"]
        iterations = state.get("search_iteration", 0)
        
        self.log("开始生成最终报告...")
        self.log(f"原始查询: {query}")
        self.log(f"总迭代次数: {iterations}")
        self.log(f"可用证据: {len(evidence)} 条")
        
        # 分析证据来源分布
        sources = {}
        for e in evidence:
            src = e.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        
        if sources:
            self.log(f"证据来源分布: {sources}", details=sources)
        
        # 生成报告
        self.log("整合证据，生成结构化报告...")
        start_time = time.time()
        report = self._generate_report(query, evidence, iterations)
        gen_time = (time.time() - start_time) * 1000
        
        self.log(f"报告生成完成 (耗时: {gen_time:.0f}ms)")
        
        # 提取关键发现摘要
        findings = self._extract_key_findings(evidence)
        if findings:
            self.log("关键发现摘要:")
            for i, f in enumerate(findings[:3], 1):
                self.log(f"  [{i}] {f[:80]}...")
        
        # 计算置信度
        confidence = self._calculate_confidence(evidence, iterations)
        self.log(f"报告置信度: {confidence:.1%}", details={
            "confidence": confidence,
            "evidence_count": len(evidence),
            "iterations": iterations,
        })
        
        return self.build_result({"final_report": report})
    
    def _generate_report(
        self,
        query: str,
        evidence: list,
        iterations: int
    ) -> str:
        """生成结构化报告"""
        lines = [
            "=" * 50,
            "[REPORT] AgenticRAG Analysis Report",
            "=" * 50,
            "",
            f"[Query] {query}",
            f"[Iterations] {iterations}",
            f"[Evidence Count] {len(evidence)}",
            "",
            "-" * 50,
            "[KEY FINDINGS]",
            "-" * 50,
        ]
        
        if evidence:
            for idx, e in enumerate(evidence, 1):
                lines.append(f"\n[Evidence {idx}]")
                lines.append(f"  Content: {e.get('content', 'N/A')}")
                lines.append(f"  Source: {e.get('source', 'unknown')} (ID: {e.get('doc_id', 'N/A')})")
                lines.append(f"  Reason: {e.get('reason', 'N/A')}")
                
                metadata = e.get("metadata", {})
                if metadata.get("title"):
                    lines.append(f"  Title: {metadata['title']}")
        else:
            lines.append("\n[WARNING] No relevant evidence found.")
        
        lines.extend([
            "",
            "=" * 50,
            "报告生成时间: " + self._get_current_time(),
            "=" * 50,
        ])
        
        return "\n".join(lines)
    
    def _extract_key_findings(self, evidence: List[Dict[str, Any]]) -> List[str]:
        """从证据中提取关键发现"""
        findings = []
        for e in evidence[:5]:
            reason = e.get("reason", "")
            content = e.get("content", "")
            if reason:
                findings.append(reason)
            elif content:
                findings.append(content[:100])
        return findings
    
    def _calculate_confidence(self, evidence: list, iterations: int) -> float:
        """计算报告置信度"""
        if not evidence:
            return 0.3
        
        base = 0.6
        evidence_bonus = min(0.3, len(evidence) * 0.05)
        iteration_penalty = min(0.1, iterations * 0.03)
        
        return min(0.95, base + evidence_bonus - iteration_penalty)
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
