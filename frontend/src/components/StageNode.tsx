import React from 'react';
import { motion } from 'framer-motion';
import { 
  Brain, 
  Search, 
  Scale, 
  GitBranch, 
  FileText,
  Loader2,
  CheckCircle2,
  Circle,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import type { PipelineStage, StageId } from '@/types/crux';
import { cn } from '@/lib/utils';
import { StageOutput } from './StageOutput';

const stageIcons: Record<StageId, React.ElementType> = {
  understand: Brain,
  retrieve: Search,
  judge: Scale,
  analyze: GitBranch,
  report: FileText,
};

const stageColors: Record<StageId, string> = {
  understand: 'stage-understand',
  retrieve: 'stage-retrieve',
  judge: 'stage-judge',
  analyze: 'stage-analyze',
  report: 'stage-report',
};

const stageBgColors: Record<StageId, string> = {
  understand: 'stage-understand-bg',
  retrieve: 'stage-retrieve-bg',
  judge: 'stage-judge-bg',
  analyze: 'stage-analyze-bg',
  report: 'stage-report-bg',
};

interface StageNodeProps {
  stage: PipelineStage;
  index: number;
  isActive: boolean;
  showConnector: boolean;
  isLoopBack?: boolean;
}

export function StageNode({ stage, index, isActive, showConnector, isLoopBack }: StageNodeProps) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const Icon = stageIcons[stage.id];
  const colorClass = stageColors[stage.id];
  const bgClass = stageBgColors[stage.id];

  const isCompleted = stage.status === 'completed';
  const isProcessing = stage.status === 'processing';
  const isPending = stage.status === 'pending';

  // Auto-expand when completed
  React.useEffect(() => {
    if (isCompleted) {
      setIsExpanded(true);
    }
  }, [isCompleted]);

  return (
    <div className="relative">
      {/* Connector line */}
      {showConnector && (
        <div className="absolute left-7 -top-8 w-0.5 h-8">
          <div 
            className={cn(
              "w-full h-full transition-colors duration-500",
              isCompleted || isProcessing 
                ? "bg-gradient-to-b from-primary/50 to-primary" 
                : "bg-border"
            )}
          />
          {(isProcessing || isActive) && (
            <motion.div 
              className="absolute top-0 left-0 w-full h-4 particle-flow"
              animate={{ y: [0, 32] }}
              transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
            />
          )}
        </div>
      )}

      {/* Loop back indicator */}
      {isLoopBack && stage.id === 'retrieve' && (
        <motion.div 
          className="absolute -left-12 top-1/2 -translate-y-1/2"
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <div className="flex items-center gap-2 text-accent text-xs font-mono">
            <GitBranch className="w-4 h-4" />
            <span>回流</span>
          </div>
        </motion.div>
      )}

      {/* Main node */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.1 }}
        className={cn(
          "relative rounded-lg border transition-all duration-300",
          bgClass,
          isActive && "glow-primary",
          isProcessing && "pulse-glow",
        )}
      >
        {/* Header */}
        <button
          onClick={() => isCompleted && setIsExpanded(!isExpanded)}
          className={cn(
            "w-full flex items-center gap-4 p-4 text-left",
            isCompleted && "cursor-pointer hover:bg-white/5"
          )}
        >
          {/* Status icon */}
          <div className={cn(
            "flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center",
            "border transition-all duration-300",
            isCompleted && `border-${colorClass}/50 bg-${colorClass}/20`,
            isProcessing && "border-primary bg-primary/20",
            isPending && "border-border bg-muted/50"
          )}>
            {isProcessing ? (
              <Loader2 className={cn("w-5 h-5 animate-spin", colorClass)} />
            ) : isCompleted ? (
              <CheckCircle2 className={cn("w-5 h-5", colorClass)} />
            ) : (
              <Icon className="w-5 h-5 text-muted-foreground" />
            )}
          </div>

          {/* Text */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className={cn(
                "text-sm font-mono",
                isCompleted || isProcessing ? colorClass : "text-muted-foreground"
              )}>
                {String(index + 1).padStart(2, '0')}
              </span>
              <h3 className={cn(
                "font-semibold",
                isCompleted || isProcessing ? "text-foreground" : "text-muted-foreground"
              )}>
                {stage.nameCn}
              </h3>
              <span className="text-xs text-muted-foreground hidden sm:inline">
                {stage.name}
              </span>
            </div>
            <p className="text-sm text-muted-foreground mt-0.5 line-clamp-1">
              {stage.description}
            </p>
          </div>

          {/* Expand indicator */}
          {isCompleted && (
            <div className="flex-shrink-0">
              {isExpanded ? (
                <ChevronDown className="w-5 h-5 text-muted-foreground" />
              ) : (
                <ChevronRight className="w-5 h-5 text-muted-foreground" />
              )}
            </div>
          )}

          {/* Processing indicator */}
          {isProcessing && (
            <div className="flex-shrink-0 flex items-center gap-2">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <motion.div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-primary"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ 
                      duration: 1, 
                      repeat: Infinity, 
                      delay: i * 0.2 
                    }}
                  />
                ))}
              </div>
              <span className="text-xs text-primary font-mono">处理中...</span>
            </div>
          )}

          {/* Duration */}
          {isCompleted && stage.startTime && stage.endTime && (
            <div className="flex-shrink-0 text-xs text-muted-foreground font-mono">
              {((stage.endTime - stage.startTime) / 1000).toFixed(1)}s
            </div>
          )}
        </button>

        {/* Expanded output */}
        {isCompleted && isExpanded && stage.output && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="border-t border-border/50"
          >
            <div className="p-4">
              <StageOutput stageId={stage.id} output={stage.output} />
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
