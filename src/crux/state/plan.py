"""
Agent Plan 定义

由 understand 模块根据 query 和 CognitiveState 生成，是 model 的直接输出。
包含三个核心要素：
- Information Facets（地图）：对问题空间的结构化拆解，为 Expansion Agent 提供探索路线
- Relevance Rubric（尺子）：每个 Facet 专属，定义"什么样的文档才算有用"，为 Justification Agent 提供筛选标准
- Completion Criteria（终点）：定义"当什么条件满足时任务完成"，为 Verification Agent 提供决策准则
"""

from typing import Annotated, List, Literal, Optional

from pydantic import BaseModel, Field


# ========================
# Relevance Rubric（尺子）
# ========================

class RelevanceRubric(BaseModel):
    """
    相关性评判标准（尺子）—— 定义"什么样的文档才算是有用的"，为 Justification Agent 提供筛选标准。
    """
    tolerance_level: Annotated[str, Field(
        description="包容性等级：high(高容忍，偏好综述) / medium(中等) / low(低容忍，严格要求精确来源)"
    )]
    quality_preference: Annotated[list[str], Field(
        description="质量偏好：偏好什么类型的文档，例如 ['学术论文', '官方文档'] 或 ['真实评价', '参数对比']"
    )]
    content_requirements: Annotated[list[str], Field(
        description="具体内容要求：文档必须满足哪些内容特征才算与该 InformationFacet 相关"
    )]


# ========================
# Information Facets（地图）
# ========================

class InformationFacet(BaseModel):
    """
    信息分面（地图）—— 对问题空间的结构化拆解，为 Expansion Agent 提供探索路线。

    每个 InformationFacet 代表当前 query 的一个独立信息需求，并携带自己的 RelevanceRubric（1-to-1）。
    """
    facet_id: Annotated[str, Field(description="分面唯一标识，如 F1、F2，格式为 F+数字")]
    description: Annotated[str, Field(description="该分面的自然语言描述，清晰说明需要获取什么信息")]
    dependency: Annotated[Optional[str], Field(
        default=None,
        description="依赖的前置 facet_id（链式依赖时使用，为 None 表示无依赖）"
    )]
    rubric: Annotated[RelevanceRubric, Field(
        description="该分面专属的相关性评判标准，为 Justification Agent 提供筛选依据"
    )]


# ========================
# Completion Criteria（终点）
# ========================

class CompletionCriteria(BaseModel):
    """
    完成标准（终点）—— 定义"当什么条件满足时，认为任务完成"，为 Verification Agent 提供决策准则。

    作用于全局：判断哪些 Facet 已被满足，是否可以终止检索循环。
    """
    metric_type: Annotated[Literal["coverage", "precision", "consistency", "actionability"], Field(
        description="度量类型：coverage(覆盖率) / precision(精确度) / consistency(逻辑一致性) / actionability(可行动性)"
    )]
    threshold_description: Annotated[str, Field(
        description="完成条件的自然语言描述，说明达到什么程度即可终止"
    )]
    specific_conditions: Annotated[list[str], Field(
        description="具体的完成条件列表，逐条列出 Verification Agent 需要检查的判断项"
    )]


# ========================
# Agent Plan（顶层）
# ========================

class AgentPlan(BaseModel):
    """
    Agent Plan —— understand 模块的直接输出，由 model 根据 query 和 CognitiveState 生成。

    - facets：信息分面列表（地图），每个分面含专属 RelevanceRubric（尺子）
    - criteria：完成标准（终点），Verification Agent 的全局终止判据
    """
    facets: Annotated[List[InformationFacet], Field(
        description="信息分面列表（地图）：问题空间的结构化拆解，每个分面含专属 RelevanceRubric（尺子）"
    )]
    criteria: Annotated[CompletionCriteria, Field(
        description="完成标准（终点）：Verification Agent 的全局终止判据"
    )]
