"""
JSON 数据加载器

从 JSON 文件加载数据，支持论文数据等格式。
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.crux.data.loaders.base import BaseDataLoader, apply_constraints
from src.crux.config import CruxConfig


class JsonDataLoader(BaseDataLoader):
    """
    JSON 数据加载器
    
    支持:
    - 单个 JSON 文件
    - 论文数据格式 (ir_papers.json)
    - 通用 JSON 数组格式
    """
    
    # 默认数据路径
    DEFAULT_PATH = "data/ir_papers.json"
    
    def __init__(
        self,
        file_path: Optional[str] = None,
        config: Optional[CruxConfig] = None
    ):
        super().__init__(config)
        self.file_path = file_path or self.DEFAULT_PATH
    
    def load(self) -> List[Dict[str, Any]]:
        """
        加载 JSON 数据
        
        Returns:
            文档列表
        """
        if self._data is not None:
            return self._data
        path = Path(self.file_path)
        if not path.exists():
            print(f"[JsonLoader] 警告: 文件不存在 {path}, 使用空数据")
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
                for key in ["papers", "documents", "data", "items"]:
                    if key in data and isinstance(data[key], list):
                        self._data = data[key]
                        break
                else:
                    # 单个文档
                    self._data = [data]
            else:
                self._data = []
            
            print(f"[JsonLoader] 加载了 {len(self._data)} 条数据")
            
        except Exception as e:
            print(f"[JsonLoader] 加载失败: {e}")
            self._data = []
        
        return self._data
    
    def search(
        self,
        keywords: List[str],
        vector_queries: List[str],
        constraints: Dict[str, Any],
        top_k: int = 50
    ) -> List[Dict[str, Any]]:
        """
        混合检索实现
        
        Args:
            keywords: BM25 关键词
            vector_queries: 向量检索查询
            constraints: 约束条件
            top_k: 返回数量
            
        Returns:
            检索结果列表
        """
        print(f"[JsonLoader] 搜索: keywords={keywords}, vector_queries={vector_queries}, constraints={constraints}")
        if self._data is None:
            self.load()
        
        # 1. 应用元数据过滤
        filtered_docs = apply_constraints(self._data, constraints)
        print(f"[JsonLoader] 过滤后剩余: {len(filtered_docs)} 条")
        
        # 2. 关键词匹配打分
        scored_docs = []
        search_terms = keywords + vector_queries
        
        for doc in filtered_docs:
            score = self._calculate_score(doc, search_terms)
            if score > 0:
                scored_docs.append((score, doc))
            elif random.random() > 0.9:  # 随机采样一些
                scored_docs.append((0.1, doc))
        
        # 3. 排序并返回 Top-K
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        results = [doc for _, doc in scored_docs[:top_k]]
        
        print(f"[JsonLoader] 召回: {len(results)} 条")
        return results
    
    def _calculate_score(
        self,
        doc: Dict[str, Any],
        search_terms: List[str]
    ) -> float:
        """计算文档与查询的相关性分数"""
        score = 0.0
        
        # 需要搜索的字段
        searchable_fields = [
            "title", "abstract", "full_text", "content",
            "alphaxiv_overview.overviews.zh.title",
            "alphaxiv_overview.overviews.zh.abstract",
        ]
        
        # 提取所有可搜索文本
        text_parts = []
        for field in searchable_fields:
            value = self._get_nested_value(doc, field)
            if value and isinstance(value, str):
                text_parts.append(value.lower())
        
        full_text = " ".join(text_parts)
        
        # 关键词匹配打分
        for term in search_terms:
            term_lower = term.lower()
            if term_lower in full_text:
                score += 1.0
                # 标题命中加权
                if "title" in doc and term_lower in doc["title"].lower():
                    score += 2.0
        
        return score
    
    def _get_nested_value(self, doc: Dict[str, Any], path: str) -> Any:
        """获取嵌套字段值"""
        parts = path.split(".")
        value = doc
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None
        return value
