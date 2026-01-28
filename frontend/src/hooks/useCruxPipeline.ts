import { useState, useCallback, useRef } from 'react';
import type { PipelineState, PipelineStage, StageOutput } from '@/types/crux';
import { 
  initialStages, 
  generateMockIntent, 
  generateMockCandidates,
  generateMockEvidence,
  generateMockGapAnalysis,
  generateMockReport
} from '@/data/mockPipeline';

const STAGE_DELAYS = {
  understand: 1500,
  retrieve: 2000,
  judge: 1800,
  analyze: 1200,
  report: 1500,
};

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

    let iteration = 1;
    let intentOutput: ReturnType<typeof generateMockIntent> | null = null;
    let candidatesOutput: ReturnType<typeof generateMockCandidates> | null = null;
    let evidenceOutput: ReturnType<typeof generateMockEvidence> | null = null;
    let gapOutput: ReturnType<typeof generateMockGapAnalysis> | null = null;

    const processStage = async (stageIndex: number): Promise<boolean> => {
      if (abortRef.current) return false;

      const stageId = initialStages[stageIndex].id;
      
      // Set processing
      setState(prev => ({
        ...prev,
        currentStageIndex: stageIndex,
        stages: prev.stages.map((s, i) => 
          i === stageIndex 
            ? { ...s, status: 'processing', startTime: Date.now() } 
            : s
        ),
      }));

      // Simulate processing time
      await new Promise(r => setTimeout(r, STAGE_DELAYS[stageId]));
      if (abortRef.current) return false;

      // Generate output based on stage
      let output: StageOutput[typeof stageId];
      
      switch (stageId) {
        case 'understand':
          intentOutput = generateMockIntent(query);
          output = intentOutput;
          break;
        case 'retrieve':
          candidatesOutput = generateMockCandidates(intentOutput!);
          output = {
            candidates: candidatesOutput,
            total_retrieved: candidatesOutput.length,
            retrieval_methods: ['BM25', 'Vector', 'Field Filter'],
          };
          break;
        case 'judge':
          evidenceOutput = generateMockEvidence(candidatesOutput!);
          output = {
            verified_evidence: evidenceOutput,
            rejected_count: candidatesOutput!.length - evidenceOutput.length,
            acceptance_rate: evidenceOutput.length / candidatesOutput!.length,
          };
          break;
        case 'analyze':
          gapOutput = generateMockGapAnalysis(iteration);
          output = gapOutput;
          break;
        case 'report':
          output = generateMockReport(evidenceOutput!, query);
          break;
      }

      // Update with completed status
      setState(prev => ({
        ...prev,
        stages: prev.stages.map((s, i) => 
          i === stageIndex 
            ? { ...s, status: 'completed', endTime: Date.now(), output } 
            : s
        ),
      }));

      return true;
    };

    // Run stages sequentially
    for (let i = 0; i < 4; i++) { // Run first 4 stages
      const success = await processStage(i);
      if (!success) return;
    }

    // Check gap analysis result
    if (gapOutput?.status === 'insufficient' && iteration < 3) {
      // Loop back to retrieve
      iteration++;
      setState(prev => ({
        ...prev,
        iteration,
        stages: prev.stages.map((s, i) => 
          i >= 1 && i <= 3 
            ? { ...s, status: 'pending', output: undefined, startTime: undefined, endTime: undefined } 
            : s
        ),
      }));

      // Re-run stages 1-3
      for (let i = 1; i <= 3; i++) {
        const success = await processStage(i);
        if (!success) return;
      }
    }

    // Final report stage
    await processStage(4);

    // Mark completed
    setState(prev => ({
      ...prev,
      isRunning: false,
      isCompleted: true,
      currentStageIndex: 4,
    }));

  }, []);

  return {
    state,
    runPipeline,
    reset,
  };
}
