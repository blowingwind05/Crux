"""
ReportNode 独立运行示例

用于单独测试报告生成模块，不依赖完整的 AgentGraph。

使用方法:
    python -m src.crux.tests.example_report_node
"""

import json
import time
from typing import Dict, Any

from src.crux.config import CruxConfig
from src.crux.modules.strategy import ReportNode


def run_report_example():
    """
    单独运行 ReportNode 的示例
    
    这个示例展示了如何：
    1. 创建配置
    2. 初始化 ReportNode
    3. 构造包含 verified_evidence 的输入状态
    4. 调用节点处理函数
    5. 查看生成的报告
    """
    
    print("=" * 60)
    print("[START] ReportNode 独立测试")
    print("=" * 60)
    
    # ========================================
    # 1. 创建配置
    # ========================================
    config = CruxConfig(
        schema_type="paper",
        debug=True,
    )
    
    print(f"\n[CONFIG] 配置信息:")
    print(f"  - schema_type: {config.schema_type}")
    print(f"  - debug: {config.debug}")
    
    # ========================================
    # 2. 初始化 ReportNode
    # ========================================
    report_node = ReportNode(config)
    
    print(f"\n[NODE] 节点信息:")
    print(f"  - name: {report_node.name}")
    print(f"  - description: {report_node.description}")
    
    # ========================================
    # 3. 准备输入状态 (模拟完整流程后的证据)
    # ========================================
    mock_verified_evidence = [
        {
            "doc_id": "2020.lewis.rag",
            "content": "RAG (Retrieval-Augmented Generation) 结合了检索器和生成器，通过检索外部知识库来增强语言模型的生成能力。这解决了传统LLM知识过时和幻觉问题。",
            "reason": "核心论文，定义了RAG的基本框架",
            "source": "arxiv",
            "metadata": {
                "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
                "year": "2020"
            }
        },
        {
            "doc_id": "2023.selfrag",
            "content": "Self-RAG 让模型学会自主决定何时需要检索，以及如何评估和筛选检索到的内容，实现了检索的自适应控制。",
            "reason": "介绍了RAG的重要改进方向",
            "source": "arxiv",
            "metadata": {
                "title": "Self-RAG: Learning to Retrieve, Generate, and Critique",
                "year": "2023"
            }
        },
        {
            "doc_id": "2024.ragsurvey",
            "content": "RAG技术已广泛应用于问答、对话、代码生成等场景。最新趋势包括：多模态RAG、自适应检索、知识图谱增强等。",
            "reason": "提供了RAG应用场景和发展趋势的全面总结",
            "source": "survey",
            "metadata": {
                "title": "A Survey on Retrieval-Augmented Generation",
                "year": "2024"
            }
        }
    ]
    
    input_state: Dict[str, Any] = {
        "user_query": "帮我全面介绍RAG检索增强生成技术的原理、应用和最新进展",
        "verified_evidence": mock_verified_evidence,
        "search_iteration": 2,  # 经过2轮检索
    }
    
    print(f"\n[INPUT] 用户查询: {input_state['user_query']}")
    print(f"[INPUT] 证据数量: {len(mock_verified_evidence)}")
    print(f"[INPUT] 检索轮次: {input_state['search_iteration']}")
    
    # ========================================
    # 4. 调用 ReportNode.process()
    # ========================================
    print("\n[PROCESSING] 正在生成报告...")
    start_time = time.time()
    
    try:
        output_state = report_node.process(input_state)
        elapsed = time.time() - start_time
        
        print(f"\n[SUCCESS] 报告生成完成 (耗时: {elapsed:.2f}s)")
        
        # ========================================
        # 5. 查看生成的报告
        # ========================================
        final_report = output_state.get("final_report", "")
        
        print("\n" + "=" * 60)
        print("[FINAL REPORT]")
        print("=" * 60)
        print(final_report)
            
    except Exception as e:
        print(f"\n[ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[END] ReportNode 测试完成")
    print("=" * 60)


def run_empty_evidence_test():
    """
    测试无证据情况下的报告生成
    """
    
    print("\n\n" + "=" * 60)
    print("[START] 空证据测试")
    print("=" * 60)
    
    config = CruxConfig(debug=True)
    report_node = ReportNode(config)
    
    input_state = {
        "user_query": "查找一个不存在的主题",
        "verified_evidence": [],  # 没有找到任何证据
        "search_iteration": 3,
    }
    
    print(f"\n[INPUT] 证据数: 0")
    
    try:
        output = report_node.process(input_state)
        print("\n[REPORT]")
        print(output.get("final_report", ""))
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    # 运行基础示例
    run_report_example()
    
    # 可选：运行空证据测试
    # run_empty_evidence_test()
