"""Helpers shared by evaluation implementations."""

from __future__ import annotations

import copy
import json
from typing import Any, Dict, Iterable, List, Optional, Set

from src.crux.config import CruxConfig
from src.crux.evaluation.fixtures import StubLLMClient, extract_doc_id
from src.crux.evaluation.llm_judge import LLMJudgeVerdict, LLMEvaluationJudge


DEFAULT_SCHEMA_PATH = "data/paper_schema.yaml"


def build_config(overrides: Optional[Dict[str, Any]] = None) -> CruxConfig:
    """Create a Crux config suitable for local evaluation."""
    config = CruxConfig(
        data_source_type="json",
        data_source_path="data/ir_papers.json",
        schema_path=DEFAULT_SCHEMA_PATH,
        debug=False,
        mock_llm=False,
    )

    overrides = overrides or {}
    nested_sections = {"search", "judge", "llm", "retriever"}
    for key, value in overrides.items():
        if key in nested_sections:
            continue
        if hasattr(config, key):
            setattr(config, key, value)

    if "search" in overrides:
        for key, value in overrides["search"].items():
            setattr(config.search, key, value)

    if "judge" in overrides:
        for key, value in overrides["judge"].items():
            setattr(config.judge, key, value)

    if "llm" in overrides:
        for key, value in overrides["llm"].items():
            setattr(config.llm, key, value)

    if "retriever" in overrides:
        for key, value in overrides["retriever"].items():
            setattr(config.retriever, key, value)

    return config


def clean_stage_output(output: Dict[str, Any]) -> Dict[str, Any]:
    """Remove bulky internal keys from a stage output snapshot."""
    return {key: value for key, value in output.items() if not key.startswith("_")}


def merge_state(state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Merge node outputs into the running pipeline state."""
    merged = copy.deepcopy(state)

    for key, value in updates.items():
        if key in {"verified_evidence", "rejected_docs"}:
            merged[key] = list(merged.get(key, [])) + list(value)
        elif key in {"satisfied_facets", "seen_doc_ids"}:
            merged[key] = set(merged.get(key, set())) | set(value)
        elif key.startswith("_"):
            continue
        else:
            merged[key] = value

    return merged


def canonical_constraint(constraint: Dict[str, Any]) -> str:
    """Create a stable representation for constraint comparison."""
    field = constraint.get("field")
    operator = constraint.get("operator")
    value = json.dumps(constraint.get("value"), sort_keys=True, ensure_ascii=False)
    return f"{field}|{operator}|{value}"


def constraint_set(constraints: Iterable[Dict[str, Any]]) -> Set[str]:
    return {canonical_constraint(item) for item in constraints}


def sparse_keyword_set(intent: Dict[str, Any]) -> Set[str]:
    retrieval = intent.get("retrieval_execution", {})
    keywords = retrieval.get("sparse_keywords", [])
    return {
        str(item.get("term") if isinstance(item, dict) else item).strip().lower()
        for item in keywords
        if str(item.get("term") if isinstance(item, dict) else item).strip()
    }


def dense_query_set(intent: Dict[str, Any]) -> Set[str]:
    retrieval = intent.get("retrieval_execution", {})
    return {
        str(item).strip().lower()
        for item in retrieval.get("dense_queries", [])
        if str(item).strip()
    }


def allowed_constraint_fields(config: CruxConfig, case_fields: Optional[List[str]] = None) -> Set[str]:
    """Resolve allowed fields from fixture metadata or the configured schema."""
    if case_fields:
        return {field.strip() for field in case_fields if field and field.strip()}

    schema = config.get_schema_config()
    return {field.get("name", "").strip() for field in schema.fields if field.get("name")}


def evidence_map_by_doc(evidence_items: List[Dict[str, Any]]) -> Dict[str, str]:
    """Map evidence records to document ids."""
    result: Dict[str, str] = {}
    for item in evidence_items:
        result[extract_doc_id(item)] = str(item.get("content", ""))
    return result


def build_evaluation_judge(
    config: CruxConfig,
    case_stubs: Dict[str, Any],
    stub_key: str,
) -> LLMEvaluationJudge:
    """Create an evaluation judge backed by either a stub or the real LLMClient."""
    stub_response = case_stubs.get(stub_key)
    if stub_response is not None:
        return LLMEvaluationJudge(
            config=config,
            llm_client=StubLLMClient(call_json_with_object=[stub_response]),
        )
    return LLMEvaluationJudge(config=config)


def dimension_scores(verdict: LLMJudgeVerdict) -> Dict[str, float]:
    """Flatten LLM dimension scores into metric keys."""
    return {
        f"llm_{dimension.name}_score": float(dimension.score)
        for dimension in verdict.dimensions
    }
