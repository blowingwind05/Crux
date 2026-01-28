"""
策略模块 - Prompt 模板

定义缺口分析相关的 Prompt。
"""

# =============================================================================
# 缺口分析 Prompt
# =============================================================================

GAP_ANALYSIS_TEMPLATE = """
You are the **Strategy Planner**.

Original Query: {query}

Collected Evidence:
{evidence}

Does the collected evidence fully answer the original query?

If YES, output JSON: {{"status": "sufficient"}}
If NO, output JSON: {{"status": "insufficient", "missing_info": "Describe what is missing"}}
"""


def get_gap_analysis_prompt(query: str, evidence: str) -> str:
    """构建缺口分析 prompt"""
    return GAP_ANALYSIS_TEMPLATE.format(query=query, evidence=evidence)
