"""
AdjudicationNode 独立运行示例

用于单独测试深度研判模块，不依赖完整�?AgentGraph�?

使用方法:
    python -m src.crux.tests.example_adjudication_node
"""

import json
import time
from typing import Dict, Any

from src.crux.config import CruxConfig
from src.crux.modules.adjudication import AdjudicationNode


def run_adjudication_example():
    """
    单独运行 AdjudicationNode 的示�?
    
    这个示例展示了如何：
    1. 创建配置
    2. 初始�?AdjudicationNode
    3. 构造包�?candidate_docs �?intent 的输入状�?
    4. 调用节点处理函数
    5. 查看研判结果
    """
    
    print("=" * 60)
    print("[START] AdjudicationNode 独立测试")
    print("=" * 60)
    
    # ========================================
    # 1. 创建配置
    # ========================================
    config = CruxConfig(
        schema_path="config/paper_schema.yaml",
        mock_llm=False,  # 设为 True 使用 mock 响应
        debug=True,
    )
    
    print(f"\n[CONFIG] 配置信息:")
    print(f"  - mock_llm: {config.mock_llm}")
    print(f"  - debug: {config.debug}")
    
    # ========================================
    # 2. 初始�?AdjudicationNode
    # ========================================
    adjudication_node = AdjudicationNode(config)
    
    print(f"\n[NODE] 节点信息:")
    print(f"  - name: {adjudication_node.name}")
    print(f"  - description: {adjudication_node.description}")
    
    # ========================================
    # 3. 准备输入状�?(模拟 RetrievalNode 的输�?
    # ========================================
    # 模拟召回的候选文�?
    mock_candidate_docs = [
        {
            "id": "paper_001",
            "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
            "abstract": "Large pre-trained language models have been shown to store factual knowledge in their parameters. However, their ability to access and manipulate knowledge is still limited. We propose RAG models that combine pre-trained parametric and non-parametric memory for language generation.",
            "year": 2023,
            "source": "arxiv"
        },
        {
            "id": "paper_002",
            "title": "A Survey on Machine Translation Methods",
            "abstract": "This paper surveys various machine translation approaches including statistical and neural machine translation. We discuss encoder-decoder architectures and attention mechanisms.",
            "year": 2022,
            "source": "arxiv"
        },
        {
            "id": "paper_003",
            "title": "Self-RAG: Learning to Retrieve, Generate, and Critique",
            "abstract": "We introduce Self-RAG, a framework that trains a single LM to adaptively retrieve passages on-demand and reflect on retrieved passages and its own generation.",
            "year": 2024,
            "source": "arxiv"
        }
    ]
    
    # 模拟意图对象
    mock_intent = {
        "user_goal": "INVESTIGATIVE",
        "rubric": "论文必须涉及RAG（检索增强生成）技术，与机器翻译无关的论文应该被排�?,
        "keywords_bm25": ["RAG", "检索增强生�?],
        "queries_vector": []
    }
    
    input_state: Dict[str, Any] = {
        "user_query": "帮我找关于RAG检索增强生成的论文",
        "intent": mock_intent,
        "candidate_docs": mock_candidate_docs,
        "verified_evidence": [],
        "search_iteration": 1,
    }
    
    print(f"\n[INPUT] 候选文档数: {len(mock_candidate_docs)}")
    print(f"[INPUT] 研判准则: {mock_intent['rubric']}")
    
    # ========================================
    # 4. 调用 AdjudicationNode.process()
    # ========================================
    print("\n[PROCESSING] 正在进行深度研判...")
    start_time = time.time()
    
    try:
        output_state = adjudication_node.process(input_state)
        elapsed = time.time() - start_time
        
        print(f"\n[SUCCESS] 研判完成 (耗时: {elapsed:.2f}s)")
        
        # ========================================
        # 5. 查看研判结果
        # ========================================
        verified_evidence = output_state.get("verified_evidence", [])
        print(f"\n[OUTPUT] 验证通过的证据数: {len(verified_evidence)}")
        
        print("\n[EVIDENCE] 采纳的证�?")
        for i, evidence in enumerate(verified_evidence, 1):
            print(f"\n  [{i}] Doc ID: {evidence.get('doc_id')}")
            print(f"      Title: {evidence.get('metadata', {}).get('title', 'N/A')}")
            print(f"      Content: {evidence.get('content', 'N/A')[:100]}...")
            print(f"      Reason: {evidence.get('reason', 'N/A')}")
            
    except Exception as e:
        print(f"\n[ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[END] AdjudicationNode 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    run_adjudication_example()
