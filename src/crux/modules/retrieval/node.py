"""
混合检索节点 (Retrieval Node)

负责人: [待分配]

功能:
- 基于意图执行混合检索
- 支持 BM25 关键词检索
- 支持向量语义检索
- 支持元数据过滤
"""

from typing import Dict, Any, List

from src.crux.utils.base import BaseNode


class RetrievalNode(BaseNode):
    """
    意图增强的混合召回节点
    
    并行执行三种检索方式:
    1. 字段过滤 - 基于硬逻辑约束 (SQL/Grep)
    2. 稀疏检索 - 基于关键词匹配 (BM25)
    3. 向量检索 - 基于语义理解 (Vector Search)
    """
    
    name = "retrieve"
    description = "执行混合检索，召回候选文档"
    
    def __init__(self, config=None):
        super().__init__(config)
        self._data_loader = None
    
    @property
    def data_loader(self):
        """延迟加载数据加载器"""
        if self._data_loader is None:
            from src.crux.data import get_data_loader
            self._data_loader = get_data_loader(self.config)
        return self._data_loader
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行混合检索
        
        Args:
            state: 包含 intent 的状态
            
        Returns:
            包含 candidate_docs 的更新
        """
        self.log("正在执行混合召回...")
        
        intent = state["intent"]
        
        # 解包意图参数
        keywords = intent.get("keywords_bm25", [])
        vector_queries = intent.get("queries_vector", [])
        constraints = intent.get("constraints", {"structured_metadata": []})
        
        # 执行检索
        docs = self.hybrid_search(keywords, vector_queries, constraints)
        
        self.log(f"召回文档数: {len(docs)}")
        
        return {"candidate_docs": docs}
    
    def hybrid_search(
        self,
        keywords: List[str],
        vector_queries: List[str],
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        混合检索实现
        
        Args:
            keywords: BM25 关键词列表
            vector_queries: 向量检索查询列表
            constraints: 约束条件
            
        Returns:
            召回的文档列表
        """
        self.log(f"执行过滤: {constraints}")
        
        # 调用数据加载器的搜索方法
        docs = self.data_loader.search(
            keywords=keywords,
            vector_queries=vector_queries,
            constraints=constraints,
            top_k=self.config.search.top_k
        )
        
        return docs[:self.config.search.top_k]
