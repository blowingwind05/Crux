"""
UnderstandingNode 独立运行示例

用于单独测试意图理解模块，不依赖完整的 AgentGraph。

使用方法:
    python -m src.crux.tests.example_understanding_node
    
    或在项目根目录下:
    python src/crux/tests/example_understanding_node.py
"""

import json
import time
from typing import Dict, Any

from src.crux.config import CruxConfig
from src.crux.modules.understanding import UnderstandingNode


def run_understanding_example():
    """
    单独运行 UnderstandingNode 的示例
    
    这个示例展示了如何：
    1. 创建配置
    2. 初始化 UnderstandingNode
    3. 构造输入状态
    4. 调用节点处理函数
    5. 查看输出结果
    """
    
    print("=" * 60)
    print("[START] UnderstandingNode 独立测试")
    print("=" * 60)
    
    # ========================================
    # 1. 创建配置
    # ========================================
    config = CruxConfig(
        data_source_type="json",
        data_source_path="data/ir_papers.json",
        schema_type="paper",
        mock_llm=False,  # 设为 True 可使用 mock 响应进行测试
        debug=True,
    )
    
    print(f"\n[CONFIG] 配置信息:")
    print(f"  - data_source_type: {config.data_source_type}")
    print(f"  - schema_type: {config.schema_type}")
    print(f"  - mock_llm: {config.mock_llm}")
    print(f"  - debug: {config.debug}")
    
    # ========================================
    # 2. 初始化 UnderstandingNode
    # ========================================
    understanding_node = UnderstandingNode(config)
    
    print(f"\n[NODE] 节点信息:")
    print(f"  - name: {understanding_node.name}")
    print(f"  - description: {understanding_node.description}")
    
    # ========================================
    # 3. 准备输入状态 (模拟 AgentState)
    # ========================================
    # 注意：UnderstandingNode 只需要 user_query 和可选的 schema_type
    test_query = "帮我找一下关于信息检索和 RAG 检索增强生成的最新研究，尤其是智能体相关的论文"
    
    input_state: Dict[str, Any] = {
        "user_query": test_query,
        "verified_evidence": [],
        "search_iteration": 0,
        "schema_type": "paper",
        "start_time": time.time(),
    }
    
    print(f"\n[INPUT] 用户查询:")
    print(f"  {test_query}")
    
    # ========================================
    # 4. 调用 UnderstandingNode.process()
    # ========================================
    print("\n[PROCESSING] 正在处理...")
    start_time = time.time()
    
    try:
        output_state = understanding_node.process(input_state)
        elapsed = time.time() - start_time
        
        print(f"\n[SUCCESS] 处理完成 (耗时: {elapsed:.2f}s)")
        
        # ========================================
        # 5. 查看输出结果
        # ========================================
        print("\n[OUTPUT] 返回的状态更新:")
        print(f"  - search_iteration: {output_state.get('search_iteration')}")
        print(f"  - verified_evidence count: {len(output_state.get('verified_evidence', []))}")
        
        # 打印意图对象
        intent = output_state.get("intent", {})
        print("\n[INTENT] 解析的意图对象:")
        print(json.dumps(intent, ensure_ascii=False, indent=2))
        
        # 详细展示关键字段
        print("\n[DETAIL] 关键字段解析:")
        print(f"  - user_goal: {intent.get('user_goal')}")
        print(f"  - keywords_bm25: {intent.get('keywords_bm25')}")
        print(f"  - queries_vector: {intent.get('queries_vector')}")
        print(f"  - rubric: {intent.get('rubric')}")
        
        constraints = intent.get("constraints", {})
        print(f"  - structured_metadata: {constraints.get('structured_metadata', [])}")
        
    except Exception as e:
        print(f"\n[ERROR] 处理失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[END] UnderstandingNode 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    # 运行基础示例
    run_understanding_example()
    

