import json
import os
import datetime
from openai import OpenAI
from dotenv import load_dotenv

from state import AgentState, IntentObject
from prompts import INTENT_PARSING_PROMPT, ADJUDICATION_PROMPT, GAP_ANALYSIS_PROMPT
from mock_db import mock_hybrid_search

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def call_llm_json(prompt: str, model="Qwen/Qwen3-32B"):
    """辅助函数：调用 LLM 并强制返回 JSON"""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=8192,
        temperature=0.1,
        top_p=0.8,
        presence_penalty=0,
        stream=False,
        extra_body={
            "top_k": 20,
            "chat_template_kwargs": {"enable_thinking": False},
            },
    )
    return json.loads(response.choices[0].message.content)

# --- Module 1: Schema-Aware Understanding ---
def node_understanding(state: AgentState):
    print("\n🔹 [1. Brain] 正在解析意图...")
    query = state["user_query"]
    current_time = datetime.datetime.now().strftime("%Y-%m-%d")
    
    prompt = INTENT_PARSING_PROMPT.replace("{{current_date}}", current_time).replace("{{user_query}}", query)

    
    # 调用 LLM 生成结构化意图
    intent_json = call_llm_json(prompt)
    
    # 这里应该做 Pydantic 校验，为简化直接传字典
    print(f"   解析结果: {json.dumps(intent_json, ensure_ascii=False, indent=2)}")
    
    return {
        "intent": intent_json,
        "search_iteration": 0,
        "verified_evidence": [] # 初始化证据列表
    }

# --- Module 2: Hybrid Retrieval ---
def node_retrieval(state: AgentState):
    print("\n🔹 [2. Hunter] 正在执行混合召回...")
    intent = state["intent"]
    
    # 解包意图参数
    keywords = intent.get("keywords_bm25", [])
    vector_qs = intent.get("queries_vector", [])
    constraints = intent.get("constraints", [])
    
    # 调用模拟数据库 (实际项目中这里接 ES/Milvus)
    docs = mock_hybrid_search(keywords, vector_qs, constraints)
    
    return {"candidate_docs": docs}

# --- Module 3: Deep Adjudication ---
def node_adjudication(state: AgentState):
    print("\n🔹 [3. Sniper] 正在进行深度研判...")
    docs = state["candidate_docs"]
    rubric = state["intent"]["rubric"]
    
    new_evidence = []
    
    for doc in docs:
        prompt = ADJUDICATION_PROMPT.format(rubric=rubric, doc_content=doc["content"])
        result = call_llm_json(prompt)
        
        if result.get("is_relevant"):
            print(f"   ✅ 采纳证据 (ID: {doc['id']}): {result.get('evidence')}")
            new_evidence.append({
                "doc_id": doc["id"],
                "content": result.get("evidence"),
                "reason": result.get("reason")
            })
        else:
            print(f"   ❌ 拒绝噪音 (ID: {doc['id']})")
            
    return {"verified_evidence": new_evidence} # LangGraph 会自动 append

# --- Module 4: Gap Analysis & Strategy ---
def node_gap_analysis(state: AgentState):
    print("\n🔹 [4. Strategist] 分析信息覆盖度...")
    evidence = state["verified_evidence"]
    query = state["user_query"]
    
    # 格式化证据给 LLM 看
    evidence_text = "\n".join([f"- {e['content']}" for e in evidence])
    
    prompt = GAP_ANALYSIS_PROMPT.format(query=query, evidence=evidence_text)
    analysis = call_llm_json(prompt)
    
    iteration = state["search_iteration"] + 1
    
    if analysis["status"] == "insufficient" and iteration < 3:
        print(f"   ⚠️ 发现缺口: {analysis.get('missing_info')}, 准备回流...")
        return {
            "gap_analysis_result": "insufficient",
            "search_iteration": iteration
            # 实际项目中，这里应该更新 state['intent'] 以聚焦缺失的信息
        }
    else:
        print("   🎉 信息充足或达到最大迭代次数。")
        return {
            "gap_analysis_result": "sufficient",
            "search_iteration": iteration
        }

# --- Final Report Generation ---
def node_report(state: AgentState):
    print("\n📝 [Final] 生成最终报告...")
    evidence = state["verified_evidence"]
    # 简单拼接，实际可用 LLM 生成漂亮报告
    report = f"基于对 {len(evidence)} 条关键证据的分析，结论如下：\n"
    for idx, e in enumerate(evidence, 1):
        report += f"{idx}. {e['content']} (来源: Doc {e['doc_id']})\n"
        
    return {"final_report": report}
