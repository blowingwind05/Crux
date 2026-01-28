"""
提示语模块
"""

from src.crux.prompts.templates import (
    INTENT_PARSING_TEMPLATE,
    ADJUDICATION_TEMPLATE,
    GAP_ANALYSIS_TEMPLATE,
    get_intent_parsing_prompt,
    get_adjudication_prompt,
    get_gap_analysis_prompt,
)

__all__ = [
    "INTENT_PARSING_TEMPLATE",
    "ADJUDICATION_TEMPLATE",
    "GAP_ANALYSIS_TEMPLATE",
    "get_intent_parsing_prompt",
    "get_adjudication_prompt",
    "get_gap_analysis_prompt",
]
