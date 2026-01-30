"""
Crux AgenticRAG Framework
=========================

基于意图深度感知的 AgenticRAG 框架，从"浅层搜索"向"深度推理"演进。

主要模块:
- modules: 核心业务模块 (understanding, retrieval, adjudication, strategy)
- utils: 通用工具 (LLM 客户端, BaseNode)
- data: 数据加载器
- schemas: 数据结构定义
- context: 上下文构建器
"""

from src.crux.graph import AgentGraph
from src.crux.state import AgentState
from src.crux.config import CruxConfig
from src.crux.state  import IntentObject

# 导出所有模块节点 (延迟导入以避免循环依赖)
def get_all_nodes():
    from src.crux.modules import (
        UnderstandingNode,
        RetrievalNode,
        AdjudicationNode,
        GapAnalysisNode,
        ReportNode,
    )
    return {
        "UnderstandingNode": UnderstandingNode,
        "RetrievalNode": RetrievalNode,
        "AdjudicationNode": AdjudicationNode,
        "GapAnalysisNode": GapAnalysisNode,
        "ReportNode": ReportNode,
    }

__version__ = "0.2.0"
__all__ = [
    "AgentGraph", 
    "AgentState", 
    "IntentObject", 
    "CruxConfig",
    "get_all_nodes",
]

