"""
Crux AgenticRAG 框架入口

使用方法:
    python main.py
"""

import time
from src.crux import AgentGraph, load_config


def main():
    # 从配置文件加载配置（优先读取 config.yaml）
    # 如果没有配置文件，则使用默认值
    config = load_config()
    
    # 或者手动指定配置文件路径:
    # config = load_config("path/to/config.yaml")
    
    # 打印加载的配置信息
    print(f"[CONFIG] 数据源: {config.data_source_type}")
    print(f"[CONFIG] 数据路径: {config.data_source_path}")
    print(f"[CONFIG] LLM 模型: {config.llm.model}")
    print(f"[CONFIG] Mock LLM: {config.mock_llm}")
    print(f"[CONFIG] Debug: {config.debug}")
    
    # 构建图
    graph = AgentGraph(config)
    graph.save_graph_image(graph.build(), "graph.png")
    
    # 测试查询 - 论文检索场景
    user_query = "帮我找一下关于2025年信息检索和 RAG 检索增强生成的最新研究，尤其是智能体相关的论文"
    
    print("=" * 60)
    print("[START] Crux AgenticRAG Demo")
    print("=" * 60)
    print(f"\n[QUERY] {user_query}\n")
    
    # 准备输入
    inputs = {
        "user_query": user_query,
        "verified_evidence": [],
        "search_iteration": 0,
        "start_time": time.time(),
    }
    
    # 运行图
    final_state = graph.invoke(inputs)
    
    # 输出结果
    print("\n" + final_state.get("final_report", "无报告生成"))


if __name__ == "__main__":
    main()
