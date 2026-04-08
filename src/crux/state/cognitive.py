"""
认知状态定义 (Cognitive State)

由 understand 模块第一阶段从 query 分类得出，包含两个维度：
1. cognitive_mode：认知模式（整体策略）—— 探索 / 深思 / 验证 / 行动
2. logical_dependency：逻辑依赖（逻辑结构）—— 独立并行 / 链式依赖 / 冲突消解

每个维度只存储分类结果（枚举值），具体的 Facets/Rubric/Criteria 生成指导由 prompt template 承载。
"""

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


class CognitiveModeType(str, Enum):
    """认知模式类型"""
    EXPLORATORY = "exploratory"      # 探索模式：好奇心驱动，广度优先
    DEEP_THINKING = "deep_thinking"  # 深思模式：具体化，深度优先
    VERIFICATION = "verification"    # 验证模式：认知失调检查，确认偏误检测
    ACTION = "action"                # 行动模式：效用驱动，行为意向


class LogicalDependencyType(str, Enum):
    """逻辑依赖类型"""
    INDEPENDENT_PARALLEL = "independent_parallel"  # 独立并行：A 和 B 互不影响
    CHAIN_DEPENDENT = "chain_dependent"            # 链式依赖：只有知道 A 才能理解 B
    CONFLICT_RESOLUTION = "conflict_resolution"    # 冲突消解：A 说是，B 说否


class CognitiveState(BaseModel):
    """
    认知状态 —— understand 模块第一阶段的输出，对 query 的认知特征分类。

    后续由 understand 模块第二阶段结合 prompt template 中各类型的生成指导，
    产出 IntentObject（Facets + Rubric + Criteria）。
    """
    cognitive_mode: Annotated[CognitiveModeType, Field(
        description=(
            "认知模式：根据查询的语言特征判断。"
            "'是什么/为什么/怎么回事' → exploratory；"
            "'具体原理/底层实现/数学推导' → deep_thinking；"
            "'真的假的/有没有依据/哪个说法对' → verification；"
            "'怎么选/怎么做/推荐什么' → action。"
        )
    )]
    logical_dependency: Annotated[LogicalDependencyType, Field(
        description=(
            "逻辑依赖：根据信息点之间的关系判断。"
            "多个互不相关的子问题 → independent_parallel；"
            "某概念是理解另一概念的前提 → chain_dependent；"
            "用户提到矛盾说法或有争议事实 → conflict_resolution。"
        )
    )]
