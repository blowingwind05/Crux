"""
Modules 核心业务模块

每个模块独立可优化，包含：
- node.py: 暴露给 Graph 的节点函数
- prompts.py: 模块专用的 Prompt
- models.py: 模块专用的 Pydantic 结构
"""

from src.crux.modules.understanding import UnderstandingNode
from src.crux.modules.retrieval import RetrievalNode
from src.crux.modules.adjudication import AdjudicationNode
from src.crux.modules.strategy import GapAnalysisNode, ReportNode

__all__ = [
    "UnderstandingNode",
    "RetrievalNode", 
    "AdjudicationNode",
    "GapAnalysisNode",
    "ReportNode",
]
