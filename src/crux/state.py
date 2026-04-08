"""
Crux Agent 工作流状态定义

LangGraph 工作流中流转的顶层状态对象。
意图理解相关的模型定义见 crux.state 子包。
"""

import operator
from typing import Annotated, Any, Dict, List, Literal, Set, TypedDict


class AgentState(TypedDict):
    """Agent 工作流状态"""

    # 1. 原始输入
    user_query: str

    # 2. 意图理解结果 (understand 模块) - IntentObject.model_dump()
    #    包含 cognitive_state / agent_plan / expansions / constraints
    intent: Dict[str, Any]

    # 3. 召回结果 (模块二)
    candidate_docs: List[dict]

    # 4. 研判证据 (模块三) - 使用 add 操作符支持追加
    verified_evidence: Annotated[List[dict], operator.add]
    rejected_docs: Annotated[List[dict], operator.add]

    # 5. 状态控制 (模块四)
    gap_analysis_result: Literal["sufficient", "insufficient"]
    search_iteration: int

    # 已满足的 Facet ID 集合（operator.or_ 执行 set 并集归约，跨迭代累积）
    satisfied_facets: Annotated[Set[str], operator.or_]

    # 已研判过的文档 ID 集合（同上，避免跨迭代重复研判）
    seen_doc_ids: Annotated[Set[str], operator.or_]

    # 6. 最终输出
    final_report: str

    # 7. 元信息（可选）
    schema_path: str
    start_time: float
