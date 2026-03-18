"""
Backend Models - 模型模块初始化
"""

from .request import QueryRequest, ConfigUpdateRequest
from .response import (
    StageLogEntry,
    ExecutionStats,
    IntentOutput,
    CandidateDocOutput,
    RetrievalOutput,
    EvidenceOutput,
    AdjudicationOutput,
    GapAnalysisOutput,
    FinalReportOutput,
    StageResult,
    StreamEvent,
    PipelineResponse,
    ConfigResponse,
    HealthResponse,
)
from .inference import (
    EmbeddingRequest,
    EmbeddingResponse,
    RerankRequest,
    RerankResponse,
)

__all__ = [
    # Request models
    "QueryRequest",
    "ConfigUpdateRequest",
    # Response models
    "StageLogEntry",
    "ExecutionStats",
    "IntentOutput",
    "CandidateDocOutput",
    "RetrievalOutput",
    "EvidenceOutput",
    "AdjudicationOutput",
    "GapAnalysisOutput",
    "FinalReportOutput",
    "StageResult",
    "StreamEvent",
    "PipelineResponse",
    "ConfigResponse",
    "HealthResponse",
    # Inference models
    "EmbeddingRequest",
    "EmbeddingResponse",
    "RerankRequest",
    "RerankResponse",
]
