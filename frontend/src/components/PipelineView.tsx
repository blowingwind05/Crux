import React from 'react';
import { motion } from 'framer-motion';
import type { PipelineState } from '@/types/crux';
import { StageNode } from './StageNode';

interface PipelineViewProps {
  state: PipelineState;
}

export function PipelineView({ state }: PipelineViewProps) {
  const { stages, currentStageIndex, iteration, isRunning } = state;

  if (currentStageIndex < 0 && !isRunning) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full max-w-3xl mx-auto mt-8"
    >
      {/* Iteration indicator */}
      {iteration > 1 && (
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="mb-4 flex items-center gap-2"
        >
          <div className="h-px flex-1 bg-gradient-to-r from-accent/50 to-transparent" />
          <span className="text-xs font-mono text-accent px-2">
            第 {iteration} 次迭代
          </span>
          <div className="h-px flex-1 bg-gradient-to-l from-accent/50 to-transparent" />
        </motion.div>
      )}

      {/* Stage nodes */}
      <div className="space-y-4">
        {stages.map((stage, index) => (
          <StageNode
            key={`${stage.id}-${iteration}`}
            stage={stage}
            index={index}
            isActive={index === currentStageIndex}
            showConnector={index > 0}
            isLoopBack={iteration > 1 && index === 1}
          />
        ))}
      </div>

      {/* Progress bar */}
      {isRunning && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-6"
        >
          <div className="h-1 bg-muted rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-primary to-accent"
              initial={{ width: '0%' }}
              animate={{ 
                width: `${((currentStageIndex + 1) / stages.length) * 100}%` 
              }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
