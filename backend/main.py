"""
Crux AgenticRAG Backend API

基于FastAPI的Crux AgenticRAG框架后端服务，
支持流式返回中间处理结果。
"""

import asyncio
import json
from typing import Dict, Any, Optional, AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.crux import AgentGraph, CruxConfig


class QueryRequest(BaseModel):
    """查询请求模型"""
    query: str
    data_source_type: str = "json"
    data_source_path: Optional[str] = None
    schema_path: Optional[str] = None  # YAML schema 配置文件路径
    mock_llm: bool = True
    debug: bool = False


class PipelineUpdate(BaseModel):
    """管线更新模型"""
    stage: str
    status: str
    data: Optional[Dict[str, Any]] = None
    timestamp: float


# 全局变量存储Agent实例
agent_instances: Dict[str, AgentGraph] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 Starting Crux AgenticRAG Backend")
    yield
    # 关闭时清理
    agent_instances.clear()
    print("🛑 Shutting down Crux AgenticRAG Backend")


app = FastAPI(
    title="Crux AgenticRAG API",
    description="基于意图深度感知的AgenticRAG框架API服务",
    version="0.1.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # 前端开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_or_create_agent(request: QueryRequest) -> AgentGraph:
    """获取或创建Agent实例"""
    key = f"{request.data_source_type}_{request.data_source_path}_{request.schema_path}"

    if key not in agent_instances:
        config = CruxConfig(
            data_source_type=request.data_source_type,
            data_source_path=request.data_source_path or "data/ir_papers.json",
            schema_path=request.schema_path or "data/paper_schema.yaml",
            mock_llm=request.mock_llm,
            debug=request.debug,
        )
        agent = AgentGraph(config)
        agent.build()
        agent_instances[key] = agent

    return agent_instances[key]


async def process_pipeline_stream(request: QueryRequest) -> AsyncGenerator[str, None]:
    """处理管线并流式返回结果"""

    try:
        # 创建Agent实例
        agent = get_or_create_agent(request)

        # 准备输入
        inputs = {
            "user_query": request.query,
            "verified_evidence": [],
            "search_iteration": 0,
            "start_time": asyncio.get_event_loop().time(),
        }

        # 发送初始状态
        yield f"data: {json.dumps({'type': 'start', 'message': '开始处理查询...'})}\n\n"

        # 使用agent的stream方法进行流式处理
        async def run_stream():
            for event in agent.stream(inputs):
                # 解析事件类型和数据
                for node_name, state in event.items():
                    if node_name == "understand":
                        yield f"data: {json.dumps({'type': 'stage_complete', 'stage': 'understand', 'output': state.get('intent_object', {})})}\n\n"
                    elif node_name == "retrieve":
                        candidates = state.get("candidates", [])
                        yield f"data: {json.dumps({'type': 'stage_complete', 'stage': 'retrieve', 'output': {'candidates': candidates, 'total_retrieved': len(candidates), 'retrieval_methods': ['BM25', 'Vector', 'Field Filter']}})}\n\n"
                    elif node_name == "judge":
                        evidence = state.get("verified_evidence", [])
                        yield f"data: {json.dumps({'type': 'stage_complete', 'stage': 'judge', 'output': {'verified_evidence': evidence, 'rejected_count': 0, 'acceptance_rate': 1.0}})}\n\n"
                    elif node_name == "analyze":
                        gap_result = state.get("gap_analysis_result", {})
                        yield f"data: {json.dumps({'type': 'stage_complete', 'stage': 'analyze', 'output': gap_result})}\n\n"
                    elif node_name == "report":
                        report = state.get("final_report", "")
                        yield f"data: {json.dumps({'type': 'stage_complete', 'stage': 'report', 'output': {'summary': report, 'key_findings': [], 'confidence_score': 0.9, 'citations': []}})}\n\n"
                await asyncio.sleep(0.1)  # 小延迟避免阻塞

        # 运行流式处理
        async for chunk in run_stream():
            yield chunk

        # 发送完成状态
        yield f"data: {json.dumps({'type': 'complete', 'message': '处理完成'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


def generate_mock_stage_output(stage: str, query: str) -> Dict[str, Any]:
    """生成模拟的阶段输出（临时使用）"""
    if stage == "understand":
        return {
            "user_goal": "INVESTIGATIVE",
            "constraints": {
                "structured_metadata": [{"field": "category", "operator": "in", "value": ["AI", "RAG"]}],
                "unstructured_content_patterns": [{"pattern": "RAG", "pattern_type": "exact_phrase"}]
            },
            "keywords_bm25": ["RAG", "检索增强生成", "Agentic"],
            "queries_vector": [query],
            "rubric": "文档需直接回答用户查询"
        }
    elif stage == "retrieve":
        return {
            "candidates": [
                {"doc_id": "doc_1", "title": "AgenticRAG论文1", "score": 0.95},
                {"doc_id": "doc_2", "title": "AgenticRAG论文2", "score": 0.89}
            ],
            "total_retrieved": 50,
            "retrieval_methods": ["BM25", "Vector", "Field Filter"]
        }
    elif stage == "judge":
        return {
            "verified_evidence": [
                {"doc_id": "doc_1", "content": "证据内容...", "relevance_score": 0.92}
            ],
            "rejected_count": 25,
            "acceptance_rate": 0.5
        }
    elif stage == "analyze":
        return {
            "status": "sufficient",
            "coverage_score": 0.92,
            "missing_facets": [],
            "iteration": 1
        }
    elif stage == "report":
        return {
            "summary": f"基于查询'{query}'的分析结果...",
            "key_findings": ["发现1", "发现2"],
            "confidence_score": 0.89,
            "citations": ["论文1", "论文2"]
        }
    return {}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "Crux AgenticRAG API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


@app.post("/api/query")
async def query_crux(request: QueryRequest):
    """查询Crux AgenticRAG（非流式）"""
    try:
        agent = get_or_create_agent(request)

        inputs = {
            "user_query": request.query,
            "verified_evidence": [],
            "search_iteration": 0,
            "start_time": asyncio.get_event_loop().time(),
        }

        result = agent.invoke(inputs)
        return {"success": True, "result": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query/stream")
async def query_crux_stream(request: QueryRequest):
    """流式查询Crux AgenticRAG"""
    return StreamingResponse(
        process_pipeline_stream(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/config/default")
async def get_default_config():
    """获取默认配置"""
    config = CruxConfig()
    return {
        "data_source_type": config.data_source_type,
        "schema_path": config.schema_path or "config/paper_schema.yaml",
        "mock_llm": config.mock_llm,
        "debug": config.debug,
        "llm": {
            "model": config.llm.model,
            "temperature": config.llm.temperature,
            "max_tokens": config.llm.max_tokens
        },
        "search": {
            "max_iterations": config.search.max_iterations,
            "top_k": config.search.top_k,
            "use_bm25": config.search.use_bm25,
            "use_vector": config.search.use_vector,
            "use_metadata_filter": config.search.use_metadata_filter
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
