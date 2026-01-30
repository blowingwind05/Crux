"""
RetrievalNode 独立运行示例

用于单独测试混合检索模块，不依赖完整的 AgentGraph�?

使用方法:
    python -m src.crux.tests.example_retrieval_node
"""

import json
import time
from typing import Dict, Any

from src.crux.config import CruxConfig
from src.crux.modules.retrieval import RetrievalNode


def run_retrieval_example():
    """
    单独运行 RetrievalNode 的示�?
    
    这个示例展示了如何：
    1. 创建配置
    2. 初始�?RetrievalNode
    3. 构造包�?intent 的输入状�?
    4. 调用节点处理函数
    5. 查看召回的文�?
    """
    
    print("=" * 60)
    print("[START] RetrievalNode 独立测试")
    print("=" * 60)
    
    # ========================================
    # 1. 创建配置
    # ========================================
    config = CruxConfig(
        data_source_type="json",
        data_source_path="data/ir_papers.json",
        schema_path="config/paper_schema.yaml",
        debug=True,
    )
    
    print(f"\n[CONFIG] 配置信息:")
    print(f"  - data_source_type: {config.data_source_type}")
    print(f"  - data_source_path: {config.data_source_path}")
    print(f"  - top_k: {config.search.top_k}")
    
    # ========================================
    # 2. 初始�?RetrievalNode
    # ========================================
    retrieval_node = RetrievalNode(config)
    
    print(f"\n[NODE] 节点信息:")
    print(f"  - name: {retrieval_node.name}")
    print(f"  - description: {retrieval_node.description}")
    
    # ========================================
    # 3. 准备输入状�?(模拟 UnderstandingNode 的输�?
    # ========================================
    # RetrievalNode 需�?intent 对象
    mock_intent = {
        "user_goal": "INVESTIGATIVE",
        "constraints": {
            "structured_metadata": [
                # 可以添加过滤条件，例�?
                # {"field": "year", "operator": "gte", "value": 2023}
            ],
            "unstructured_content_patterns": []
        },
        "keywords_bm25": ["RAG", "检索增强生�?, "信息检�?, "LLM"],
        "queries_vector": [
            "RAG检索增强生成的最新研究进�?,
            "大语言模型与信息检索的结合"
        ],
        "rubric": "论文需要涉及RAG或检索增强相关技�?
    }
    
    input_state: Dict[str, Any] = {
        "user_query": "帮我找关于RAG检索增强生成的论文",
        "intent": mock_intent,
        "verified_evidence": [],
        "search_iteration": 0,
    }
    
    print(f"\n[INPUT] 意图对象:")
    print(f"  - keywords_bm25: {mock_intent['keywords_bm25']}")
    print(f"  - queries_vector: {mock_intent['queries_vector']}")
    
    # ========================================
    # 4. 调用 RetrievalNode.process()
    # ========================================
    print("\n[PROCESSING] 正在执行混合检�?..")
    start_time = time.time()
    
    try:
        output_state = retrieval_node.process(input_state)
        elapsed = time.time() - start_time
        
        print(f"\n[SUCCESS] 检索完�?(耗时: {elapsed:.2f}s)")
        
        # ========================================
        # 5. 查看召回结果
        # ========================================
        candidate_docs = output_state.get("candidate_docs", [])
        print(f"\n[OUTPUT] 召回文档�? {len(candidate_docs)}")
        
        # 显示�?个文�?
        print("\n[DOCS] 召回的文�?(�?�?:")
        for i, doc in enumerate(candidate_docs[:3], 1):
            print(f"\n  [{i}] ID: {doc.get('id', doc.get('arxiv_id', 'N/A'))}")
            print(f"      Title: {doc.get('title', 'N/A')[:60]}...")
            if 'abstract' in doc:
                print(f"      Abstract: {doc['abstract'][:80]}...")
            if 'score' in doc:
                print(f"      Score: {doc['score']:.4f}")
                
    except Exception as e:
        print(f"\n[ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[END] RetrievalNode 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    run_retrieval_example()
