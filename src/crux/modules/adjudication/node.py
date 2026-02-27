"""
深度研判节点 (Adjudication Node)

负责人: Jun Yang

功能:
- 根据研判准则评估文档相关性
- 提取高价值证据
- 过滤语义相似但事实无关的噪音
"""

import time
from typing import Dict, Any, List

from src.crux.utils.base import BaseNode
from src.crux.utils.llm_client import LLMClient
from src.crux.modules.adjudication.prompts import get_single_adjudication_prompt


class AdjudicationNode(BaseNode):
    """
    准则引导的深度研判节点

    对每个候选文档进行证据级评估:
    1. 轻量筛选 - 快速淘汰明显不相关文档
    2. 证据级评估 - 利用 LLM 根据准则判断相关性
    """

    name = "judge"
    name_cn = "深度研判"
    description = "深度研判候选文档，提取证据"

    def __init__(self, config=None):
        super().__init__(config)
        self.llm_client = LLMClient(config)
        # 初始化配置
        self.use_parallel = self.config.judge.use_parallel
        self.max_workers = self.config.judge.max_workers
        self.max_retry = self.config.judge.max_retry

    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        对候选文档进行深度研判

        使用 single prompt，每次输入一个文档：
        - use_parallel=True: 使用 batch_call_json 并行调用多个 prompt
        - use_parallel=False: 使用 call_json 串行调用多个 prompt

        Args:
            state: 包含 candidate_docs, intent 的状态

        Returns:
            包含 verified_evidence 的更新
        """
        self.reset_logger()

        docs = state["candidate_docs"]
        intent = state["intent"]
        rubric = self._get_rubric(intent)
        query = state.get("user_query", "")

        new_evidence = []
        rejected_docs = []  # 收集被拒绝的文档
        rejected_count = 0

        self.log("开始深度研判流程...")
        self.log(f"待研判文档: {len(docs)} 篇")
        self.log(f"研判准则: {rubric[:100]}..." if len(rubric) > 100 else f"研判准则: {rubric}")
        self.log(f"并行模式: {self.use_parallel}")

        # ==================== 步骤 1: 构建 prompts ====================
        # single prompt: 每个文档一个 prompt
        prompts = [
            get_single_adjudication_prompt(
                query=query,
                rubric=rubric,
                doc_content=self._extract_content(doc)
            )
            for doc in docs
        ]

        # ==================== 步骤 2: 调用 LLM ====================
        if self.use_parallel:
            # 使用 batch_call_json 并行调用
            results = self.llm_client.batch_call_json(
                prompts=prompts,
                max_workers=self.max_workers,
                max_retry=self.max_retry
            )
            # batch_call_json 直接返回 List[Dict[str, Any]]
        else:
            # 使用 call_json 串行调用
            results = []
            for prompt in prompts:
                result = self.llm_client.call_json(prompt)
                results.append(result)

        # ==================== 步骤 3: 处理结果并过滤 ====================
        for idx, doc in enumerate(docs):
            result = results[idx]
            doc_id = doc.get("id", doc.get("arxiv_id", f"doc_{idx}"))
            title = doc.get("title", "无标题")[:50]

            # single prompt 的结果结构包含 relevance, reason, evidence 字段
            is_relevant = result.get("relevance") in ["Perfectly Relevant", "Somewhat Relevant"]
            evidence_list = result.get("evidence", [])
            reason = result.get("reason", "")

            if is_relevant:
                evidence_text = "; ".join(evidence_list) if evidence_list else ""
                self.log(f"[ACCEPT] 采纳证据 (ID: {doc_id}): {title}", details={
                    "doc_id": doc_id,
                    "reason": reason,
                    "evidence_preview": evidence_text[:200] if evidence_text else "",
                })
                new_evidence.append({
                    "doc_id": doc_id,
                    "content": evidence_text,
                    "reason": reason,
                    "source": doc.get("source", "unknown"),
                    "relevance_score": result.get("relevance_score") or self._default_score(result.get("relevance", "")),
                    "facet_id": result.get("facet_id"),
                    "metadata": {
                        "title": doc.get("title", ""),
                        "year": doc.get("year") or doc.get("metadata", {}).get("date", ""),
                        "authors": doc.get("authors", []),
                        "url": doc.get("arxiv_url", ""),
                    }
                })
            else:
                rejected_count += 1
                reject_reason = reason or "不符合研判准则"
                self.log(f"[REJECT] 拒绝文档 (ID: {doc_id}): {title}", details={
                    "doc_id": doc_id,
                    "reason": reject_reason,
                })
                
                # 收集被拒绝的文档信息
                rejected_docs.append({
                    "doc_id": doc_id,
                    "title": doc.get("title", ""),
                    "reason": reject_reason,
                    "abstract": doc.get("abstract", "")[:200] if doc.get("abstract") else "",
                })

        # ==================== 步骤 4: 统计结果 ====================
        total = len(docs)
        accepted = len(new_evidence)
        acceptance_rate = accepted / total if total > 0 else 0

        self.log(f"研判完成: 采纳 {accepted} 篇, 拒绝 {rejected_count} 篇")
        self.log(f"通过率: {acceptance_rate:.1%}", details={
            "accepted": accepted,
            "rejected": rejected_count,
            "total": total,
            "acceptance_rate": acceptance_rate,
        })

        # 如果通过率较低，给出提示
        if acceptance_rate < 0.3 and total > 0:
            self.log("通过率较低，可能需要调整检索策略", level="WARN")

        return self.build_result({
            "verified_evidence": new_evidence,
            "rejected_docs": rejected_docs,  # 包含被拒绝的文档
        })

    def _get_rubric(self, intent: Dict[str, Any]) -> str:
        """
        获取研判准则

        Args:
            intent: 意图字典

        Returns:
            研判准则字符串
        """
        judgement = intent.get("judgement_rubric", {})
        if isinstance(judgement, dict):
            positive = judgement.get("criteria_positive", "")
            negative = judgement.get("criteria_negative", "")
            rubric = positive
            if negative:
                rubric += f" (排除: {negative})"
            return rubric or "文档内容相关即可"
        return str(judgement) if judgement else "文档内容相关即可"

    def _extract_content(self, doc: Dict[str, Any]) -> str:
        """
        从文档中提取用于评估的内容

        Args:
            doc: 文档对象

        Returns:
            提取的文本内容
        """
        # 优先使用 content 字段
        if "content" in doc:
            return doc["content"]

        # 论文数据：拼接标题和摘要
        parts = []
        if "title" in doc:
            parts.append(f"标题: {doc['title']}")
        if "abstract" in doc:
            parts.append(f"摘要: {doc['abstract']}")
        if "full_text" in doc:
            # 截取前 1000 字符
            parts.append(f"全文: {doc['full_text'][:1000]}...")

        return "\n".join(parts) if parts else str(doc)

    def _default_score(self, relevance: str) -> float:
        """当 LLM 未返回 relevance_score 时，根据分类给出默认分数"""
        mapping = {
            "Perfectly Relevant": 0.9,
            "Somewhat Relevant": 0.6,
            "Not Relevant": 0.1,
        }
        return mapping.get(relevance, 0.5)
