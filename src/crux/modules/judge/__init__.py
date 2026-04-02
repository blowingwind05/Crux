"""
Judge Module - 相关性研判模块

负责：
- 按 Facet 对候选文档进行相关性研判
- 根据每个 Facet 的 RelevanceRubric 输出文档摘要、相关性等级和判断理由
"""

from src.crux.modules.judge.node import JudgeNode

__all__ = ["JudgeNode"]
