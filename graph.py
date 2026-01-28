from langgraph.graph import StateGraph, END
from state import AgentState
from nodes import (
    node_understanding,
    node_retrieval,
    node_adjudication,
    node_gap_analysis,
    node_report
)

def build_graph():
    # 1. 初始化图
    workflow = StateGraph(AgentState)

    # 2. 添加节点
    workflow.add_node("understand", node_understanding)
    workflow.add_node("retrieve", node_retrieval)
    workflow.add_node("judge", node_adjudication)
    workflow.add_node("analyze", node_gap_analysis)
    workflow.add_node("report", node_report)

    # 3. 定义流程
    workflow.set_entry_point("understand")
    workflow.add_edge("understand", "retrieve")
    workflow.add_edge("retrieve", "judge")
    workflow.add_edge("judge", "analyze")

    # 4. 定义条件分支 (闭环逻辑)
    def check_gap(state):
        if state["gap_analysis_result"] == "insufficient":
            return "retrieve" # 回流到检索
        return "report"   # 结束

    workflow.add_conditional_edges(
        "analyze",
        check_gap,
        {
            "retrieve": "retrieve",
            "report": "report"
        }
    )
    
    workflow.add_edge("report", END)

    return workflow.compile()
