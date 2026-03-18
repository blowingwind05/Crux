"""
Pipeline Service - 管线服务

封装 Agent 调用和状态管理逻辑，支持实时流式日志推送
"""

import asyncio
import time
from typing import Dict, Any, AsyncGenerator, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from src.crux import AgentGraph, CruxConfig, load_config
from src.crux.utils.callback import StreamCallback, set_global_callback
from backend.models import (
    QueryRequest,
    StageLogEntry,
    ExecutionStats,
    StreamEvent,
)


class PipelineService:
    """管线服务 - 管理 Agent 实例和执行流程"""
    
    def __init__(self):
        self._agent_cache: Dict[str, AgentGraph] = {}
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def _get_cache_key(self, request: QueryRequest) -> str:
        """生成缓存键"""
        return f"{request.data_source_type}_{request.data_source_path}_{request.schema_path}"
    
    def get_or_create_agent(self, request: QueryRequest) -> AgentGraph:
        """获取或创建 Agent 实例"""
        key = self._get_cache_key(request)
        
        if key not in self._agent_cache:
            # 首先尝试从配置文件加载基础配置
            config = load_config("/workspace/crux/Crux/config_arxiv_full.yaml")
            
            # 根据请求参数覆盖配置
            # if request.data_source_type:
            #     config.data_source_type = request.data_source_type
            if request.data_source_path:
                config.data_source_path = request.data_source_path
            if request.schema_path:
                config.schema_path = request.schema_path
            if request.mock_llm is not None:
                config.mock_llm = request.mock_llm
            if request.debug is not None:
                config.debug = request.debug
            
            agent = AgentGraph(config)
            agent.build()
            self._agent_cache[key] = agent
        
        return self._agent_cache[key]
    
    def clear_cache(self):
        """清空 Agent 缓存"""
        self._agent_cache.clear()
    
    async def stream_pipeline(self, request: QueryRequest) -> AsyncGenerator[StreamEvent, None]:
        """
        流式运行管线 - 支持实时日志推送
        
        使用回调机制在节点执行过程中实时收集和推送日志
        """
        start_time = time.time()
        stats = ExecutionStats()
        current_iteration = -1  # Start at -1 so first iteration (0) triggers iteration_start
        
        # 创建回调收集器
        callback = StreamCallback()
        set_global_callback(callback)
        
        try:
            agent = self.get_or_create_agent(request)
            
            inputs = {
                "user_query": request.query,
                "verified_evidence": [],
                "search_iteration": 0,
                "start_time": start_time,
            }
            
            # 发送开始事件
            yield StreamEvent(
                type="start",
                message="开始处理查询...",
                iteration=current_iteration,
            )
            
            # 使用线程池运行 LangGraph（因为它是同步的）
            loop = asyncio.get_event_loop()
            
            # 创建异步生成器来处理流式输出
            stream_queue: asyncio.Queue = asyncio.Queue()
            
            async def process_stream():
                """在后台处理 LangGraph stream"""
                def run_stream():
                    try:
                        for event in agent.stream(inputs):
                            stream_queue.put_nowait(("event", event))
                        stream_queue.put_nowait(("done", None))
                    except Exception as e:
                        stream_queue.put_nowait(("error", e))
                
                await loop.run_in_executor(self._executor, run_stream)
            
            # 启动后台流处理
            stream_task = asyncio.create_task(process_stream())
            
            last_stage = None
            
            while True:
                # 1. 先检查并推送所有待处理的日志（实时）
                pending_logs = callback.get_pending_logs()
                for log_event in pending_logs:
                    yield StreamEvent(
                        type="stage_log",
                        stage=log_event.stage,
                        log=StageLogEntry(
                            level=log_event.level,
                            message=log_event.message,
                            timestamp=log_event.timestamp,
                            details=log_event.details,
                        ),
                        iteration=log_event.iteration,
                    )
                
                # 2. 检查是否有新的节点完成事件
                try:
                    msg_type, data = await asyncio.wait_for(
                        stream_queue.get(), 
                        timeout=0.05  # 50ms 轮询间隔
                    )
                    
                    if msg_type == "done":
                        break
                    elif msg_type == "error":
                        raise data
                    elif msg_type == "event":
                        for node_name, state in data.items():
                            # 检测新迭代 - 每次进入 retrieve 节点就是新一轮迭代
                            # 注意：不能使用 state.search_iteration，因为它在 analyze 完成后才更新
                            if node_name == "retrieve":
                                current_iteration += 1
                                callback.set_iteration(current_iteration)
                                yield StreamEvent(
                                    type="iteration_start",
                                    message=f"开始第 {current_iteration + 1} 轮迭代",
                                    iteration=current_iteration,
                                )
                            
                            # 发送阶段开始（如果是新阶段）
                            if last_stage != node_name:
                                yield StreamEvent(
                                    type="stage_start",
                                    stage=node_name,
                                    message=f"正在执行 {node_name}...",
                                    iteration=current_iteration,
                                )
                                last_stage = node_name
                            
                            # 推送该节点执行期间产生的所有剩余日志
                            remaining_logs = callback.get_pending_logs()
                            for log_event in remaining_logs:
                                yield StreamEvent(
                                    type="stage_log",
                                    stage=log_event.stage,
                                    log=StageLogEntry(
                                        level=log_event.level,
                                        message=log_event.message,
                                        timestamp=log_event.timestamp,
                                        details=log_event.details,
                                    ),
                                    iteration=log_event.iteration,
                                )
                            
                            # 构建阶段输出
                            output = self._build_stage_output(node_name, state, stats)
                            
                            # 发送阶段完成
                            yield StreamEvent(
                                type="stage_complete",
                                stage=node_name,
                                output=output,
                                stats=stats,
                                iteration=current_iteration,
                            )
                            
                except asyncio.TimeoutError:
                    # 超时只是继续循环，检查更多日志
                    continue
            
            # 等待后台任务完成
            await stream_task
            
            # 更新最终统计
            stats.processing_time_ms = (time.time() - start_time) * 1000
            stats.iteration_count = current_iteration + 1
            
            # 发送完成事件
            yield StreamEvent(
                type="complete",
                message="处理完成",
                stats=stats,
                iteration=current_iteration,
            )
            
        except Exception as e:
            yield StreamEvent(
                type="error",
                message=str(e),
            )
        finally:
            # 清理回调
            callback.close()
            set_global_callback(None)
    
    def _build_stage_output(
        self, 
        stage: str, 
        state: Dict[str, Any],
        stats: ExecutionStats
    ) -> Dict[str, Any]:
        """构建阶段输出"""
        
        if stage == "understand":
            intent = state.get("intent_object", state.get("intent", {}))
            return {
                "user_goal": intent.get("cognitive_strategy", {}).get("user_goal", "FACTUAL"),
                "cognitive_strategy": intent.get("cognitive_strategy"),
                "constraints": intent.get("constraints", {}),
                "information_facets": intent.get("information_facets", []),
                "keywords_bm25": self._extract_keywords(intent),
                "queries_vector": self._extract_queries(intent),
                "rubric": intent.get("judgement_rubric", {}).get("criteria_positive", ""),
            }
        
        elif stage == "retrieve":
            candidates = state.get("candidate_docs", [])
            stats.total_candidates = len(candidates)
            
            formatted_candidates = []
            for doc in candidates[:20]:
                formatted_candidates.append({
                    "doc_id": doc.get("id", doc.get("arxiv_id", "unknown")),
                    "title": doc.get("title", ""),
                    "abstract": doc.get("abstract", "")[:300] + "..." if len(doc.get("abstract", "")) > 300 else doc.get("abstract", ""),
                    "score": doc.get("score", 0.0),
                    "source": doc.get("source", "hybrid"),
                    "authors": doc.get("authors", []),
                    "year": doc.get("year") or doc.get("metadata", {}).get("date", ""),
                    "url": doc.get("arxiv_url", ""),
                })
            
            return {
                "candidates": formatted_candidates,
                "total_retrieved": len(candidates),
                "iteration": state.get("search_iteration", 0),
            }
        
        elif stage == "judge":
            evidence = state.get("verified_evidence", [])
            stats.verified_count = len(evidence)
            
            # 获取所有候选文档和被拒绝的文档
            all_candidates = state.get("candidate_docs", [])
            verified_doc_ids = {ev.get("doc_id") for ev in evidence}
            
            formatted_evidence = []
            for ev in evidence:
                formatted_evidence.append({
                    "doc_id": ev.get("doc_id", "unknown"),
                    "content": ev.get("content", ""),
                    "reason": ev.get("reason", ""),
                    "source": ev.get("source", "unknown"),
                    "relevance_score": ev.get("relevance_score", 0.8),
                    "facet_id": ev.get("facet_id"),
                    "metadata": ev.get("metadata", {}),
                })
            
            # 构建被拒绝的文档列表
            rejected_docs = state.get("rejected_docs", [])
            formatted_rejected = []
            for doc in rejected_docs:
                formatted_rejected.append({
                    "doc_id": doc.get("doc_id", doc.get("id", "unknown")),
                    "title": doc.get("title", ""),
                    "reason": doc.get("reason", "不符合研判准则"),
                    "abstract": doc.get("abstract", "")[:200] if doc.get("abstract") else "",
                })
            
            # 如果没有显式的 rejected_docs，从 candidates 推断
            if not formatted_rejected:
                for doc in all_candidates:
                    doc_id = doc.get("id", doc.get("arxiv_id", "unknown"))
                    if doc_id not in verified_doc_ids:
                        formatted_rejected.append({
                            "doc_id": doc_id,
                            "title": doc.get("title", ""),
                            "reason": "未通过深度研判",
                            "abstract": doc.get("abstract", "")[:200] if doc.get("abstract") else "",
                        })
            
            stats.rejected_count = len(formatted_rejected)
            
            return {
                "verified_evidence": formatted_evidence,
                "rejected_docs": formatted_rejected,
                "new_evidence_count": len(formatted_evidence),
                "total_evidence": len(evidence),
                "iteration": state.get("search_iteration", 0),
            }
        
        elif stage == "analyze":
            gap_result = state.get("gap_analysis_result", "sufficient")
            iteration = state.get("search_iteration", 0)
            stats.iteration_count = iteration
            
            # 获取缺口分析的详细信息
            gap_details = state.get("gap_analysis_details", {})
            coverage_score = gap_details.get("coverage_score", 0.8 if gap_result == "sufficient" else 0.5)
            missing_info = gap_details.get("missing_info", "")
            
            return {
                "status": gap_result,
                "should_loop_back": gap_result == "insufficient",
                "iteration": iteration,
                "max_iterations": 3,
                "coverage_score": coverage_score,
                "missing_info": missing_info,
            }
        
        elif stage == "report":
            report = state.get("final_report", "")
            evidence = state.get("verified_evidence", [])
            
            return {
                "summary": report if isinstance(report, str) else str(report),
                "key_findings": self._extract_findings(evidence),
                "evidence_chain": [
                    {
                        "doc_id": ev.get("doc_id", ""),
                        "content": ev.get("content", ""),
                        "reason": ev.get("reason", ""),
                    }
                    for ev in evidence[:5]
                ],
                "confidence_score": 0.9 if evidence else 0.5,
                "citations": [ev.get("doc_id", "") for ev in evidence],
                "total_iterations": stats.iteration_count,
            }
        
        return {}
    
    def _extract_keywords(self, intent: Dict[str, Any]) -> List[str]:
        """从意图中提取 BM25 关键词"""
        retrieval = intent.get("retrieval_execution", {})
        sparse = retrieval.get("sparse_keywords", [])
        return [kw.get("term", kw) if isinstance(kw, dict) else str(kw) for kw in sparse]
    
    def _extract_queries(self, intent: Dict[str, Any]) -> List[str]:
        """从意图中提取向量查询"""
        retrieval = intent.get("retrieval_execution", {})
        return retrieval.get("dense_queries", [])
    
    def _extract_findings(self, evidence: List[Dict[str, Any]]) -> List[str]:
        """从证据中提取关键发现"""
        findings = []
        for ev in evidence[:5]:
            reason = ev.get("reason", "")
            if reason:
                findings.append(reason)
        return findings


# 服务单例
pipeline_service = PipelineService()
