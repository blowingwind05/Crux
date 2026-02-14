import json
import pandas as pd

from pathlib import Path
from typing import List, Dict, Any, Optional

from src.crux.data.loaders.base import BaseDataLoader
from src.crux.config import CruxConfig
from src.crux.utils.constraints import apply_constraints
from src.crux.retriever.hybrid_retriever import HybridRetriever

from src.crux.utils.retriever_config import RetrieverConfig

CONFIG = RetrieverConfig(r"src\crux\utils\config.yaml").config_dict

class HybridDataLoader(BaseDataLoader):
    """
    混合检索加载器
    目前仅支持从 JSON 文件加载数据

    """

    # 默认数据路径
    DEFAULT_PATH = "data/ir_papers.json"
    def __init__(self, config: Optional[CruxConfig] = None):
        super().__init__(config)
        self.file_path = (config.data_source_path if config else None) or self.DEFAULT_PATH
    
    def load(self) -> List[Dict[str, Any]]:
        """
        加载数据
        
        Returns:
            文档列表
        """
        if self._data is not None:
            return self._data
        path = Path(self.file_path)
        if not path.exists():
            print(f"[HybridDataLoader] 警告: 文件不存在 {path}, 使用空数据")
            self._data = []
            return self._data
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理不同格式
            if isinstance(data, list):
                self._data = data
            elif isinstance(data, dict):
                # 可能是 {"papers": [...]} 格式
                self._data = data.get("papers", [])
            else:
                print(f"[HybridDataLoader] 警告: 不支持的数据格式 {type(data)}, 使用空数据")
        except Exception as e:
            print(f"[HybridDataLoader] 加载数据失败: {e}")
        self._data = self._data or []
        return self._data
    
    def search(
        self,
        keywords: List[str],
        vector_queries: List[str],
        constraints: Dict[str, Any],
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        搜索接口
        
        Args:
            keywords: BM25 关键词列表
            vector_queries: 向量检索查询列表
            constraints: 约束条件
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        if self._data is None:
            self.load()

        # 1. 应用元数据过滤
        filtered_docs = apply_constraints(self._data, constraints)
        print(f"[HybridDataLoader] 过滤后剩余: {len(filtered_docs)} 条")

        df_papers = pd.DataFrame(filtered_docs)
        df_papers.fillna("", inplace=True)
        # Create a combined text field for search
        df_papers["combined_text"] = df_papers.apply(
            lambda x: f"{x['title']} {x['abstract']}", axis=1
        )
        retriever = HybridRetriever(df_papers)
        query_tokens = [keywords]
        candidates = retriever.hybrid_search(
            queries=vector_queries,
            query_tokens=query_tokens,
            top_k=top_k
        )
        # Create a lookup dict for fast access
        doc_lookup = {doc["arxiv_id"]: doc for doc in filtered_docs}
        if CONFIG.get("rerank", False):
            sorted_docs = []
            for arxiv_id, _ in candidates:
                if arxiv_id in doc_lookup:
                    sorted_docs.append(doc_lookup[arxiv_id])
            return sorted_docs
        else:
            merged_query = " ".join(vector_queries)
            tops = retriever.rerank(merged_query, candidates, top_k)
            sorted_docs = []
            for arxiv_id in tops:
                if arxiv_id in doc_lookup:
                    sorted_docs.append(doc_lookup[arxiv_id])
            return sorted_docs


