"""
策略模块 - Prompt 模板

FACET_SUFFICIENCY_PROMPT：根据 CompletionCriteria 对每个 Facet 做充足性评估。
输入变量：
  {{metric_type}}
  {{threshold_description}}
  {{specific_conditions}}
  {{facets_evidence_block}}   ← 每个 Facet 的 description + 已收集证据列表
"""

FACET_SUFFICIENCY_PROMPT: str = """
You are a **Verification Agent** for an agentic retrieval system.
Your task is to assess whether the collected evidence sufficiently addresses EACH information facet,
based on the CompletionCriteria below.

## CompletionCriteria
- Metric type: {{metric_type}}
- Threshold: {{threshold_description}}
- Specific conditions:
{{specific_conditions}}

## Facets & Their Collected Evidence
{{facets_evidence_block}}

## Your Task
For EACH facet listed above, output one assessment with:
1. **facet_id** — copy the facet_id exactly as given
2. **satisfied** — true if the collected evidence meets the threshold for this facet, false otherwise
3. **reason** — 1 sentence explaining why the evidence is or is not sufficient

Also set **overall_sufficient** to true only if ALL facets are satisfied.

Return a FacetSufficiencyResult JSON object. Evaluate ALL facets; do not skip any.
""".strip()


def build_sufficiency_prompt(
    criteria: dict,
    facets_evidence_block: str,
) -> str:
    specific_conditions = criteria.get("specific_conditions", [])
    conditions_text = "\n".join(f"  - {c}" for c in specific_conditions) if specific_conditions else "  (none specified)"

    return (
        FACET_SUFFICIENCY_PROMPT
        .replace("{{metric_type}}", criteria.get("metric_type", "coverage"))
        .replace("{{threshold_description}}", criteria.get("threshold_description", ""))
        .replace("{{specific_conditions}}", conditions_text)
        .replace("{{facets_evidence_block}}", facets_evidence_block)
    )
