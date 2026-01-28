"""
数据加载器基类

定义所有数据加载器的通用接口。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from src.crux.config import CruxConfig


class BaseDataLoader(ABC):
    """
    数据加载器抽象基类
    
    所有数据加载器都需要实现:
    - load(): 加载全部数据
    - search(): 执行检索
    """
    
    def __init__(self, config: Optional[CruxConfig] = None):
        self.config = config or CruxConfig()
        self._data: Optional[List[Dict[str, Any]]] = None
    
    @abstractmethod
    def load(self) -> List[Dict[str, Any]]:
        """
        加载数据
        
        Returns:
            文档列表
        """
        pass
    
    @abstractmethod
    def search(
        self,
        keywords: List[str],
        vector_queries: List[str],
        constraints: Dict[str, Any],
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            keywords: BM25 关键词
            vector_queries: 向量检索查询
            constraints: 约束条件
            top_k: 返回数量
            
        Returns:
            检索结果列表
        """
        pass
    
    def get_by_id(self, doc_id: Any) -> Optional[Dict[str, Any]]:
        """
        根据 ID 获取文档
        
        Args:
            doc_id: 文档 ID
            
        Returns:
            文档对象或 None
        """
        if self._data is None:
            self._data = self.load()
        
        for doc in self._data:
            if doc.get("id") == doc_id or doc.get("arxiv_id") == doc_id:
                return doc
        return None
    
    def count(self) -> int:
        """获取文档总数"""
        if self._data is None:
            self._data = self.load()
        return len(self._data)
