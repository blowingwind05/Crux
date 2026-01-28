"""
提示语模板

所有 prompt 模板都使用 {{变量名}} 格式的占位符。
Schema 信息通过 {{schema_description}} 动态注入。
"""

# =============================================================================
# 意图解析 Prompt
# =============================================================================

INTENT_PARSING_TEMPLATE = """
# Role Definition
You are the **Intent Parsing Engine** for an advanced Agentic RAG system.
Your goal is to parse the user query into a machine-readable `IntentObject` JSON format.
Your analysis must bridge the gap between human ambiguity and rigorous database/search engine execution logic.

# Data Schema Context
{{schema_description}}

{{env_context}}

# Workflow (Thinking Process)
Before generating JSON, perform the following analysis internally:
1.  **Analyze User Goal:** Is the user exploring, fact-checking, or debugging?
2.  **Identify Hard Constraints:**
    - Is there a time range? (Metadata filter)
    - Is there a specific category or topic to focus on?
3.  **Formulate Retrieval Strategy:**
    - What keywords work for BM25?
    - What descriptions work for Vector Search?
4.  **Define Success Criteria:** What makes a document "relevant" for the final Judge LLM?

# Output Schema
You must output a SINGLE valid JSON object:
```json
{
  "user_goal": "INVESTIGATIVE | FACTUAL | DEBUGGING | COMPARATIVE",
  "constraints": {
    "structured_metadata": [
      { "field": "string", "operator": "eq|neq|gt|lt|gte|lte|in|range", "value": "any" }
    ]
  },
  "keywords_bm25": ["keyword1", "keyword2"],
  "queries_vector": ["semantic query 1", "semantic query 2"],
  "rubric": "Document relevance criteria for the judge",
  "missing_info_gap": null
}
```

# Current Task
Current Time: {{current_date}}
User Query: {{user_query}}
{{extra_context}}

Output JSON:
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


# =============================================================================
# 便捷函数
# =============================================================================

def get_intent_parsing_prompt(
    query: str,
    current_date: str,
    schema_description: str = "",
    env_context: str = "",
    extra_context: str = ""
) -> str:
    """构建意图解析 prompt"""
    prompt = INTENT_PARSING_TEMPLATE
    prompt = prompt.replace("{{current_date}}", current_date)
    prompt = prompt.replace("{{user_query}}", query)
    prompt = prompt.replace("{{schema_description}}", schema_description)
    prompt = prompt.replace("{{env_context}}", env_context)
    prompt = prompt.replace("{{extra_context}}", extra_context)
    return prompt


def get_adjudication_prompt(rubric: str, doc_content: str) -> str:
    """构建研判 prompt"""
    return ADJUDICATION_TEMPLATE.format(rubric=rubric, doc_content=doc_content)


def get_gap_analysis_prompt(query: str, evidence: str) -> str:
    """构建缺口分析 prompt"""
    return GAP_ANALYSIS_TEMPLATE.format(query=query, evidence=evidence)
