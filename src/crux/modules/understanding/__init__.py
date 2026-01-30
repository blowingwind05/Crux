"""
Understanding Module - 意图理解模块

负责：
- 解析用户自然语言查询
- 生成结构化 IntentObject
- 识别认知策略、约束条件、信息面
"""

from src.crux.modules.understanding.node import UnderstandingNode
from src.crux.state import IntentObject

__all__ = ["UnderstandingNode", "IntentObject"]
