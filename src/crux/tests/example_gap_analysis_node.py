"""
GapAnalysisNode 独立运行示例

用于单独测试信息缺口分析模块，不依赖完整的 AgentGraph。

使用方法:
    python -m src.crux.tests.example_gap_analysis_node
"""

import json
import time
from typing import Dict, Any

from src.crux.config import CruxConfig
from src.crux.modules.strategy import GapAnalysisNode


def run_gap_analysis_example():
    """
    单独运行 GapAnalysisNode 的示例

    这个示例展示了如何：
    1. 创建配置
    2. 初始化 GapAnalysisNode
    3. 构造包含 verified_evidence 的输入状态
    4. 调用节点处理函数
    5. 查看缺口分析结果
    """

    print("=" * 60)
    print("[START] GapAnalysisNode 独立测试")
    print("=" * 60)

    # ========================================
    # 1. 创建配置
    # ========================================
    config_dict = {
        "llm": {
            "api_key": "Empty",
            "base_url": "https://aicloud.oneainexus.cn:30013/inference/aicloud-yanqiang/qwen3-32b-server/v1",
            "model": "Qwen/Qwen3-32B",
            "temperature": 0.7,
            "max_tokens": 32768
        },
        "judge": {
            "use_parallel": True,
            "max_retry": 5,
            "max_workers": 4,
            "batch_size": 4
        },
        "search": {
            "max_iterations": 3,
            "top_k": 2,
            "use_bm25": True,
            "use_vector": True,
            "use_metadata_filter": True
        },
        "schema_path": "config/paper_schema.yaml",
        "mock_llm": False,
        "debug": True,
    }
    config = CruxConfig.from_dict(config_dict)

    # 设置最大迭代次数
    config.search.max_iterations = 3

    print(f"\n[CONFIG] 配置信息:")
    print(f"  - max_iterations: {config.search.max_iterations}")
    print(f"  - mock_llm: {config.mock_llm}")

    # ========================================
    # 2. 初始化 GapAnalysisNode
    # ========================================
    gap_node = GapAnalysisNode(config)

    print(f"\n[NODE] 节点信息:")
    print(f"  - name: {gap_node.name}")
    print(f"  - description: {gap_node.description}")

    # ========================================
    # 3. 准备输入状态 (模拟 AdjudicationNode 的输出)
    # ========================================
    # 场景1: 证据充足
    mock_evidence_sufficient = [
        {
            "doc_id": "paper_001",
            "content": "RAG通过检索外部知识库来增强LLM的生成能力，解决了知识过时和幻觉问题。",
            "reason": "直接描述了RAG的核心原理和优势",
            "metadata": {"title": "RAG综述论文"}
        },
        {
            "doc_id": "paper_002",
            "content": "Self-RAG框架让模型学会自主决定何时检索以及如何反思检索结果。",
            "reason": "介绍了RAG的最新进展Self-RAG",
            "metadata": {"title": "Self-RAG论文"}
        }
    ]

    # 场景2: 证据不足 (只有1条)
    mock_evidence_insufficient = [
        {
            "doc_id": "paper_001",
            "content": "RAG模型结合了参数化和非参数化记忆。",
            "reason": "描述了RAG基本概念",
            "metadata": {"title": "RAG论文"}
        }
    ]

    # 选择测试场景
    use_sufficient = True  # 切换为 False 测试不足场景
    mock_evidence = mock_evidence_sufficient if use_sufficient else mock_evidence_insufficient

    input_state: Dict[str, Any] = {
        "user_query": "帮我全面介绍RAG检索增强生成技术",
        "informative_facets": [
            {
            "facet_id": "F1",
            "facet_type": "DEFINITION",
            "description": "RAG（Retrieval-Augmented Generation）的核心定义、基本工作流程和关键组成模块",
            "dependency": "null"
            }
        ],
        "verified_evidence": mock_evidence,
        "search_iteration": 0,  # 当前迭代次数
    }

    print(f"\n[INPUT] 用户查询: {input_state['user_query'][:50]}...")
    print(f"[INPUT] 已有证据数: {len(mock_evidence)}")
    print(f"[INPUT] 当前迭代: {input_state['search_iteration']}")

    # ========================================
    # 4. 调用 GapAnalysisNode.process()
    # ========================================
    print("\n[PROCESSING] 正在分析信息覆盖度...")
    start_time = time.time()

    try:
        output_state = gap_node.process(input_state)
        elapsed = time.time() - start_time

        print(f"\n[SUCCESS] 分析完成 (耗时: {elapsed:.2f}s)")

        # ========================================
        # 5. 查看分析结果
        # ========================================
        gap_result = output_state.get("gap_analysis_result")
        new_iteration = output_state.get("search_iteration")

        print(f"\n[OUTPUT] 分析结果:")
        print(f"  - gap_analysis_result: {gap_result}")
        print(f"  - search_iteration: {new_iteration}")

        if gap_result == "insufficient":
            print("\n[ACTION] 信息不足，需要回流到检索阶段!")
        else:
            print("\n[ACTION] 信息充足，可以进入报告生成阶段!")

    except Exception as e:
        print(f"\n[ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("[END] GapAnalysisNode 测试完成")
    print("=" * 60)


def run_iteration_limit_test():
    """
    测试迭代次数限制

    验证当达到最大迭代次数时，即使信息不足也会停止检索。
    """

    print("\n\n" + "=" * 60)
    print("[START] 迭代次数限制测试")
    print("=" * 60)

    config = CruxConfig(debug=True)
    config.search.max_iterations = 3

    gap_node = GapAnalysisNode(config)

    # 模拟已经迭代了2次的状态
    input_state = {
        "user_query": "复杂查询需要多轮检索",
        "verified_evidence": [{"content": "部分证据"}],
        "search_iteration": 2,  # 已经迭代2次
    }

    print(f"\n[INPUT] 当前迭代: {input_state['search_iteration']}")
    print(f"[CONFIG] 最大迭代: {config.search.max_iterations}")

    try:
        output = gap_node.process(input_state)
        print(f"\n[OUTPUT] gap_result: {output.get('gap_analysis_result')}")
        print(f"[OUTPUT] iteration: {output.get('search_iteration')}")
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    # 运行基础示例
    run_gap_analysis_example()

