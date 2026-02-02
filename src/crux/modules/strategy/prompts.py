"""
策略模块 - Prompt 模板

定义缺口分析相关的 Prompt。
"""

# =============================================================================
# 缺口分析 Prompt
# =============================================================================

GAP_ANALYSIS_TEMPLATE = """
Role:
You are the **Strategy Planner**.

Given:
- The User Question
{query}
- Collected Evidence
{evidence}
- The Information Facets
{facets}

Tasks:
1. Check if the collected evidence fully satisfies all information facets:
    - If YES, respond with "sufficient" and no missing info
    - If NO, respond with "insufficient" and identify what information is missing to satisfy the facets
2. Provide a coverage score with the range of 0 to 1, indicating the degree of evidence satisfaction for the facets

Output format (only JSON, nothing else): 
{{
    "status": "sufficient | insufficient",
    "missing_info": "null or description of what is missing"
    "coverage_score": 0.X
}}
"""


def get_gap_analysis_prompt(query: str, evidence: str, facets: str) -> str:
    """构建缺口分析 prompt"""
    return GAP_ANALYSIS_TEMPLATE.format(query=query, evidence=evidence, facets=facets)
