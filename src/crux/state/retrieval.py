"""
研判结果模型

Judge 模块的 LLM 输出结构，用于 call_object 的 response_object。
"""

from typing import Annotated, List, Literal

from pydantic import BaseModel, Field


class DocumentJudgment(BaseModel):
    """单个文档的研判结果"""
    doc_id: Annotated[str, Field(description="文档唯一标识，与输入文档的 doc_id 对应")]
    summary: Annotated[str, Field(description="1-2 句话概括文档内容")]
    relevance_level: Annotated[
        Literal["high", "medium", "low", "irrelevant"],
        Field(description="相关性程度：high/medium/low/irrelevant")
    ]
    reason: Annotated[str, Field(description="结合 Rubric 说明判断依据")]


class FacetJudgments(BaseModel):
    """单个 Facet 所有候选文档的研判结果（LLM 一次调用的输出）"""
    judgments: Annotated[List[DocumentJudgment], Field(
        description="按输入文档顺序返回，每个文档对应一个 DocumentJudgment"
    )]


class FacetSufficiency(BaseModel):
    """单个 Facet 的充足性评估结果"""
    facet_id: Annotated[str, Field(description="Facet 唯一标识，与输入 Facet 的 facet_id 对应")]
    satisfied: Annotated[bool, Field(description="当前证据是否满足该 Facet 的 CompletionCriteria")]
    reason: Annotated[str, Field(description="1 句话说明满足或不满足的原因")]


class FacetSufficiencyResult(BaseModel):
    """所有待评估 Facet 的充足性评估汇总（GapAnalysisNode 的 LLM 输出）"""
    overall_sufficient: Annotated[bool, Field(
        description="所有 Facet 均满足时为 true；节点会根据 facets 列表自行兜底计算"
    )]
    facets: Annotated[List[FacetSufficiency], Field(
        description="每个待评估 Facet 对应一个 FacetSufficiency"
    )]

