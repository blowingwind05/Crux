"""
Crux Agent 状态定义

定义 LangGraph 工作流中流转的状态对象。
"""

import operator
from typing import List, Optional, Any
from typing import TypedDict, Literal, Annotated

from pydantic import BaseModel, Field

"""
意图理解模块 - Pydantic 模型定义

定义 IntentObject 及相关结构。
"""


class StructuredConstraint(BaseModel):
    """结构化元数据约束条件"""
    field: str = Field(description="字段名，如 year, category, source 等")
    operator: str = Field(description="操作符: eq, neq, gt, lt, gte, lte, in, range")
    value: Any = Field(description="约束值")


class ContentPattern(BaseModel):
    """非结构化内容匹配模式"""
    pattern: str = Field(description="匹配模式：正则表达式或精确短语")
    pattern_type: str = Field(default="exact_phrase", description="模式类型: regex, exact_phrase, wildcard")
    scope: str = Field(default="full_text", description="搜索范围: full_text, title, abstract")
    is_negative: bool = Field(default=False, description="是否为排除条件")
    rationale: Optional[str] = Field(default=None, description="设置该约束的原因")


class CognitiveStrategy(BaseModel):
    """认知策略"""
    user_goal: str = Field(description="用户目标: INVESTIGATIVE | FACTUAL | DEBUGGING | COMPARATIVE")
    reasoning_topology: str = Field(default="FLAT_LIST",
                                    description="推理拓扑: CAUSAL_CHAIN | TEMPORAL_SEQUENCE | FLAT_LIST")
    depth_requirement: str = Field(default="SHALLOW", description="深度需求: DEEP | SHALLOW")


class InformationFacet(BaseModel):
    """信息面 - 子需求"""
    facet_id: str = Field(description="唯一标识，如 F1, F2")
    facet_type: str = Field(description="类型: CAUSE | CONSEQUENCE | DEFINITION | SOLUTION | EVIDENCE")
    description: str = Field(description="自然语言描述")
    dependency: Optional[str] = Field(default=None, description="依赖的前置 facet_id")


class SparseKeyword(BaseModel):
    """稀疏检索关键词"""
    term: str = Field(description="关键词")
    weight: float = Field(default=1.0, description="权重")


class RetrievalExecution(BaseModel):
    """检索执行策略"""
    sparse_keywords: List[SparseKeyword] = Field(default_factory=list, description="稀疏检索关键词及权重")
    dense_queries: List[str] = Field(default_factory=list, description="向量检索的语义查询")
    hypothetical_document: Optional[str] = Field(default=None, description="HyDE 假设文档")


class JudgementRubric(BaseModel):
    """研判标准"""
    relevance_threshold: str = Field(default="MEDIUM", description="相关性阈值: HIGH | MEDIUM")
    criteria_positive: str = Field(default="", description="正向判断标准")
    criteria_negative: str = Field(default="", description="排除标准")
    evidence_extraction_template: Optional[dict] = Field(default=None, description="证据提取模板")


class IntentObject(BaseModel):
    """深度意图对象 - LLM 输出的结构化意图（匹配 INTENT_PARSING_PROMPT 输出格式）"""
    
    # 认知策略
    cognitive_strategy: CognitiveStrategy = Field(
        default_factory=lambda: CognitiveStrategy(user_goal="FACTUAL"),
        description="认知策略"
    )

    # 约束条件
    constraints: dict = Field(
        default_factory=lambda: {"structured_metadata": [], "unstructured_content_patterns": []},
        description="硬性约束条件"
    )

    # 信息面列表
    information_facets: List[InformationFacet] = Field(default_factory=list, description="信息面列表")

    # 检索执行策略
    retrieval_execution: RetrievalExecution = Field(
        default_factory=RetrievalExecution,
        description="检索执行策略"
    )

    # 研判标准
    judgement_rubric: JudgementRubric = Field(
        default_factory=JudgementRubric,
        description="研判标准"
    )


"""
全局State
"""


class AgentState(TypedDict):
    """Agent 工作流状态"""

    # 1. 原始输入
    user_query: str

    # 2. 意图理解结果 (模块一)
    intent: dict  # 存储 IntentObject.model_dump()
    intent_object: dict  # 兼容前端

    # 3. 召回结果 (模块二)
    candidate_docs: List[dict]

    # 4. 研判证据 (模块三) - 使用 add 操作符支持追加
    verified_evidence: Annotated[List[dict], operator.add]
    rejected_docs: List[dict]  # 被拒绝的文档列表

    # 5. 状态控制 (模块四)
    gap_analysis_result: Literal["sufficient", "insufficient"]
    search_iteration: int  # 迭代计数器

    # 6. 最终输出
    final_report: str

    # 7. 元信息（可选）
    schema_path: str  # YAML schema 配置文件路径
    start_time: float  # 开始时间戳
