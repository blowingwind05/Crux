"""
上下文构建器

组合 context、超参、输入、环境变量进行 prompt 构造。
"""

import os
from typing import Optional, Dict, Any

from src.crux.config import CruxConfig
from src.crux.state.cognitive import CognitiveState, CognitiveModeType, LogicalDependencyType
from src.crux.modules.understanding.prompts import (
    COGNITIVE_STATE_PROMPT,
    CONSTRAINTS_PROMPT,
    AGENT_PLAN_PROMPT,
    FACET_EXPANSION_PROMPT,
)


# ========================
# 认知模式指导文本（指导 Facets 生成 + Rubric + Completion Criteria）
# ========================

_MODE_GUIDANCE: dict = {
    CognitiveModeType.EXPLORATORY: (
        "Psychological driver: curiosity / breadth-first.\n"
        "Facets: Generate MECE categories covering the topic broadly (e.g. {definition, principles, applications, challenges}).\n"
        "Rubric: High tolerance — shallow or survey-level documents are acceptable; prefer comprehensive overviews.\n"
        "Completion criteria: Coverage-oriented — task is done when every facet has at least one document."
    ),
    CognitiveModeType.DEEP_THINKING: (
        "Psychological driver: concreteness / depth-first.\n"
        "Facets: Drill down into specific dimensions (e.g. {mathematical formulation, experimental validation}).\n"
        "Rubric: Strict — require precise data, authoritative sources, and quantitative evidence.\n"
        "Completion criteria: Precision-oriented — must answer 'why' and 'how' with verifiable specifics."
    ),
    CognitiveModeType.VERIFICATION: (
        "Psychological driver: cognitive dissonance / confirmation-bias check.\n"
        "Facets: Adversarial dimensions (e.g. {supporting evidence, opposing evidence, meta-analysis / authoritative ruling}).\n"
        "Rubric: Authority-first — heavily prefer government sites, top-tier journals, official statements; filter personal blogs.\n"
        "Completion criteria: Consistency-oriented — task is done when a meta-source C explains WHY A and B conflict."
    ),
    CognitiveModeType.ACTION: (
        "Psychological driver: utility / behavioral intent.\n"
        "Facets: Comparative and evaluative dimensions (e.g. {option comparison, pricing, user pain points, step-by-step guide}).\n"
        "Rubric: Practicality-first — value real user reviews, spec comparisons, and actionable how-to content.\n"
        "Completion criteria: Actionability-oriented — sufficient to support a purchase decision or concrete action steps."
    ),
}

# ========================
# 逻辑依赖指导文本（只指导 Facets 结构 + Completion Criteria，不涉及 Rubric）
# ========================

_DEPENDENCY_GUIDANCE: dict = {
    LogicalDependencyType.INDEPENDENT_PARALLEL: (
        "Logic: A and B are unrelated — answer them in any order.\n"
        "Facets: Flat list; each facet is fully independent; set dependency to null for all.\n"
        "Completion criteria: Set coverage — task ends when ALL facets have been individually satisfied."
    ),
    LogicalDependencyType.CHAIN_DEPENDENT: (
        "Logic: Must know A before understanding B.\n"
        "Facets: Sequential steps — set the 'dependency' field to the prerequisite facet_id for each dependent facet.\n"
        "Completion criteria: Topological order — if the corpus lacks documents for facet A, the Verification Agent must "
        "trigger expansion for A before attempting B."
    ),
    LogicalDependencyType.CONFLICT_RESOLUTION: (
        "Logic: Source A says yes, source B says no — arbitration needed.\n"
        "Facets: Three arbitration dimensions: [supporting evidence, opposing evidence, third-party meta-analysis / authoritative ruling].\n"
        "Completion criteria: Arbitration mechanism — task is NOT done when A and B are found; "
        "task IS done when a meta-source C explains WHY A and B conflict "
        "(e.g. A is an older study, B is newer; or A applies to adults, B to children)."
    ),
}


class ContextBuilder:
    """
    上下文构建器

    负责:
    1. 根据 YAML 配置加载数据结构描述
    2. 组合环境变量、超参数和用户输入
    3. 构建完整的 prompt
    """

    def __init__(self, config: Optional[CruxConfig] = None):
        self.config = config or CruxConfig()

    def get_schema_description(self) -> str:
        """
        获取 Schema 描述文本

        从配置中加载 YAML schema 并生成描述文本

        Returns:
            Schema 描述的格式化文本
        """
        schema = self.config.get_schema_config()
        return schema.get_field_descriptions()

    # -------------------------
    # Stage 1a: CognitiveState
    # -------------------------

    def build_cognitive_state_prompt(self, query: str) -> str:
        return COGNITIVE_STATE_PROMPT.replace("{{user_query}}", query)

    # -------------------------
    # Stage 1b: Constraints
    # -------------------------

    def build_constraints_prompt(self, query: str, current_date: str) -> str:
        return (
            CONSTRAINTS_PROMPT
            .replace("{{user_query}}", query)
            .replace("{{current_date}}", current_date)
        )

    # -------------------------
    # Stage 2: AgentPlan
    # -------------------------

    def build_agent_plan_prompt(self, query: str, cognitive_state: CognitiveState) -> str:
        mode = cognitive_state.cognitive_mode
        dep = cognitive_state.logical_dependency
        return (
            AGENT_PLAN_PROMPT
            .replace("{{user_query}}", query)
            .replace("{{cognitive_mode}}", mode.value)
            .replace("{{logical_dependency}}", dep.value)
            .replace("{{mode_guidance}}", _MODE_GUIDANCE[mode])
            .replace("{{dependency_guidance}}", _DEPENDENCY_GUIDANCE[dep])
        )

    # -------------------------
    # Stage 3: FacetExpansion
    # -------------------------

    def build_facet_expansion_prompt(
        self, query: str, facet_id: str, facet_description: str
    ) -> str:
        return (
            FACET_EXPANSION_PROMPT
            .replace("{{user_query}}", query)
            .replace("{{facet_id}}", facet_id)
            .replace("{{facet_description}}", facet_description)
        )

    # -------------------------
    # 通用工具方法
    # -------------------------

    def build_prompt(
        self,
        template: str,
        **kwargs
    ) -> str:
        """
        通用 prompt 构建

        Args:
            template: prompt 模板
            **kwargs: 模板变量

        Returns:
            完整的 prompt
        """
        if "{{schema_description}}" in template:
            kwargs["schema_description"] = self.get_schema_description()

        if "{{env_context}}" in template:
            kwargs["env_context"] = self._build_env_context()

        result = template
        for key, value in kwargs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))

        return result

    def _build_env_context(self) -> str:
        """构建环境上下文"""
        env_vars = {
            "DEBUG": os.getenv("CRUX_DEBUG", "false"),
            "MAX_ITERATIONS": str(self.config.search.max_iterations),
            "TOP_K": str(self.config.search.top_k),
        }

        lines = ["## 环境配置"]
        for k, v in env_vars.items():
            lines.append(f"- {k}: {v}")

        return "\n".join(lines)
