"""
意图理解模块 - Prompt 模板

定义意图解析相关的 Prompt。
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
