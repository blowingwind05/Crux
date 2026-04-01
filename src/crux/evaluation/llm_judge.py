"""LLM-assisted semantic judging for evaluation."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, Field

from src.crux.config import CruxConfig
from src.crux.utils.llm_client import LLMClient


class EvaluationDimension(BaseModel):
    """One scored dimension in an LLM judgement."""

    name: str
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str


class LLMJudgeVerdict(BaseModel):
    """Structured result returned by the evaluation judge model."""

    overall_score: float = Field(ge=0.0, le=1.0)
    pass_recommendation: bool
    summary: str
    strengths: List[str] = Field(default_factory=list)
    issues: List[str] = Field(default_factory=list)
    dimensions: List[EvaluationDimension] = Field(default_factory=list)


class LLMEvaluationJudge:
    """Semantic evaluator built on top of the project's LLMClient."""

    def __init__(self, config: Optional[CruxConfig] = None, llm_client: Optional[Any] = None):
        self.config = config or CruxConfig()
        self.llm_client = llm_client or LLMClient(self.config)

    def evaluate(
        self,
        task_name: str,
        instructions: str,
        payload: Dict[str, Any],
        dimensions: Iterable[str],
    ) -> LLMJudgeVerdict:
        """Ask the LLM to judge one evaluation case semantically."""
        dimension_list = list(dimensions)
        prompt = self._build_prompt(task_name, instructions, payload, dimension_list)
        verdict = self.llm_client.call_json_with_object(
            prompt=prompt,
            response_object=LLMJudgeVerdict,
        )
        return self._normalize_dimensions(verdict, dimension_list)

    def _build_prompt(
        self,
        task_name: str,
        instructions: str,
        payload: Dict[str, Any],
        dimensions: List[str],
    ) -> str:
        serialized = json.dumps(payload, ensure_ascii=False, indent=2)
        dimension_text = ", ".join(dimensions)

        return f"""
You are an expert evaluator for the Crux Agentic RAG system.

Task: {task_name}

Evaluation instructions:
{instructions}

Score each required dimension on a 0.0-1.0 scale.
Required dimensions: {dimension_text}

Scoring rules:
- 0.9-1.0: excellent, fully satisfies the requirement
- 0.7-0.89: good, mostly satisfies the requirement with minor issues
- 0.4-0.69: partially satisfies the requirement, clear weaknesses remain
- 0.0-0.39: poor, requirement is not met

Important:
- Judge semantic correctness, not only exact string overlap.
- If wording differs but meaning is equivalent, score it positively.
- If there are schema violations or logic mistakes, mention them explicitly.
- Be conservative: do not give high scores without evidence.
- Output valid JSON only.

Return JSON with this exact structure:
{{
  "overall_score": 0.0,
  "pass_recommendation": true,
  "summary": "short summary",
  "strengths": ["..."],
  "issues": ["..."],
  "dimensions": [
    {{
      "name": "dimension_name",
      "score": 0.0,
      "reasoning": "why"
    }}
  ]
}}

Evaluation payload:
{serialized}
""".strip()

    def _normalize_dimensions(
        self,
        verdict: LLMJudgeVerdict,
        expected_dimensions: List[str],
    ) -> LLMJudgeVerdict:
        """Ensure all expected dimensions are present in the verdict."""
        existing = {dimension.name: dimension for dimension in verdict.dimensions}
        normalized: List[EvaluationDimension] = []

        for name in expected_dimensions:
            if name in existing:
                normalized.append(existing[name])
            else:
                normalized.append(
                    EvaluationDimension(
                        name=name,
                        score=0.0,
                        reasoning="Missing from LLM judgement output.",
                    )
                )

        verdict.dimensions = normalized
        return verdict
