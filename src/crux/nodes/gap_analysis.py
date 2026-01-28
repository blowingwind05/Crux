"""
缺口分析节点 (Gap Analysis Node)

负责人: [待分配]

功能:
- 分析已验证证据的覆盖度
- 判断是否需要补充检索
- 实现闭环控制逻辑
"""

from typing import Dict, Any

from src.crux.nodes.base import BaseNode
from src.crux.core.state import AgentState
from src.crux.llm.client import LLMClient
from src.crux.prompts.templates import get_gap_analysis_prompt


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
    
    def process(self, state: AgentState) -> Dict[str, Any]:
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
                # 可以在这里更新 intent 以聚焦缺失信息
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
        """
        格式化证据列表为文本
        
        Args:
            evidence: 证据列表
            
        Returns:
            格式化的文本
        """
        if not evidence:
            return "暂无收集到的证据。"
        
        lines = []
        for idx, e in enumerate(evidence, 1):
            lines.append(f"{idx}. {e.get('content', str(e))}")
        return "\n".join(lines)
