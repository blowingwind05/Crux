from graph import build_graph

def main():
    app = build_graph()
    
    # 测试查询：故意设计一个复杂的，看看能否触发 Mock DB 的 hit
    user_query = "帮我找一下2023年以后关于比亚迪销量和特斯拉FSD里程的数据，最好有具体数字。"
    
    print(f"[START] 启动 Zhiji Agent... 查询: {user_query}")
    
    inputs = {
        "user_query": user_query,
        "verified_evidence": [], # 初始化
        "search_iteration": 0
    }
    
    # 运行图
    final_state = app.invoke(inputs)
    
    print("\n" + "="*30)
    print("[SUCCESS] 最终执行结果")
    print("="*30)
    print(final_state["final_report"])

if __name__ == "__main__":
    main()
