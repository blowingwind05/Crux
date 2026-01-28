from typing import TypedDict, List, Literal, Optional, Any
from pydantic import BaseModel, Field
import operator
from typing import Annotated

# --- Pydantic 模型 (用于 LLM 结构化输出) ---

class StructuredConstraint(BaseModel):
    field: str
    operator: str
    value: Any

class IntentObject(BaseModel):
    """DeepIntentObject 的精简版定义"""
    user_goal: str = Field(description="用户目标: INVESTIGATIVE | FACTUAL etc.")
    constraints: List[StructuredConstraint] = Field(description="硬性元数据过滤条件")
    keywords_bm25: List[str] = Field(description="用于稀疏检索的关键词")
    queries_vector: List[str] = Field(description="用于向量检索的描述性语句")
    rubric: str = Field(description="用于后续研判的相关性准则")
    missing_info_gap: Optional[str] = Field(None, description="当前的缺口描述")

# --- LangGraph 状态定义 ---

class AgentState(TypedDict):
    # 1. 原始输入
    user_query: str
    
    # 2. 意图理解结果 (模块一)
    intent: dict # 存储 IntentObject.model_dump()
    
    # 3. 召回结果 (模块二)
    candidate_docs: List[dict] 
    
    # 4. 研判证据 (模块三) - 使用 add 操作符支持追加
    verified_evidence: Annotated[List[dict], operator.add]
    
    # 5. 状态控制 (模块四)
    gap_analysis_result: Literal["sufficient", "insufficient"]
    search_iteration: int # 迭代计数器
    
    # 6. 最终输出
    final_report: str
