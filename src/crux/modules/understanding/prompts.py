"""
understand 模块 Prompt 模板

四个独立 Prompt，对应 understand 模块的四个阶段：
- COGNITIVE_STATE_PROMPT    : Stage 1a — query → CognitiveState
- CONSTRAINTS_PROMPT        : Stage 1b — query → Constraints
- AGENT_PLAN_PROMPT         : Stage 2  — query + cognitive guidance → AgentPlan
- FACET_EXPANSION_PROMPT    : Stage 3  — facet_id + description → FacetExpansion
"""


# =============================================================================
# Stage 1a: CognitiveState
# =============================================================================

COGNITIVE_STATE_PROMPT: str = """
You are a query intent classifier for an agentic retrieval system.
Given a user query, select exactly ONE cognitive mode and ONE logical dependency type that best characterize the information need.

## Cognitive Mode Options

| Mode | When to Choose | Key Signal |
|------|---------------|------------|
| exploratory | User wants a broad survey or overview; curiosity-driven, no specific target | "what is", "overview of", "tell me about" |
| deep_thinking | User wants depth on a specific aspect; concrete, analytical | "how does X work", "explain the mechanism", "compare A and B in detail" |
| verification | User suspects conflicting info or wants fact-checking; seeking authoritative resolution | "is it true that", "I heard X, but also Y", "which is correct" |
| action | User wants to DO something; decision-making, purchase, or step-by-step guidance | "how to", "best option for", "should I", "recommend" |

## Logical Dependency Options

| Type | When to Choose | Key Signal |
|------|---------------|------------|
| independent_parallel | Sub-questions are unrelated; can be answered in any order | Multiple disconnected topics in one query |
| chain_dependent | Must understand A before B; sequential knowledge build-up | "because of X, what is Y", "given that X, how does Y" |
| conflict_resolution | Sources are known or likely to disagree; need arbitration | Controversial topics, rapidly-changing facts, disputed claims |

## Task
Classify the following query and output JSON.

User Query: {{user_query}}
""".strip()


# =============================================================================
# Stage 1b: Constraints
# =============================================================================

CONSTRAINTS_PROMPT: str = """
You are a constraint extractor for a document retrieval system.
Analyze the user query and extract any explicit or implicit filtering constraints.

## Structured Metadata Constraints
Extract conditions on known metadata fields:
- field: one of "year", "category", "source"
- operator: one of "eq", "neq", "gt", "lt", "in", "range"
- value: string, integer, list of strings, or list of two integers [min, max]

Examples:
- "papers from 2023" → {"field": "year", "operator": "eq", "value": 2023}
- "after 2020" → {"field": "year", "operator": "gt", "value": 2020}
- "from Nature or Science" → {"field": "source", "operator": "in", "value": ["Nature", "Science"]}

## Content Pattern Constraints
Extract required or forbidden text patterns in the document content:
- pattern: the string pattern to match
- pattern_type: "exact_phrase", "regex", or "wildcard"
- scope: "full_text" or "title"
- is_negative: true if the document must NOT contain this pattern

## Output Rules
- If no constraints are found, return empty lists.
- Do not fabricate constraints not implied by the query.
- Current date context: {{current_date}}

User Query: {{user_query}}
""".strip()


# =============================================================================
# Stage 2: AgentPlan
# =============================================================================

AGENT_PLAN_PROMPT: str = """
You are an information planning engine for an agentic retrieval system.
Based on the user query and the identified cognitive strategy, decompose the query into structured information facets and define completion criteria.

## Cognitive Strategy (already classified)

**Cognitive Mode: {{cognitive_mode}}**
{{mode_guidance}}

**Logical Dependency: {{logical_dependency}}**
{{dependency_guidance}}

## Your Task

### 1. Information Facets
Decompose the query into a list of InformationFacet objects following the cognitive strategy guidance above.
Each facet must include:
- facet_id: "F1", "F2", ... (sequential)
- description: natural language description of the specific information need
- dependency: null, or the facet_id this facet depends on (only for chain_dependent)
- rubric: a RelevanceRubric specifying:
  - tolerance_level: "high" / "medium" / "low"
  - quality_preference: list of preferred document types
  - content_requirements: list of specific content criteria a document must meet

### 2. Completion Criteria
Define a single global CompletionCriteria:
- metric_type: one of "coverage" / "precision" / "consistency" / "actionability"
- threshold_description: when is the task considered done
- specific_conditions: checklist items for the Verification Agent

## Output
Return a valid AgentPlan JSON object.

User Query: {{user_query}}
""".strip()


# =============================================================================
# Stage 3: FacetExpansion
# =============================================================================

FACET_EXPANSION_PROMPT: str = """
You are a retrieval query expansion engine.
Given a single information facet from a retrieval plan, generate the retrieval parameters for this facet.

## Input Facet
- Facet ID: {{facet_id}}
- Description: {{facet_description}}
- Original User Query: {{user_query}}

## Your Task
Generate a FacetExpansion with three components:

1. **facet_query** (for dense/vector retrieval)
   A fluent, self-contained natural language sentence that fully captures the information need of this facet.
   Should be suitable as a standalone semantic search query.

2. **sparse_keywords** (for BM25 retrieval)
   A list of 3–6 high-signal keywords or short phrases specific to this facet.
   Prioritize domain-specific terms, proper nouns, and distinctive concepts.
   Avoid stopwords and overly generic terms.

3. **hypothetical_document** (HyDE — for enhanced dense retrieval)
   Write a short hypothetical document (2–4 sentences) that would perfectly answer this facet's information need.
   This will be embedded and used to find real documents with similar vector representations.

## Output
Return a valid FacetExpansion JSON object with facet_id set to "{{facet_id}}".
""".strip()
