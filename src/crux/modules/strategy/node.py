"""
策略模块节点

包含：
- GapAnalysisNode: 缺口分析节点
- ReportNode: 报告生成节点
"""

import datetime
from typing import Dict, Any

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
        self.log("分析信息覆盖度...")
        
        evidence = state.get("verified_evidence", [])
        query = state["user_query"]
        iteration = state.get("search_iteration", 0) + 1
        max_iterations = self.config.search.max_iterations
        
        # 格式化证据供 LLM 分析
        evidence_text = self._format_evidence(evidence)
        
        # 构建 prompt 并调用 LLM
        prompt = get_gap_analysis_prompt(query=query, evidence=evidence_text)
        analysis = self.llm_client.call_json(prompt)
        
        # 判断是否需要回流
        if analysis.get("status") == "insufficient" and iteration < max_iterations:
            missing_info = analysis.get("missing_info", "未知信息缺口")
            self.log(f"[WARNING] 发现缺口: {missing_info}, 准备回流 (迭代 {iteration}/{max_iterations})...")
            return {
                "gap_analysis_result": "insufficient",
                "search_iteration": iteration,
            }
        else:
            if iteration >= max_iterations:
                self.log(f"[INFO] 达到最大迭代次数 ({max_iterations})，结束检索。")
            else:
                self.log("[SUCCESS] 信息充足，准备生成报告。")
            return {
                "gap_analysis_result": "sufficient",
                "search_iteration": iteration
            }
    
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
    description = "生成最终分析报告"
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成最终报告
        
        Args:
            state: 包含 verified_evidence, user_query 的状态
            
        Returns:
            包含 final_report 的更新
        """
        self.log("生成最终报告...")
        
        evidence = state.get("verified_evidence", [])
        query = state["user_query"]
        iterations = state.get("search_iteration", 0)
        
        # 生成报告
        report = self._generate_report(query, evidence, iterations)
        
        self.log(f"报告生成完成，包含 {len(evidence)} 条证据。")
        
        return {"final_report": report}
    
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
    
    def _get_current_time(self) -> str:
        """获取当前时间字符串"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
