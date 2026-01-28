"""
Adjudication Module - 深度研判模块

负责：
- 根据研判准则评估文档相关性
- 提取高价值证据
- 过滤语义相似但事实无关的噪音
"""

from src.crux.modules.adjudication.node import AdjudicationNode

__all__ = ["AdjudicationNode"]
