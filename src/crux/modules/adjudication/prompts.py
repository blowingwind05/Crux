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

SINGLE_ADJUDICATION_TEMPLATE = """
Role: 
You are the **Critical Judge**.

Given:
- The User Question
{query}
- Rubric
{rubric}
- Document Content
{doc_content}

Tasks:
1. Classify the document into exactly one category:
   - "Perfectly Relevant"  — strongly satisfies the required rubric
   - "Somewhat Relevant"   — offers partial support, context or background for the rubric
   - "Not Relevant"        — does not meaningfully support the rubric

2. Give the reason for the document's classification.

3. Assign a relevance_score between 0.0 and 1.0:
   - "Perfectly Relevant"  → 0.8–1.0
   - "Somewhat Relevant"   → 0.4–0.79
   - "Not Relevant"        → 0.0–0.39

4. Extract the specific evidence (quote or summary),
   - Return [] if the document is classified as "Not Relevant"
   - Return a list of evidence if the document is classified as "Perfectly Relevant" or "Somewhat Relevant"
   - Focus on content that supports the rubric

Output format (only JSON, nothing else): 
{{
    "relevance": "Perfectly Relevant|Somewhat Relevant|Not Relevant",
    "relevance_score": 0.85,
    "reason": "One short explanation of the classification",
    "evidence": ["quote or summary 1", "quote or summary 2", ...]
}} 
"""

MULTI_ADJUDICATION_TEMPLATE = """
Role: 
You are the **Critical Judge**.

Given:
- The User Question
{query}
- Rubric
{rubric}
- Document Contents
{doc_contents}

Tasks:
1. Classify each document into exactly one category:
   - "Perfectly Relevant"  — strongly satisfies the required rubric
   - "Somewhat Relevant"   — offers partial support, context or background for the rubric
   - "Not Relevant"        — does not meaningfully support the rubric

2. Give the reason for each document's classification.

3. Assign a relevance_score between 0.0 and 1.0 for each document:
   - "Perfectly Relevant"  → 0.8–1.0
   - "Somewhat Relevant"   → 0.4–0.79
   - "Not Relevant"        → 0.0–0.39

4. Extract the specific evidence (quote or summary),
   - Return [] if the document is classified as "Not Relevant"
   - Return a list of evidence if the document is classified as "Perfectly Relevant" or "Somewhat Relevant"
   - Focus on content that supports the rubric

Output format (only JSON, nothing else): 
{{
  "judgements": [
    {{
      "document_id": 1,
      "relevance": "Perfectly Relevant|Somewhat Relevant|Not Relevant",
      "relevance_score": 0.85,
      "reason": "One short explanation of the classification",
      "evidence": ["quote or summary 1", "quote or summary 2", ...]
    }},
  ]
}}
"""

def get_single_adjudication_prompt(query: str, rubric: str, doc_content: str) -> str:
    """构建单个研判 prompt"""
    return SINGLE_ADJUDICATION_TEMPLATE.format(query=query, rubric=rubric, doc_content=doc_content)

def get_multi_adjudication_prompt(query: str, rubric: str, doc_contents: list[str]) -> str:
    """构建批量研判 prompt"""
    doc_contents = [
        f"Doc[{i+1}]:{content}\n"
        for i, content in enumerate(doc_contents)
    ]
    return MULTI_ADJUDICATION_TEMPLATE.format(query=query, rubric=rubric, doc_contents=doc_contents)
