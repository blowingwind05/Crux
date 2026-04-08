"""
Judge 模块 Prompt 模板

FACET_JUDGE_PROMPT：根据 Facet 的 RelevanceRubric 对一批文档逐一研判。
输入变量：
  {{user_query}}
  {{facet_id}}
  {{facet_description}}
  {{tolerance_level}}
  {{quality_preference}}
  {{content_requirements}}
  {{documents}}           ← 编号文档列表（doc_id / title / abstract）
"""

FACET_JUDGE_PROMPT: str = """
You are a **Relevance Judge** for an agentic retrieval system.
Your task is to evaluate a list of candidate documents against a specific information facet and its relevance rubric.

## Information Facet
- Facet ID: {{facet_id}}
- Description: {{facet_description}}

## Relevance Rubric
- Tolerance level: {{tolerance_level}}
  - high   → accept survey/overview documents; shallow coverage is fine
  - medium → require meaningful coverage of the facet topic
  - low    → require precise data, authoritative sources, direct answers
- Quality preference: {{quality_preference}}
- Content requirements:
{{content_requirements}}

## Original User Query
{{user_query}}

## Candidate Documents
{{documents}}

## Your Task
For EACH document above, output one judgment with:
1. **doc_id** — copy the doc_id exactly as given
2. **summary** — 1-2 sentences summarizing what the document is about
3. **relevance_level** — one of: "high" / "medium" / "low" / "irrelevant"
   - "high"       → directly and fully addresses this facet; meets rubric strictly
   - "medium"     → partially addresses this facet; offers useful context or background
   - "low"        → tangentially related; minimal usefulness for this facet
   - "irrelevant" → does not address this facet at all
4. **reason** — 1-2 sentences citing specific rubric criteria to justify your judgment

Return a FacetJudgments JSON object. Evaluate ALL documents; do not skip any.
""".strip()


def build_facet_judge_prompt(
    user_query: str,
    facet_id: str,
    facet_description: str,
    tolerance_level: str,
    quality_preference: list,
    content_requirements: list,
    documents: str,
) -> str:
    return (
        FACET_JUDGE_PROMPT
        .replace("{{user_query}}", user_query)
        .replace("{{facet_id}}", facet_id)
        .replace("{{facet_description}}", facet_description)
        .replace("{{tolerance_level}}", tolerance_level)
        .replace("{{quality_preference}}", ", ".join(quality_preference))
        .replace("{{content_requirements}}", "\n".join(f"  - {r}" for r in content_requirements))
        .replace("{{documents}}", documents)
    )
