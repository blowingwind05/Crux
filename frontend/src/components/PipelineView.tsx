import React from 'react';
import { motion } from 'framer-motion';
import type { PipelineState } from '@/types/crux';
import { WorkflowPanel } from './WorkflowPanel';
import { ResultsPanel } from './ResultsPanel';

interface PipelineViewProps {
  state: PipelineState;
}

export function PipelineView({ state }: PipelineViewProps) {
  const { currentStageIndex, isRunning, isCompleted } = state;

  // Don't render if not started
  if (currentStageIndex < 0 && !isRunning && !isCompleted) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full mt-6"
    >
      {/* 左右分栏布局 */}
      <div className="flex h-[calc(100vh-280px)] min-h-[500px] rounded-xl overflow-hidden border border-border bg-card/30 backdrop-blur-sm">
        {/* 左侧 Working Flow Panel - 固定宽度 */}
        <div className="w-[340px] shrink-0">
          <WorkflowPanel state={state} />
        </div>

        {/* 右侧 Results Panel - 3/4 宽度 */}
        <div className="flex-1">
          <ResultsPanel state={state} />
        </div>
      </div>
    </motion.div>
  );
}
