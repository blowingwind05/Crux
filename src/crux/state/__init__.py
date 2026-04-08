"""Unified exports for structured state models."""

import operator
from typing import Annotated, Any, Dict, List, Literal, Set, TypedDict

from src.crux.state.cognitive import (
    CognitiveModeType,
    CognitiveState,
    LogicalDependencyType,
)
from src.crux.state.constraints import (
    Constraints,
    ContentConstraint,
    StructuredConstraint,
)
from src.crux.state.expansion import FacetExpansion
from src.crux.state.intent import IntentObject
from src.crux.state.plan import (
    AgentPlan,
    CompletionCriteria,
    InformationFacet,
    RelevanceRubric,
)
from src.crux.state.retrieval import (
    DocumentJudgment,
    FacetJudgments,
    FacetSufficiency,
    FacetSufficiencyResult,
)


class AgentState(TypedDict, total=False):
    """Top-level pipeline state flowing across the Crux graph."""

    user_query: str
    intent: Dict[str, Any]
    candidate_docs: List[dict]
    verified_evidence: Annotated[List[dict], operator.add]
    rejected_docs: Annotated[List[dict], operator.add]
    gap_analysis_result: Literal["sufficient", "insufficient"]
    search_iteration: int
    satisfied_facets: Annotated[Set[str], operator.or_]
    seen_doc_ids: Annotated[Set[str], operator.or_]
    final_report: str
    schema_path: str
    start_time: float


__all__ = [
    "AgentState",
    "CognitiveModeType",
    "LogicalDependencyType",
    "CognitiveState",
    "StructuredConstraint",
    "ContentConstraint",
    "Constraints",
    "FacetExpansion",
    "RelevanceRubric",
    "InformationFacet",
    "CompletionCriteria",
    "AgentPlan",
    "IntentObject",
    "DocumentJudgment",
    "FacetJudgments",
    "FacetSufficiency",
    "FacetSufficiencyResult",
]
