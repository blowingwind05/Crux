"""
研判逻辑核心类

提供文档评估的核心逻辑。
"""

from typing import Dict, Any, List, Optional

from src.crux.utils.llm_client import LLMClient
from src.crux.modules.adjudication.prompts import get_adjudication_prompt


class DocumentJudge:
    """
    文档研判器
    
    负责对文档进行证据级评估。
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def evaluate(
        self,
        doc: Dict[str, Any],
        rubric: str
    ) -> Dict[str, Any]:
        """
        评估单个文档
        
        Args:
            doc: 文档对象
            rubric: 研判准则
            
        Returns:
            评估结果
        """
        content = self._extract_content(doc)
        prompt = get_adjudication_prompt(rubric=rubric, doc_content=content)
        return self.llm_client.call_json(prompt)
    
    def batch_evaluate(
        self,
        docs: List[Dict[str, Any]],
        rubric: str,
        fast_filter: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量评估文档
        
        Args:
            docs: 文档列表
            rubric: 研判准则
            fast_filter: 是否启用快速过滤
            
        Returns:
            通过评估的证据列表
        """
        results = []
        
        for doc in docs:
            # 快速过滤：基于简单规则跳过明显不相关的文档
            if fast_filter and self._quick_reject(doc):
                continue
            
            result = self.evaluate(doc, rubric)
            if result.get("is_relevant"):
                results.append({
                    "doc": doc,
                    "evidence": result.get("evidence"),
                    "reason": result.get("reason")
                })
        
        return results
    
    def _quick_reject(self, doc: Dict[str, Any]) -> bool:
        """
        快速拒绝明显不相关的文档
        
        Args:
            doc: 文档对象
            
        Returns:
            是否应该拒绝
        """
        # 可以添加简单的规则判断
        # 例如：文档太短、缺少关键字段等
        content = doc.get("abstract", "") or doc.get("content", "")
        if len(content) < 50:
            return True
        return False
    
    def _extract_content(self, doc: Dict[str, Any]) -> str:
        """从文档中提取内容"""
        if "content" in doc:
            return doc["content"]
        
        parts = []
        if "title" in doc:
            parts.append(f"标题: {doc['title']}")
        if "abstract" in doc:
            parts.append(f"摘要: {doc['abstract']}")
        if "full_text" in doc:
            parts.append(f"全文: {doc['full_text'][:1000]}...")
        
        return "\n".join(parts) if parts else str(doc)
