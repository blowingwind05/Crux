"""
Query Router - 查询相关路由

处理管线查询请求
"""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.models import QueryRequest, PipelineResponse, StreamEvent
from backend.services import pipeline_service

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query")
async def query_crux(request: QueryRequest) -> PipelineResponse:
    """查询 Crux AgenticRAG（非流式）"""
    try:
        result = await pipeline_service.run_pipeline(request)
        
        return PipelineResponse(
            success=True,
            query=request.query,
            final_report=result.get("final_report"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_crux_stream(request: QueryRequest):
    """流式查询 Crux AgenticRAG"""
    
    async def generate():
        async for event in pipeline_service.stream_pipeline(request):
            yield f"data: {event.model_dump_json()}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
