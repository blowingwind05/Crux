"""
Crux Agent 图定义

使用 LangGraph 构建 Agent 工作流。
"""

from langgraph.graph import StateGraph, END
from typing import Optional, Callable, Dict, Any

from src.crux.state import AgentState
from src.crux.config import CruxConfig


class AgentGraph:
    """
    Crux Agent 图构建器
    
    支持配置化的节点注册和图构建。
    """
    
    def __init__(self, config: Optional[CruxConfig] = None):
        self.config = config or CruxConfig()
        self._nodes: Dict[str, Callable] = {}
        self._compiled = None
    
    def register_node(self, name: str, node_func: Callable):
        """
        注册节点
        """
        self._nodes[name] = node_func
    
    def build(self):
        """
        构建并返回编译后的图
        """
        from src.crux.modules import (
            UnderstandingNode,
            RetrievalNode,
            JudgeNode,
            GapAnalysisNode,
            ReportNode,
        )

        # 1. 初始化图
        workflow = StateGraph(AgentState)

        # 2. 创建节点实例
        understanding = UnderstandingNode(self.config)
        retrieval = RetrievalNode(self.config)
        judge = JudgeNode(self.config)
        gap_analysis = GapAnalysisNode(self.config)
        report = ReportNode(self.config)

        # 3. 添加节点
        workflow.add_node("understand", understanding.process)
        workflow.add_node("retrieve", retrieval.process)
        workflow.add_node("judge", judge.process)
        workflow.add_node("analyze", gap_analysis.process)
        workflow.add_node("report", report.process)
        
        # 4. 定义流程
        workflow.set_entry_point("understand")
        workflow.add_edge("understand", "retrieve")
        workflow.add_edge("retrieve", "judge")
        workflow.add_edge("judge", "analyze")
        
        # 5. 定义条件分支 (闭环逻辑)
        def check_gap(state: AgentState) -> str:
            if state.get("gap_analysis_result") == "insufficient":
                return "retrieve"  # 回流到检索
            return "report"  # 结束
        
        workflow.add_conditional_edges(
            "analyze",
            check_gap,
            {
                "retrieve": "retrieve",
                "report": "report"
            }
        )
        
        workflow.add_edge("report", END)
        
        self._compiled = workflow.compile()
        return self._compiled

    def save_graph_image(self, graph = None, img_path= "graph.png") -> None:
        # 显示工作流
        png_data = graph.get_graph().draw_mermaid_png()
        with open(img_path, "wb") as f:
            f.write(png_data)

    def invoke(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行图
        """
        if self._compiled is None:
            self.build()
        return self._compiled.invoke(inputs)
    
    def stream(self, inputs: Dict[str, Any]):
        """
        流式运行图
        """
        if self._compiled is None:
            self.build()
        return self._compiled.stream(inputs)



