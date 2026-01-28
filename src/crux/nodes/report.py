"""
报告生成节点 (Report Node)

负责人: [待分配]

功能:
- 整合验证后的证据
- 生成结构化分析报告
- 支持多种输出格式
"""

from typing import Dict, Any

from src.crux.nodes.base import BaseNode
from src.crux.core.state import AgentState


class ReportNode(BaseNode):
    """
    报告生成节点
    
    将验证后的证据整合为最终报告。
    """
    
    name = "report"
    description = "生成最终分析报告"
    
    def process(self, state: AgentState) -> Dict[str, Any]:
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
        """
        生成结构化报告
        
        Args:
            query: 原始查询
            evidence: 证据列表
            iterations: 检索迭代次数
            
        Returns:
            格式化的报告文本
        """
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
                
                # 显示元数据
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
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
