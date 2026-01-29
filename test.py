"""
Crux AgenticRAG 框架入口

使用方法:
    python main.py
"""

import time
from src.crux import AgentGraph, CruxConfig


def main():
    # 创建配置
    config_dict = {
        "llm": {
            "api_key": "Empty",
            "base_url": "http://localhost:8000/v1",
            "model": "Qwen3-8B",
            "temperature": 0.7,
            "max_tokens": 32768
        },
        "search": {
            "max_iterations": 3,
            "top_k": 50,
            "use_bm25": True,
            "use_vector": True,
            "use_metadata_filter": True
        },
        "data_source": "json",
        "data_source_path": "data/ir_papers.json",
        "schema_type": "paper",
        "mock_llm": False,
        "debug": True,
    }

    config = CruxConfig.from_dict(config_dict)
    
    # 构建图
    graph = AgentGraph(config)
    app = graph.build()
    
    # 测试查询 - 论文检索场景
    user_query = "帮我找一下关于信息检索和 RAG 检索增强生成的最新研究，尤其是智能体相关的论文"
    
    print("=" * 60)
    print("[START] Crux AgenticRAG Demo")
    print("=" * 60)
    print(f"\n[QUERY] {user_query}\n")
    
    # 准备输入
    inputs = {
        "user_query": user_query,
        "verified_evidence": [],
        "search_iteration": 0,
        "schema_type": "paper",
        "start_time": time.time(),
    }
    
    # 运行图
    final_state = graph.invoke(inputs)
    
    # 输出结果
    print("\n" + final_state.get("final_report", "无报告生成"))


if __name__ == "__main__":
    main()
