import { useState, useCallback, useRef } from 'react';
import type { PipelineState, PipelineStage, StageOutput } from '@/types/crux';
import { initialStages } from '@/data/mockPipeline';


export function useCruxPipeline() {
  const [state, setState] = useState<PipelineState>({
    query: '',
    stages: initialStages.map(s => ({ ...s })),
    currentStageIndex: -1,
    iteration: 0,
    isRunning: false,
    isCompleted: false,
  });

  const abortRef = useRef(false);
  const stateRef = useRef(state);
  stateRef.current = state;

  const reset = useCallback(() => {
    abortRef.current = true;
    setState({
      query: '',
      stages: initialStages.map(s => ({ ...s, status: 'pending', output: undefined })),
      currentStageIndex: -1,
      iteration: 0,
      isRunning: false,
      isCompleted: false,
    });
  }, []);

  const updateStage = useCallback((
    stageIndex: number,
    updates: Partial<PipelineStage>
  ) => {
    setState(prev => ({
      ...prev,
      stages: prev.stages.map((s, i) =>
        i === stageIndex ? { ...s, ...updates } : s
      ),
    }));
  }, []);

  const runPipeline = useCallback(async (query: string) => {
    if (!query.trim()) return;

    abortRef.current = false;

    // Reset and start
    setState({
      query,
      stages: initialStages.map(s => ({ ...s, status: 'pending', output: undefined })),
      currentStageIndex: 0,
      iteration: 1,
      isRunning: true,
      isCompleted: false,
    });

    try {
      // 调用后端流式API
      const response = await fetch('/api/query/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          data_source_type: 'json',
          data_source_path: 'data/ir_papers.json',
          schema_path: 'config/paper_schema.yaml',
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
        buffer = lines.pop() || ''; // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'stage_complete') {
                const stageIndex = initialStages.findIndex(s => s.id === data.stage);
                if (stageIndex !== -1) {
                  setState(prev => ({
                    ...prev,
                    currentStageIndex: stageIndex,
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
                  }));
                }
              } else if (data.type === 'complete') {
                setState(prev => ({
                  ...prev,
                  isRunning: false,
                  isCompleted: true,
                  currentStageIndex: initialStages.length - 1,
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
