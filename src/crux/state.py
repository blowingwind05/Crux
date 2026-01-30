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


class IntentObject(BaseModel):
    """深度意图对象 - LLM 输出的结构化意图"""
    user_goal: str = Field(description="用户目标: INVESTIGATIVE | FACTUAL | DEBUGGING | COMPARATIVE")

    # 约束条件
    constraints: dict = Field(
        default_factory=lambda: {"structured_metadata": [], "unstructured_content_patterns": []},
        description="硬性约束条件"
    )

    # 检索相关
    keywords_bm25: List[str] = Field(default_factory=list, description="用于稀疏检索的关键词")
    queries_vector: List[str] = Field(default_factory=list, description="用于向量检索的描述性语句")

    # 研判相关
    rubric: str = Field(default="文档内容相关即可", description="用于后续研判的相关性准则")

    # 缺口分析
    missing_info_gap: Optional[str] = Field(default=None, description="当前的信息缺口描述")

    # 扩展字段
    cognitive_strategy: Optional[dict] = Field(default=None, description="认知策略")
    information_facets: Optional[List[dict]] = Field(default=None, description="信息面列表")


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

    # 5. 状态控制 (模块四)
    gap_analysis_result: Literal["sufficient", "insufficient"]
    search_iteration: int  # 迭代计数器

    # 6. 最终输出
    final_report: str

    # 7. 元信息（可选）
    schema_type: str  # 当前使用的 schema 类型
    start_time: float  # 开始时间戳
