import random

# 模拟本地知识库
MOCK_KNOWLEDGE_BASE = [
    {"id": 1, "content": "2023年Q4，特斯拉FSD Beta累计行驶里程突破5亿英里。", "source": "news", "year": 2023},
    {"id": 2, "content": "比亚迪2023年全年销量302万辆，同比增长62%。", "source": "financial_report", "year": 2023},
    {"id": 3, "content": "OpenAI发布Sora模型，支持生成60秒长视频。", "source": "news", "year": 2024},
    {"id": 4, "content": "某内部系统报错：TimeoutException 5002 at Service A.", "source": "internal_log", "year": 2024},
    {"id": 5, "content": "关于 LLM 上下文丢失问题的研究报告...", "source": "paper", "year": 2023},
]

def mock_hybrid_search(keywords: list, vector_queries: list, constraints: dict) -> list:
    """
    模拟混合检索：
    1. 模拟 SQL 过滤 (Constraints)
    2. 模拟 关键词匹配 (BM25)
    3. 模拟 向量检索 (随机返回一些相关性高的)
    """
    print(f"   [DB] 执行过滤: {constraints}")
    
    # 1. 简单的字段过滤模拟
    filtered_docs = MOCK_KNOWLEDGE_BASE
    for c in constraints['structured_metadata']:
        if c['field'] == 'year' and c['operator'] == 'gte':
            filtered_docs = [d for d in filtered_docs if d['year'] >= int(c['value'])]
            
    # 2. 模拟检索 (简单字符串匹配作为 mock)
    hits = []
    search_terms = keywords + vector_queries
    for doc in filtered_docs:
        score = 0
        for term in search_terms:
            if term in doc['content']:
                score += 1
        
        # 模拟向量检索总是能找回一点东西
        if score > 0 or random.random() > 0.7: 
            hits.append(doc)
            
    print(f"   [DB] 召回文档数: {len(hits)}")
    return hits[:5] # Top 5
