"""
研判模块 - Prompt 模板

定义研判相关的 Prompt。
"""

# =============================================================================
# 研判 Prompt
# =============================================================================

ADJUDICATION_TEMPLATE = """
You are the **Critical Judge**.
Evaluate the following document based on the strictly defined rubric.

Rubric: {rubric}

Document Content:
{doc_content}

If the document is relevant and meets the rubric:
1. Extract the specific evidence (quote or summary).
2. Return JSON: {{"is_relevant": true, "evidence": "...", "reason": "..."}}

If NOT relevant:
Return JSON: {{"is_relevant": false, "reason": "..."}}
"""


def get_adjudication_prompt(rubric: str, doc_content: str) -> str:
    """构建研判 prompt"""
    return ADJUDICATION_TEMPLATE.format(rubric=rubric, doc_content=doc_content)
