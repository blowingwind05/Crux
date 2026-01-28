"""
Crux AgenticRAG Framework
=========================

基于意图深度感知的 AgenticRAG 框架，从"浅层搜索"向"深度推理"演进。

主要模块:
- core: 核心状态和图定义
- nodes: 各功能节点实现
- data: 数据加载器
- schemas: 数据结构定义
- context: 上下文构建器
- prompts: 提示语模板
- llm: LLM 调用封装
"""

from src.crux.core.graph import AgentGraph
from src.crux.core.state import AgentState, IntentObject
from src.crux.config import CruxConfig

__version__ = "0.1.0"
__all__ = ["AgentGraph", "AgentState", "IntentObject", "CruxConfig"]
