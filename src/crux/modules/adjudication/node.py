"""
深度研判节点 (Adjudication Node)

负责人: [待分配]

功能:
- 根据研判准则评估文档相关性
- 提取高价值证据
- 过滤语义相似但事实无关的噪音
"""

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
        self.log("正在进行深度研判...")
        
        docs = state["candidate_docs"]
        rubric = state["intent"].get("rubric", "文档内容相关即可")
        
        new_evidence = []
        
        for doc in docs:
            result = self.evaluate_document(doc, rubric)
            
            if result.get("is_relevant"):
                doc_id = doc.get("id", doc.get("arxiv_id", "unknown"))
                self.log(f"[ACCEPT] 采纳证据 (ID: {doc_id}): {result.get('evidence', '')[:50]}...")
                new_evidence.append({
                    "doc_id": doc_id,
                    "content": result.get("evidence"),
                    "reason": result.get("reason"),
                    "source": doc.get("source", "unknown"),
                    "metadata": {
                        "title": doc.get("title", ""),
                        "year": doc.get("year") or doc.get("metadata", {}).get("date", ""),
                    }
                })
            else:
                doc_id = doc.get("id", doc.get("arxiv_id", "unknown"))
                self.log(f"[REJECT] 拒绝噪音 (ID: {doc_id})")
        
        return {"verified_evidence": new_evidence}
    
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
