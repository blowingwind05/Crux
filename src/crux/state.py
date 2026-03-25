"""
Crux Agent 状态定义

定义 LangGraph 工作流中流转的状态对象。
"""

import operator
from typing import List, Optional, Any, TypedDict, Literal, Annotated, Union, Dict

from pydantic import BaseModel, Field

"""
意图理解模块 - Pydantic 模型定义

定义 IntentObject 及相关结构。
"""


class CognitiveStrategy(BaseModel):
    user_goal: Annotated[
        Literal["INVESTIGATIVE", "FACTUAL", "DEBUGGING", "COMPARATIVE"],
        Field(default="FACTUAL", description="用户目标类型：INVESTIGATIVE(调查分析)、FACTUAL(事实查询)、DEBUGGING(问题排查)、COMPARATIVE(对比分析)")
    ]
    reasoning_topology: Annotated[
        Literal["CAUSAL_CHAIN", "TEMPORAL_SEQUENCE", "FLAT_LIST"],
        Field(default="FLAT_LIST", description="推理结构：CAUSAL_CHAIN(因果链)、TEMPORAL_SEQUENCE(时间序列)、FLAT_LIST(无结构列表)")
    ]
    depth_requirement: Annotated[
        Literal["DEEP", "SHALLOW"],
        Field(default="SHALLOW", description="信息深度需求：DEEP(深入分析)、SHALLOW(浅层信息)")
    ]


class StructuredConstraint(BaseModel):
    field: Annotated[
        Literal["year", "category", "source"],
        Field(description="字段名，例如 year、category、source，用于结构化过滤")
    ]
    operator: Annotated[
        Literal["eq", "neq", "gt", "lt", "in", "range"],
        Field(description="比较操作符：eq(等于)、neq(不等于)、gt(大于)、lt(小于)、in(集合包含)、range(区间)")
    ]
    value: Annotated[
        Union[str, int, list[str],
            list[int]
        ],
        Field(description="约束值，例如 2020、['AI','ML']、[2010,2020]")]
    rationale: Annotated[
        Optional[str],
        Field(default=None, description="设置该约束的原因或意图（用于解释性或调试）")
    ]


class ContentConstraint(BaseModel):
    pattern: Annotated[
        str,
        Field(description="匹配模式，可以是精确短语或re正则表达式，例如 'climate change' 或 '^F\d+$'")
    ]
    pattern_type: Annotated[
        Literal["regex", "exact_phrase", "wildcard"],
        Field(description="匹配类型：regex(正则表达式)、exact_phrase(精确短语匹配)、wildcard(通配符匹配)")
    ]
    scope: Annotated[
        Literal["full_text", "title"],
        Field(description="匹配范围：full_text(全文)、title(标题)")
    ]
    is_negative: Annotated[
        bool,
        Field(description="是否为排除条件：true 表示排除匹配该模式的内容")
    ]
    rationale: Annotated[
        Optional[str],
        Field(default=None, description="设置该约束的原因或意图（用于解释性或调试）")
    ]

class Constraints(BaseModel):
    structured_metadata: Annotated[
        List[StructuredConstraint],
        Field(default_factory=list, description="结构化元数据约束列表（用于数据库字段过滤）")
    ]
    unstructured_content_patterns: Annotated[
        List[ContentConstraint],
        Field(default_factory=list, description="非结构化文本匹配约束列表（用于全文检索过滤或增强）")
    ]


class InformationFacet(BaseModel):
    facet_id: Annotated[
        str,
        Field(pattern=r'^F\d+$', description="子需求唯一标识，必须为 F 开头加数字，例如 F1、F2")
    ]
    facet_type: Annotated[
        Literal["EVIDENCE", "CAUSE", "CONSEQUENCE", "DEFINITION", "SOLUTION"],
        Field(description="子需求类型：EVIDENCE(证据)、CAUSE(原因)、CONSEQUENCE(结果/影响)、DEFINITION(定义)、SOLUTION(解决方案)")
    ]
    description: Annotated[
        str,
        Field(description="该子需求的自然语言描述，应清晰说明需要获取的信息内容")
    ]
    dependency: Annotated[
        Optional[str],
        Field(default=None, description="依赖的前置 facet_id，例如 F1；若无依赖则为 None")
    ]

class SparseKeyword(BaseModel):
    term: Annotated[
        str,
        Field(description="用于稀疏检索（关键词匹配）的关键词")
    ]
    weight: Annotated[
        float,
        Field(default=1.0, description="关键词权重，用于控制检索重要性（默认 1.0）")
    ]

class RetrievalExecution(BaseModel):
    sparse_keywords: Annotated[
        List[SparseKeyword],
        Field(default_factory=list, description="稀疏检索关键词列表（用于 BM25 等关键词检索）")
    ]
    dense_queries: Annotated[
        List[str],
        Field(default_factory=list, description="语义检索查询列表（用于向量检索）")
    ]
    hypothetical_document: Annotated[
        Optional[str],
        Field(default=None, description="HyDE 假设文档，用于增强语义检索效果（生成一段假想答案）")
    ]


class JudgementRubric(BaseModel):
    relevance_threshold: Annotated[
        Literal["HIGH", "MEDIUM"],
        Field(default="MEDIUM", description="相关性阈值：HIGH(严格)、MEDIUM(中等)")
    ]
    criteria_positive: Annotated[
        str,
        Field(default="", description="判定为相关的标准，应具体说明哪些内容是有价值的")
    ]
    criteria_negative: Annotated[
        str,
        Field(default="", description="排除标准，应明确哪些内容需要过滤")
    ]

# =========================
# 顶层 IntentObject
# =========================

class IntentObject(BaseModel):
    cognitive_strategy: Annotated[
        CognitiveStrategy,
        Field(description="认知策略，定义用户意图类型、推理方式和深度需求")
    ]

    constraints: Annotated[
        Constraints,
        Field(default_factory=Constraints, description="约束条件，包括结构化过滤和文本匹配规则")
    ]

    information_facets: Annotated[
        List[InformationFacet],
        Field(description="信息需求拆解列表，将复杂问题拆解为多个子问题")
    ]

    retrieval_execution: Annotated[
        RetrievalExecution,
        Field(description="检索执行策略，包括关键词、语义查询和 HyDE 文档")
    ]

    judgement_rubric: Annotated[
        JudgementRubric,
        Field(description="结果评估标准，用于判断检索结果是否相关及提取证据")
    ]

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
