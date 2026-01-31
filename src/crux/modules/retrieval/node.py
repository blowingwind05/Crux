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
    name_cn = "混合召回"
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
        self.reset_logger()
        
        intent = state["intent"]
        iteration = state.get("search_iteration", 0)
        
        self.log("开始混合检索流程...")
        if iteration > 0:
            self.log(f"当前为第 {iteration + 1} 次迭代检索", level="INFO")
        
        # 解包意图参数
        keywords = self._extract_keywords(intent)
        vector_queries = self._extract_queries(intent)
        constraints = intent.get("constraints", {"structured_metadata": []})
        
        # 记录检索参数
        self.log(f"BM25 关键词: {keywords}", details={"keywords": keywords})
        self.log(f"向量查询: {len(vector_queries)} 条", details={"queries": vector_queries})
        
        # 记录约束条件
        structured = constraints.get("structured_metadata", [])
        if structured:
            self.log(f"应用 {len(structured)} 个结构化过滤条件", details={
                "filters": structured
            })
        
        # 执行 BM25 检索
        self.log("执行 BM25 稀疏检索...")
        bm25_results = self._bm25_search(keywords)
        self.log(f"BM25 召回: {len(bm25_results)} 篇文档")
        
        # 执行向量检索
        self.log("执行向量语义检索...")
        vector_results = self._vector_search(vector_queries)
        self.log(f"向量召回: {len(vector_results)} 篇文档")
        
        # 执行过滤
        self.log("应用元数据过滤...")
        filter_results = self._filter_search(constraints)
        self.log(f"过滤通过: {len(filter_results)} 篇文档")
        
        # 融合结果
        self.log("融合多路召回结果...")
        docs = self.hybrid_search(keywords, vector_queries, constraints)
        
        # 标记来源
        for doc in docs:
            if "source" not in doc:
                doc["source"] = "hybrid"
        
        self.log(f"最终召回文档数: {len(docs)}", details={
            "total": len(docs),
            "bm25_count": len(bm25_results),
            "vector_count": len(vector_results),
            "top_k": self.config.search.top_k,
        })
        
        # 记录 Top 结果摘要
        for i, doc in enumerate(docs[:3]):
            title = doc.get("title", "无标题")[:50]
            score = doc.get("score", 0)
            self.log(f"Top-{i+1}: {title}... (score: {score:.3f})")
        
        return self.build_result({"candidate_docs": docs})
    
    def _extract_keywords(self, intent: Dict[str, Any]) -> List[str]:
        """从意图中提取 BM25 关键词"""
        retrieval = intent.get("retrieval_execution", {})
        sparse = retrieval.get("sparse_keywords", [])
        return [kw.get("term", kw) if isinstance(kw, dict) else str(kw) for kw in sparse]
    
    def _extract_queries(self, intent: Dict[str, Any]) -> List[str]:
        """从意图中提取向量查询"""
        retrieval = intent.get("retrieval_execution", {})
        return retrieval.get("dense_queries", [])
    
    def _bm25_search(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """BM25 检索"""
        if not keywords:
            return []
        return self.data_loader.search(
            keywords=keywords,
            vector_queries=[],
            constraints={},
            top_k=self.config.search.top_k
        )
    
    def _vector_search(self, queries: List[str]) -> List[Dict[str, Any]]:
        """向量检索"""
        if not queries:
            return []
        return self.data_loader.search(
            keywords=[],
            vector_queries=queries,
            constraints={},
            top_k=self.config.search.top_k
        )
    
    def _filter_search(self, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤检索"""
        structured = constraints.get("structured_metadata", [])
        if not structured:
            return []
        return self.data_loader.search(
            keywords=[],
            vector_queries=[],
            constraints=constraints,
            top_k=self.config.search.top_k
        )
    
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
        # 调用数据加载器的搜索方法
        docs = self.data_loader.search(
            keywords=keywords,
            vector_queries=vector_queries,
            constraints=constraints,
            top_k=self.config.search.top_k
        )
        
        return docs[:self.config.search.top_k]
