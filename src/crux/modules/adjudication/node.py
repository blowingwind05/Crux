"""
深度研判节点 (Adjudication Node)

负责人: [待分配]

功能:
- 根据研判准则评估文档相关性
- 提取高价值证据
- 过滤语义相似但事实无关的噪音
"""

import time
from typing import Dict, Any, List

from src.crux.utils.base import BaseNode
from src.crux.utils.llm_client import LLMClient
from src.crux.modules.adjudication.prompts import get_adjudication_prompt


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
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        对候选文档进行深度研判
        
        Args:
            state: 包含 candidate_docs, intent 的状态
            
        Returns:
            包含 verified_evidence 的更新
        """
        self.reset_logger()
        
        docs = state["candidate_docs"]
        intent = state["intent"]
        rubric = self._get_rubric(intent)
        
        self.log("开始深度研判流程...")
        self.log(f"待研判文档: {len(docs)} 篇")
        self.log(f"研判准则: {rubric[:100]}..." if len(rubric) > 100 else f"研判准则: {rubric}")
        
        new_evidence = []
        rejected_count = 0
        
        for idx, doc in enumerate(docs):
            doc_id = doc.get("id", doc.get("arxiv_id", f"doc_{idx}"))
            title = doc.get("title", "无标题")[:50]
            
            self.log(f"评估文档 [{idx+1}/{len(docs)}]: {title}...", details={
                "doc_id": doc_id,
                "title": doc.get("title", ""),
            })
            
            # 评估文档
            start_time = time.time()
            result = self.evaluate_document(doc, rubric)
            eval_time = (time.time() - start_time) * 1000
            
            if result.get("is_relevant"):
                evidence_preview = result.get("evidence", "")[:80]
                self.log(f"[ACCEPT] 采纳证据: {evidence_preview}...", details={
                    "doc_id": doc_id,
                    "reason": result.get("reason", ""),
                    "eval_time_ms": eval_time,
                })
                
                new_evidence.append({
                    "doc_id": doc_id,
                    "content": result.get("evidence"),
                    "reason": result.get("reason"),
                    "source": doc.get("source", "unknown"),
                    "relevance_score": result.get("relevance_score", 0.8),
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
                reject_reason = result.get("reason", "不符合研判准则")
                self.log(f"[REJECT] 拒绝文档: {reject_reason}", level="DEBUG", details={
                    "doc_id": doc_id,
                    "reason": reject_reason,
                })
        
        # 统计结果
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
        
        return self.build_result({"verified_evidence": new_evidence})
    
    def _get_rubric(self, intent: Dict[str, Any]) -> str:
        """获取研判准则"""
        judgement = intent.get("judgement_rubric", {})
        if isinstance(judgement, dict):
            positive = judgement.get("criteria_positive", "")
            negative = judgement.get("criteria_negative", "")
            rubric = positive
            if negative:
                rubric += f" (排除: {negative})"
            return rubric or "文档内容相关即可"
        return str(judgement) if judgement else "文档内容相关即可"
    
    def evaluate_document(self, doc: Dict[str, Any], rubric: str) -> Dict[str, Any]:
        """
        评估单个文档
        
        Args:
            doc: 文档对象
            rubric: 研判准则
            
        Returns:
            评估结果，包含 is_relevant, evidence, reason
        """
        # 获取文档内容
        content = self._extract_content(doc)
        
        # 构建 prompt
        prompt = get_adjudication_prompt(rubric=rubric, doc_content=content)
        
        # 调用 LLM
        result = self.llm_client.call_json(prompt)
        
        return result
    
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
