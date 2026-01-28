"""
Strategy Module - 策略模块 (缺口分析与报告)

负责：
- 分析已验证证据的覆盖度
- 判断是否需要补充检索
- 实现闭环控制逻辑
- 生成最终分析报告
"""

from src.crux.modules.strategy.node import GapAnalysisNode, ReportNode

__all__ = ["GapAnalysisNode", "ReportNode"]
