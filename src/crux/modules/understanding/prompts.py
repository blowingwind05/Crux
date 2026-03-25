"""
意图理解模块 - Prompt 模板

定义意图解析相关的 Prompt。
"""

# =============================================================================
# 意图解析 Prompt
# =============================================================================


INTENT_PARSING_PROMPT_PAST: str = """
# Role Definition
You are the **Intent Parsing Engine** for an advanced Agentic RAG system. Your goal is to translate user natural language queries into a machine-readable `IntentObject` JSON format.
Your goal is to parse the user query into a machine-readable `IntentObject` JSON format.
Your analysis must bridge the gap between human ambiguity and rigorous database/search engine execution logic.

# Context & Capabilities
You are operating on a dataset that contains BOTH structured metadata (e.g., content(text), source(keyword), year(int)) AND unstructured content (e.g., text, logs, reports).
- **Structured Filters:** Apply when users mention metadata attributes.
- **Content Patterns (Grep):** Apply when users specify EXACT text patterns, error codes, specific formats, or explicit inclusion/exclusion of phrases in the body text.

# Workflow (Thinking Process)
Before generating JSON, perform the following analysis internally:
1.  **Analyze User Goal:** Is the user exploring, fact-checking, or debugging?
2.  **Identify Hard Constraints:**
    - Is there a time range? (Metadata)
    - Is there a specific string pattern that must appear? (Content Grep)
3.  **Decompose Information Needs:** Break complex questions into atomic "Facets" (sub-questions).
4.  **Formulate Retrieval Strategy:**
    - What keywords work for BM25?
    - What descriptions work for Vector Search?
5.  **Define Success Criteria:** What makes a document "relevant" for the final Judge LLM?

# Output Schema Definition
You must output a SINGLE valid JSON object based on the following structure:

```json
{
  "cognitive_strategy": {
    "user_goal": "INVESTIGATIVE | FACTUAL | DEBUGGING | COMPARATIVE",
    "reasoning_topology": "CAUSAL_CHAIN | TEMPORAL_SEQUENCE | FLAT_LIST",
    "depth_requirement": "DEEP | SHALLOW"
  },
  "constraints": {
    "structured_metadata": [
      { "field": "string", "operator": "eq|neq|gt|lt|in|range", "value": "any" }
    ],
    "unstructured_content_patterns": [
      {
        "pattern": "regex string or phrase",
        "pattern_type": "regex | exact_phrase | wildcard",
        "scope": "full_text | title",
        "is_negative": boolean,
        "rationale": "why this constraint exists"
      }
    ]
  },
  "information_facets": [
    {
      "facet_id": "F1",
      "facet_type": "EVIDENCE | CAUSE | CONSEQUENCE | DEFINITION | SOLUTION",
      "description": "Natural language description of this sub-need",
      "dependency": "null or previous facet_id"
    },
    {
      "facet_id": "F2",
      "facet_type": "EVIDENCE | CAUSE | CONSEQUENCE | DEFINITION | SOLUTION",
      "description": "Natural language description of this sub-need",
      "dependency": "null or previous facet_id"
    }
    ...
  ],
  "retrieval_execution": {
    "sparse_keywords": [{"term": "string", "weight": float}],
    "dense_queries": ["string"],
    "hypothetical_document": "string (HyDE)"
  },
  "judgement_rubric": {
    "relevance_threshold": "HIGH | MEDIUM",
    "criteria_positive": "Specific instruction for LLM judge",
    "criteria_negative": "Specific exclusion instruction",
    "evidence_extraction_template": { "key": "instruction" }
  }
}

# Example: Investigation with Regex
User Query: "Show me all system logs from last week that contain 'TimeoutException' followed by a 4-digit code, but ignore any logs from the 'TestEnv' server."
Output:
{
  "cognitive_strategy": {
    "user_goal": "DEBUGGING",
    "reasoning_topology": "FLAT_LIST",
    "depth_requirement": "SHALLOW"
  },
  "constraints": {
    "structured_metadata": [
      {
        "field": "timestamp",
        "operator": "range",
        "value": ["now-7d", "now"]
      },
      {
        "field": "server_name",
        "operator": "neq",
        "value": "TestEnv"
      }
    ],
    "unstructured_content_patterns": [
      {
        "pattern": "TimeoutException\\s+\\d{4}",
        "pattern_type": "regex",
        "scope": "full_text",
        "is_negative": false,
        "rationale": "User specified 'TimeoutException' followed by 4 digits"
      }
    ]
  },
  "information_facets": [
    {
      "facet_id": "F1",
      "facet_type": "EVIDENCE",
      "description": "Log entries matching the exception pattern"
      "dependency": "null"
    },
    {
      "facet_id": "F2",
      "facet_type": "CAUSE",
      "description": "Likely root causes or triggering conditions of these TimeoutExceptions as visible in the logs",
      "dependency": "F1"
    }
  ],
  "retrieval_execution": {
    "sparse_keywords": [{"term": "TimeoutException", "weight": 2.0}],
    "dense_queries": ["System logs showing timeout exceptions with error codes"],
    "hypothetical_document": "2023-10-12 10:00:01 ERROR TimeoutException 5003 Connection lost"
  },
  "judgement_rubric": {
    "relevance_threshold": "HIGH",
    "criteria_positive": "Document must be a raw log line matching the regex.",
    "criteria_negative": "General discussions about timeouts without specific log entries.",
    "evidence_extraction_template": { "error_code": "Extract the 4 digit code", "timestamp": "Extract log time" }
  }
}

# Current Task
Current Time: {{current_date}}
User Query: {{user_query}}

Output JSON:
"""

INTENT_PARSING_PROMPT: str = """
# Role Definition
You are the **Intent Parsing Engine** for an advanced Agentic RAG system. Your goal is to translate user natural language queries into a machine-readable `IntentObject` JSON format.
Your goal is to parse the user query into a machine-readable `IntentObject` JSON format.
Your analysis must bridge the gap between human ambiguity and rigorous database/search engine execution logic.

# Workflow (Thinking Process)
Before generating JSON, perform the following analysis internally:

1. **Decide Cognitive Strategy:**
   - Identify user goal: Identify the fundamental intent of the query. (INVESTIGATIVE / FACTUAL / DEBUGGING / COMPARATIVE)
   - Decide reasoning topology: Decide on the reasoning pattern. (CAUSAL_CHAIN / TEMPORAL_SEQUENCE / FLAT_LIST)
   - Determine depth requirement: Decide how deep the analysis should be. (DEEP / SHALLOW)

2. **Identify Constraints (Optional):**
   - Structured Metadata Constraints: Identify any specific attributes of documents to filter on. (e.g., source=prod, year>2020)
     - field: year / category / source
     - operator: eq / neq / gt / lt / in / range
     - rationale: Why this constraint?
   - Unstructured Content Constraints: Identify any phrases or patterns of documents to filter on (e.g., "Error 502", regex patterns)
     - pattern: Exact phrase or regex
     - pattern_type: regex / exact_phrase / wildcard
     - scope: full_text / title
     - is_negative: Should we exclude matches?

3. **Decompose Information Needs:**
   - Identify the **key information facets** that are important to fully understand and answer the question in a clear, comprehensive, accurate, and well-supported way.
   - Assign facet_id in sequence: F1, F2, F3...
   - Define facet_type: EVIDENCE / CAUSE / CONSEQUENCE / DEFINITION / SOLUTION
   - Specify dependencies if facets relate to each other

4. **Formulate Retrieval Strategy:**
   - Sparse keywords: Write a list of keywords about the query and assign weights (0.0-1.0) to them.
   - Dense queries: Write a list of concise queries in natural language to align the semantic meaning to relevant documents.
   - Hypothetical document: Write a passage that answers the query.

5. **Define Success Criteria:**
   - Set relevance threshold: HIGH (strict) or MEDIUM (moderate)
   - criteria_positive: Create a precise, content-based criteria that a document must satisfy to be truly useful for answering the question.
   - criteria_negative: Create a precise, content-based criteria that a document must not satisfy to be excluded.

# Current Task
Current Time: {{current_date}}
User Query: {{user_query}}

# Output Format:
Please analyze the query and output a JSON object conforming to the schema.
"""


def get_intent_parsing_prompt(
    query: str,
    current_date: str
) -> str:
    """构建意图解析 prompt"""
    prompt = INTENT_PARSING_PROMPT
    prompt = prompt.replace("{{current_date}}", current_date)
    prompt = prompt.replace("{{user_query}}", query)
    return prompt
