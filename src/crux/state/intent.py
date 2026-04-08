"""
Intent Object 定义

understand 模块的最终输出，整合四阶段 LLM 调用的结果：
- cognitive_state：认知分类（Stage 1a）
- constraints：过滤约束（Stage 1b）
- agent_plan：信息分面 + 完成标准（Stage 2）
- expansions：每个 Facet 的检索扩展参数（Stage 3）
"""

from typing import Annotated, List

from pydantic import BaseModel, Field

from crux.state.cognitive import CognitiveState
from crux.state.plan import AgentPlan
from crux.state.expansion import FacetExpansion
from crux.state.constraints import Constraints


class IntentObject(BaseModel):
    """
    understand 模块的最终输出，组合四阶段 LLM 调用的结果。

    下游模块按需取用：
    - Expansion Agent    → expansions[*]（facet_query + sparse_keywords + hyde）
    - Justification Agent → agent_plan.facets[*].rubric
    - Verification Agent  → agent_plan.criteria
    - 数据加载层          → constraints
    """
    cognitive_state: Annotated[CognitiveState, Field(
        description="认知状态：认知模式 + 逻辑依赖，指导 AgentPlan 的生成策略"
    )]
    agent_plan: Annotated[AgentPlan, Field(
        description="Agent Plan：信息分面列表（含 RelevanceRubric）+ 全局完成标准"
    )]
    expansions: Annotated[List[FacetExpansion], Field(
        description="Facet 检索扩展列表，与 agent_plan.facets 1-to-1 对应（按 facet_id 匹配）"
    )]
    constraints: Annotated[Constraints, Field(
        description="过滤约束：结构化元数据条件 + 内容模式匹配规则"
    )]
