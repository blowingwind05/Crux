"""
Crux Agent 状态定义

定义 LangGraph 工作流中流转的状态对象。
"""

from typing import TypedDict, List, Literal, Annotated
import operator


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
