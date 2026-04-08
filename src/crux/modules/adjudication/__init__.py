"""Backward-compatible alias for the old adjudication module name."""

from src.crux.modules.judge import JudgeNode as AdjudicationNode

__all__ = ["AdjudicationNode"]
