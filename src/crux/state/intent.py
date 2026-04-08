"""Structured intent object emitted by the understanding stage."""

from typing import Annotated, List

from pydantic import BaseModel, Field

from src.crux.state.cognitive import CognitiveState
from src.crux.state.constraints import Constraints
from src.crux.state.expansion import FacetExpansion
from src.crux.state.plan import AgentPlan


class IntentObject(BaseModel):
    """Aggregate output from the understanding stage."""

    cognitive_state: Annotated[
        CognitiveState,
        Field(description="Cognitive mode and dependency pattern for the query."),
    ]
    agent_plan: Annotated[
        AgentPlan,
        Field(description="Facet plan, relevance rubrics, and completion criteria."),
    ]
    expansions: Annotated[
        List[FacetExpansion],
        Field(description="Per-facet retrieval expansions."),
    ]
    constraints: Annotated[
        Constraints,
        Field(description="Structured and unstructured retrieval constraints."),
    ]
