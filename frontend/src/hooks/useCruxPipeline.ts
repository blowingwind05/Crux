import { useState, useCallback, useRef } from 'react';
import type {
  PipelineState,
  PipelineStage,
  StageLog,
  ExecutionStats,
  IterationResult,
  CandidateDoc,
  Evidence,
  RejectedDoc,
  StageId,
} from '@/types/crux';
import { initialStages } from '@/data/mockPipeline';


const createInitialState = (): PipelineState => ({
  query: '',
  stages: initialStages.map(s => ({ ...s, status: 'pending', output: undefined, logs: [] })),
  currentStageIndex: -1,
  currentStage: null,
  iteration: 0,
  isRunning: false,
  isCompleted: false,
  stats: {
    totalCandidates: 0,
    verifiedCount: 0,
    rejectedCount: 0,
    tokensUsed: 0,
    processingTimeMs: 0,
    iterationCount: 0,
  },
  allLogs: [],
  iterations: [],
});


export function useCruxPipeline() {
  const [state, setState] = useState<PipelineState>(createInitialState());

  const abortRef = useRef(false);

  const reset = useCallback(() => {
    abortRef.current = true;
    setState(createInitialState());
  }, []);

  const runPipeline = useCallback(async (query: string) => {
    if (!query.trim()) return;

    abortRef.current = false;

    // Reset and start
    setState({
      ...createInitialState(),
      query,
      currentStageIndex: 0,
      iteration: 0,
      isRunning: true,
    });

    try {
      const response = await fetch('/api/query/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          data_source_type: 'json',
          // 留空让后端从 config.yaml 文件读取默认值
          data_source_path: '',
          schema_path: '',
          mock_llm: false,
          debug: false,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('Failed to get response reader');
      }

      let buffer = '';

      while (!abortRef.current) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              const eventIteration = data.iteration ?? 0;

              if (data.type === 'start') {
                // 开始事件
                setState(prev => ({
                  ...prev,
                  isRunning: true,
                  iteration: 0,
                }));
              } else if (data.type === 'iteration_start') {
                // 新一轮迭代开始
                setState(prev => ({
                  ...prev,
                  iteration: eventIteration,
                  // 重置当前轮次的阶段状态
                  stages: prev.stages.map(s => {
                    if (['retrieve', 'judge', 'analyze'].includes(s.id)) {
                      return { ...s, status: 'pending' as const, output: undefined };
                    }
                    return s;
                  }),
                }));
              } else if (data.type === 'stage_start') {
                // 阶段开始
                const stageIndex = initialStages.findIndex(s => s.id === data.stage);
                if (stageIndex !== -1) {
                  setState(prev => ({
                    ...prev,
                    currentStageIndex: stageIndex,
                    currentStage: data.stage as StageId,
                    stages: prev.stages.map((s, i) =>
                      i === stageIndex
                        ? { ...s, status: 'processing' as const, startTime: Date.now() }
                        : s
                    ),
                  }));
                }
              } else if (data.type === 'stage_log') {
                // 实时日志 - 追加到 allLogs
                if (data.log) {
                  const newLog: StageLog = {
                    level: data.log.level || 'INFO',
                    message: data.log.message || '',
                    timestamp: data.log.timestamp || Date.now() / 1000,
                    details: data.log.details,
                    iteration: eventIteration,
                  };

                  setState(prev => ({
                    ...prev,
                    allLogs: [...prev.allLogs, newLog],
                    // 同时追加到对应阶段的 logs
                    stages: prev.stages.map(s =>
                      s.id === data.stage
                        ? { ...s, logs: [...(s.logs || []), newLog] }
                        : s
                    ),
                  }));
                }
              } else if (data.type === 'stage_complete') {
                // 阶段完成
                const stageIndex = initialStages.findIndex(s => s.id === data.stage);
                if (stageIndex !== -1) {
                  const newStats = data.stats ? {
                    totalCandidates: data.stats.total_candidates ?? 0,
                    verifiedCount: data.stats.verified_count ?? 0,
                    rejectedCount: data.stats.rejected_count ?? 0,
                    tokensUsed: data.stats.tokens_used ?? 0,
                    processingTimeMs: data.stats.processing_time_ms ?? 0,
                    iterationCount: data.stats.iteration_count ?? 1,
                  } : undefined;

                  setState(prev => {
                    // 更新迭代结果
                    let newIterations = [...prev.iterations];

                    // Debug log
                    console.log('[SSE] stage_complete', {
                      stage: data.stage,
                      iteration: eventIteration,
                      output: data.output,
                      currentIterationsLength: newIterations.length
                    });

                    if (data.stage === 'retrieve' && data.output?.candidates) {
                      // 确保迭代数组足够长
                      while (newIterations.length <= eventIteration) {
                        newIterations.push({
                          iteration: newIterations.length,
                          candidates: [],
                          evidence: [],
                          rejectedDocs: [],
                        });
                      }
                      newIterations[eventIteration] = {
                        ...newIterations[eventIteration],
                        candidates: data.output.candidates as CandidateDoc[],
                      };
                      console.log('[SSE] retrieve - updated iterations', newIterations);
                    }

                    // Judge stage - 支持空 evidence 的情况
                    if (data.stage === 'judge') {
                      while (newIterations.length <= eventIteration) {
                        newIterations.push({
                          iteration: newIterations.length,
                          candidates: [],
                          evidence: [],
                          rejectedDocs: [],
                        });
                      }
                      const evidence = data.output?.verified_evidence || [];
                      const rejectedDocs = data.output?.rejected_docs || [];
                      newIterations[eventIteration] = {
                        ...newIterations[eventIteration],
                        evidence: evidence as Evidence[],
                        rejectedDocs: rejectedDocs as RejectedDoc[],
                      };
                      console.log('[SSE] judge - updated iterations', {
                        evidence: evidence.length,
                        rejected: rejectedDocs.length,
                        newIterations
                      });
                    }

                    if (data.stage === 'analyze' && data.output?.status) {
                      while (newIterations.length <= eventIteration) {
                        newIterations.push({
                          iteration: newIterations.length,
                          candidates: [],
                          evidence: [],
                          rejectedDocs: [],
                        });
                      }
                      newIterations[eventIteration] = {
                        ...newIterations[eventIteration],
                        gapStatus: data.output.status,
                        gapReason: data.output.missing_info || '',
                        coverageScore: data.output.coverage_score,
                      };
                    }

                    return {
                      ...prev,
                      stats: newStats || prev.stats,
                      iterations: newIterations,
                      stages: prev.stages.map((s, i) =>
                        i === stageIndex
                          ? {
                            ...s,
                            status: 'completed' as const,
                            endTime: Date.now(),
                            output: data.output
                          }
                          : s
                      ),
                    };
                  });
                }
              } else if (data.type === 'complete') {
                // 完成
                const finalStats = data.stats ? {
                  totalCandidates: data.stats.total_candidates ?? 0,
                  verifiedCount: data.stats.verified_count ?? 0,
                  rejectedCount: data.stats.rejected_count ?? 0,
                  tokensUsed: data.stats.tokens_used ?? 0,
                  processingTimeMs: data.stats.processing_time_ms ?? 0,
                  iterationCount: data.stats.iteration_count ?? 1,
                } : undefined;

                setState(prev => ({
                  ...prev,
                  isRunning: false,
                  isCompleted: true,
                  stats: finalStats || prev.stats,
                }));
              } else if (data.type === 'error') {
                throw new Error(data.message);
              }
            } catch (parseError) {
              console.warn('Failed to parse SSE data:', line, parseError);
            }
          }
        }
      }

      reader.releaseLock();

    } catch (error) {
      console.error('Pipeline execution error:', error);
      setState(prev => ({
        ...prev,
        isRunning: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      }));
    }
  }, []);

  return {
    state,
    runPipeline,
    reset,
  };
}
