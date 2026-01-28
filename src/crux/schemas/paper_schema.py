"""
论文数据 Schema

定义学术论文数据的结构配置。
"""

from typing import List, Dict, Any

from src.crux.schemas.base import BaseSchema


class PaperSchema(BaseSchema):
    """
    学术论文数据 Schema
    
    基于 data/schema.md 定义的字段结构。
    """
    
    name = "paper"
    description = "学术论文数据结构，包含标题、摘要、作者、分类等信息"
    
    def get_field_descriptions(self) -> str:
        """获取字段描述"""
        return """
## 论文数据结构

本数据集包含学术论文的结构化信息，主要字段如下：

### 基础字段
- `arxiv_id`: 论文的 arXiv ID（如 "2512.23647"）
- `title`: 论文英文标题
- `abstract`: 论文英文摘要
- `full_text`: 论文完整文本内容

### 元数据 (metadata)
- `metadata.category`: 类别缩写（如 "CL", "IR"）
- `metadata.authors`: 作者列表
- `metadata.date`: 发布日期（如 "2025-12-29"）
- `metadata.primary_category`: 主要类别（如 "cs.CL"）
- `metadata.all_categories`: 所有类别列表

### 多语言概览 (alphaxiv_overview.overviews)
- `zh.title`: 中文标题
- `zh.abstract`: 中文摘要
- `zh.summary.summary`: 中文简短总结
- `zh.summary.originalProblem`: 原始问题列表
- `zh.summary.solution`: 解决方案列表
- `zh.summary.keyInsights`: 关键洞察列表
- `zh.summary.results`: 结果列表

### 评分详情 (score_detail)
- `scores.novelty`: 新颖性评分 (0-100)
- `scores.methodology`: 方法论评分
- `scores.relevance`: 相关性评分
- `scores.impact`: 影响力评分
- `overall_score`: 总体评分

### 分类详情 (category_detail)
- `category_name`: 类别名称
- `category_description`: 类别描述
- `sub_categories`: 子类别列表
- `confidence`: 分类置信度

### 统计信息 (hits)
- `views`: 浏览量
- `citations`: 引用数
- `comments`: 评论数
"""
    
    def get_searchable_fields(self) -> List[str]:
        """获取可搜索字段"""
        return [
            "title",
            "abstract",
            "full_text",
            "alphaxiv_overview.overviews.zh.title",
            "alphaxiv_overview.overviews.zh.abstract",
            "alphaxiv_overview.overviews.zh.overview",
        ]
    
    def get_filterable_fields(self) -> List[Dict[str, Any]]:
        """获取可过滤字段"""
        return [
            {
                "name": "metadata.date",
                "type": "date",
                "operators": ["eq", "gt", "lt", "gte", "lte", "range"],
                "description": "发布日期"
            },
            {
                "name": "metadata.primary_category",
                "type": "string",
                "operators": ["eq", "neq", "in"],
                "description": "主要类别"
            },
            {
                "name": "metadata.all_categories",
                "type": "array",
                "operators": ["in", "contains"],
                "description": "所有类别"
            },
            {
                "name": "score_detail.overall_score",
                "type": "number",
                "operators": ["eq", "gt", "lt", "gte", "lte", "range"],
                "description": "总体评分"
            },
            {
                "name": "category_detail.category_name",
                "type": "string",
                "operators": ["eq", "in"],
                "description": "分类名称"
            },
            {
                "name": "hits.citations",
                "type": "number",
                "operators": ["gt", "gte"],
                "description": "引用数"
            },
        ]
    
    def get_example_queries(self) -> List[str]:
        """获取示例查询"""
        return [
            "找一下关于 RAG 和检索增强生成的最新论文",
            "帮我找2024年发布的信息检索方向高分论文",
            "有什么关于 Agent 智能体的研究吗？",
            "搜索关于大语言模型推理能力的论文",
        ]
    
    def get_category_mapping(self) -> Dict[str, str]:
        """获取类别代码到名称的映射"""
        return {
            "cs.IR": "Information Retrieval",
            "cs.CL": "Computation and Language",
            "cs.AI": "Artificial Intelligence",
            "cs.LG": "Machine Learning",
            "cs.CV": "Computer Vision",
            "cs.MA": "Multi-Agent Systems",
        }
