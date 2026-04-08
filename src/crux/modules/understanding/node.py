"""
意图理解节点 (Understanding Node)

四阶段流程：
  Stage 1a (并行): query → CognitiveState
  Stage 1b (并行): query → Constraints
  Stage 2:         query + CognitiveState → AgentPlan
  Stage 3 (并行):  每个 InformationFacet → FacetExpansion

最终合并为 IntentObject 存入 AgentState.intent。
"""

import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

from src.crux.context.builder import ContextBuilder
from src.crux.state.cognitive import CognitiveState
from src.crux.state.constraints import Constraints
from src.crux.state.plan import AgentPlan
from src.crux.state.expansion import FacetExpansion
from src.crux.state.intent import IntentObject
from src.crux.utils.base import BaseNode
from src.crux.utils.llm_client import LLMClient


class UnderstandingNode(BaseNode):
    """
    意图理解节点

    将用户自然语言查询转化为机器可执行的结构化 IntentObject。
    """

    name = "understand"
    name_cn = "意图理解"
    description = "解析用户意图，生成结构化 IntentObject"

    def __init__(self, config=None):
        super().__init__(config)
        self.llm_client = LLMClient(config)
        self.context_builder = ContextBuilder(config)

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        self.reset_logger()

        query = state["user_query"]
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")

        self.log(f"用户查询: {query}", details={"query": query})

        # ── Stage 1: 并行分类 ───────────────────────────────────────
        self.log("Stage 1: 认知分类 + 约束提取（并行）...")
        p_cognitive = self.context_builder.build_cognitive_state_prompt(query)
        p_constraints = self.context_builder.build_constraints_prompt(query, current_date)

        with ThreadPoolExecutor(max_workers=2) as executor:
            f_cog = executor.submit(self.llm_client.call_object, p_cognitive, CognitiveState)
            f_con = executor.submit(self.llm_client.call_object, p_constraints, Constraints)
            cognitive_state: CognitiveState = f_cog.result()
            constraints: Constraints = f_con.result()

        self.log(
            f"认知模式: {cognitive_state.cognitive_mode.value} | "
            f"逻辑依赖: {cognitive_state.logical_dependency.value}"
        )

        # ── Stage 2: 生成 AgentPlan ─────────────────────────────────
        self.log("Stage 2: 生成 AgentPlan...")
        p_plan = self.context_builder.build_agent_plan_prompt(query, cognitive_state)
        agent_plan: AgentPlan = self.llm_client.call_object(p_plan, AgentPlan)

        self.log(f"生成 {len(agent_plan.facets)} 个 InformationFacet")

        # ── Stage 3: 并行生成 FacetExpansion ────────────────────────
        self.log("Stage 3: 检索扩展（并行，每个 Facet 一次）...")
        expansion_prompts = [
            self.context_builder.build_facet_expansion_prompt(
                query, facet.facet_id, facet.description
            )
            for facet in agent_plan.facets
        ]
        expansions = self.llm_client.batch_call_object(
            expansion_prompts, FacetExpansion
        )

        # ── 合并 IntentObject ────────────────────────────────────────
        intent_obj = IntentObject(
            cognitive_state=cognitive_state,
            agent_plan=agent_plan,
            expansions=expansions,
            constraints=constraints,
        )

        self.log("意图理解完成", level="INFO")

        return self.build_result({
            "intent": intent_obj.model_dump(),
            "search_iteration": 0,
            "verified_evidence": [],
            "satisfied_facets": set(),
            "seen_doc_ids": set(),
        })
