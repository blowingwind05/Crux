"""
Backend Models - 响应模型定义

丰富的响应结构，支持前端展示需求
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============ 日志相关 ============

class StageLogEntry(BaseModel):
    """阶段日志条目"""
    level: Literal["INFO", "WARN", "ERROR", "DEBUG"] = "INFO"
    message: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    details: Optional[Dict[str, Any]] = None


class ExecutionStats(BaseModel):
    """执行统计信息"""
    total_candidates: int = 0
    verified_count: int = 0
    rejected_count: int = 0
    tokens_used: int = 0
    processing_time_ms: float = 0
    iteration_count: int = 0


# ============ 意图理解阶段 ============

class CognitiveStrategyOutput(BaseModel):
    """认知策略输出"""
    user_goal: str = "FACTUAL"
    reasoning_topology: str = "FLAT_LIST"
    depth_requirement: str = "SHALLOW"


class InformationFacetOutput(BaseModel):
    """信息面输出"""
    facet_id: str
    facet_type: str
    description: str
    dependency: Optional[str] = None


class ConstraintOutput(BaseModel):
    """约束条件输出"""
    structured_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    unstructured_content_patterns: List[Dict[str, Any]] = Field(default_factory=list)


class RetrievalStrategyOutput(BaseModel):
    """检索策略输出"""
    sparse_keywords: List[Dict[str, Any]] = Field(default_factory=list)
    dense_queries: List[str] = Field(default_factory=list)
    hypothetical_document: Optional[str] = None


class IntentOutput(BaseModel):
    """意图理解阶段输出"""
    user_goal: str
    cognitive_strategy: Optional[CognitiveStrategyOutput] = None
    constraints: ConstraintOutput = Field(default_factory=ConstraintOutput)
    information_facets: List[InformationFacetOutput] = Field(default_factory=list)
    retrieval_strategy: Optional[RetrievalStrategyOutput] = None
    keywords_bm25: List[str] = Field(default_factory=list)
    queries_vector: List[str] = Field(default_factory=list)
    rubric: str = ""


# ============ 检索召回阶段 ============

class CandidateDocOutput(BaseModel):
    """候选文档输出"""
    doc_id: str
    title: str
    abstract: str = ""
    score: float
    source: str = "hybrid"  # bm25, vector, hybrid
    authors: List[str] = Field(default_factory=list)
    year: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RetrievalOutput(BaseModel):
    """检索阶段输出"""
    candidates: List[CandidateDocOutput] = Field(default_factory=list)
    total_retrieved: int = 0
    retrieval_methods: List[str] = Field(default_factory=list)
    bm25_count: int = 0
    vector_count: int = 0
    filter_count: int = 0
    search_time_ms: float = 0


# ============ 深度研判阶段 ============

class EvidenceOutput(BaseModel):
    """证据输出"""
    doc_id: str
    content: str
    reason: str
    source: str = "unknown"
    relevance_score: float = 0.0
    facet_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AdjudicationOutput(BaseModel):
    """研判阶段输出"""
    verified_evidence: List[EvidenceOutput] = Field(default_factory=list)
    rejected_count: int = 0
    acceptance_rate: float = 0.0
    evaluated_count: int = 0
    evaluation_time_ms: float = 0


# ============ 缺口分析阶段 ============

class GapAnalysisOutput(BaseModel):
    """缺口分析输出"""
    status: Literal["sufficient", "insufficient"] = "sufficient"
    coverage_score: float = 0.0
    missing_facets: List[str] = Field(default_factory=list)
    suggested_queries: List[str] = Field(default_factory=list)
    iteration: int = 0
    max_iterations: int = 3
    should_loop_back: bool = False


# ============ 报告生成阶段 ============

class FinalReportOutput(BaseModel):
    """最终报告输出"""
    summary: str = ""
    key_findings: List[str] = Field(default_factory=list)
    evidence_chain: List[EvidenceOutput] = Field(default_factory=list)
    confidence_score: float = 0.0
    citations: List[str] = Field(default_factory=list)
    total_iterations: int = 0
    generation_time_ms: float = 0


# ============ 阶段结果包装 ============

class StageResult(BaseModel):
    """单个阶段的完整结果"""
    stage: str
    status: Literal["pending", "processing", "completed", "error"] = "pending"
    output: Optional[Dict[str, Any]] = None
    logs: List[StageLogEntry] = Field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: float = 0


# ============ 流式事件 ============

class StreamEvent(BaseModel):
    """SSE 流式事件"""
    type: Literal["start", "stage_start", "stage_log", "stage_complete", "iteration_start", "complete", "error"]
    stage: Optional[str] = None
    message: Optional[str] = None
    output: Optional[Dict[str, Any]] = None
    log: Optional[StageLogEntry] = None
    stats: Optional[ExecutionStats] = None
    iteration: int = 0
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


# ============ 完整响应 ============

class PipelineResponse(BaseModel):
    """管线完整响应（非流式）"""
    success: bool = True
    query: str
    stages: List[StageResult] = Field(default_factory=list)
    stats: ExecutionStats = Field(default_factory=ExecutionStats)
    final_report: Optional[FinalReportOutput] = None
    error: Optional[str] = None


class ConfigResponse(BaseModel):
    """配置响应"""
    data_source_type: str
    data_source_path: Optional[str] = None
    schema_path: Optional[str] = None
    mock_llm: bool
    debug: bool
    llm: Dict[str, Any] = Field(default_factory=dict)
    search: Dict[str, Any] = Field(default_factory=dict)
    judge: Dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "healthy"
    version: str = "0.1.0"
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
