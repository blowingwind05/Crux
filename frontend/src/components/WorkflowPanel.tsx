import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Activity,
    Clock,
    Zap,
    ChevronDown,
    ChevronRight,
    MessageSquare,
    AlertTriangle,
    CheckCircle2,
    Info,
    Bug,
    RefreshCw,
} from 'lucide-react';
import type { PipelineState, StageLog } from '@/types/crux';
import { cn } from '@/lib/utils';

interface WorkflowPanelProps {
    state: PipelineState;
}

const logIcons = {
    INFO: Info,
    WARN: AlertTriangle,
    ERROR: Bug,
    DEBUG: MessageSquare,
};

const logColors = {
    INFO: 'text-blue-400',
    WARN: 'text-yellow-400',
    ERROR: 'text-red-400',
    DEBUG: 'text-gray-400',
};

export function WorkflowPanel({ state }: WorkflowPanelProps) {
    const { stages, isRunning, isCompleted, stats, allLogs, iteration, iterations } = state;
    const logsEndRef = React.useRef<HTMLDivElement>(null);
    const [autoScroll, setAutoScroll] = React.useState(true);

    // 自动滚动到最新日志
    React.useEffect(() => {
        if (autoScroll && logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [allLogs.length, autoScroll]);

    const completedCount = stages.filter(s => s.status === 'completed').length;
    const totalStages = stages.length;

    // 计算累积统计 - 从所有迭代中累加
    const cumulativeStats = React.useMemo(() => {
        let totalCandidates = 0;
        let totalVerified = 0;

        iterations.forEach(iter => {
            totalCandidates += iter.candidates.length;
            totalVerified += iter.evidence.length;
        });

        return {
            totalCandidates,
            totalVerified,
            iterationCount: iterations.length || 1,
        };
    }, [iterations]);

    return (
        <div className="h-full flex flex-col bg-card/50 backdrop-blur-sm border-r border-border">
            {/* Header */}
            <div className="p-4 border-b border-border">
                <div className="flex items-center gap-2 mb-3">
                    <Activity className="w-5 h-5 text-primary" />
                    <h2 className="font-semibold text-foreground">Working Flow</h2>
                    {iteration > 0 && (
                        <span className="ml-auto flex items-center gap-1 text-xs bg-primary/20 text-primary px-2 py-0.5 rounded">
                            <RefreshCw className="w-3 h-3" />
                            第 {iteration + 1} 轮
                        </span>
                    )}
                </div>

                {/* Stats Grid - 使用累积统计 */}
                <div className="grid grid-cols-3 gap-2">
                    <StatCard
                        label="已验证"
                        value={cumulativeStats.totalVerified}
                        color="text-green-400"
                    />
                    <StatCard
                        label="候选"
                        value={cumulativeStats.totalCandidates}
                        color="text-blue-400"
                    />
                    <StatCard
                        label="迭代"
                        value={cumulativeStats.iterationCount}
                        color="text-purple-400"
                    />
                </div>
            </div>

            {/* Progress */}
            <div className="px-4 py-3 border-b border-border/50">
                <div className="flex items-center justify-between text-sm mb-2">
                    <span className="text-muted-foreground">任务进度</span>
                    <span className="font-mono text-primary">
                        {completedCount}/{totalStages}
                    </span>
                </div>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <motion.div
                        className="h-full bg-gradient-to-r from-primary to-accent"
                        initial={{ width: 0 }}
                        animate={{ width: `${(completedCount / totalStages) * 100}%` }}
                        transition={{ duration: 0.5 }}
                    />
                </div>
            </div>

            {/* Stage Status Pills */}
            <div className="px-4 py-3 border-b border-border/50">
                <div className="flex flex-wrap gap-1.5">
                    {stages.map((stage, index) => {
                        const isActive = stage.status === 'processing';
                        const isComplete = stage.status === 'completed';

                        return (
                            <div
                                key={stage.id}
                                className={cn(
                                    "px-2 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1",
                                    isActive && "bg-primary/20 text-primary animate-pulse",
                                    isComplete && "bg-green-500/20 text-green-400",
                                    !isActive && !isComplete && "bg-muted text-muted-foreground"
                                )}
                            >
                                <span className="font-mono w-4">{index + 1}</span>
                                <span>{stage.nameCn}</span>
                                {isActive && (
                                    <span className="ml-1 flex gap-0.5">
                                        {[0, 1, 2].map(i => (
                                            <motion.span
                                                key={i}
                                                className="w-1 h-1 rounded-full bg-primary"
                                                animate={{ opacity: [0.3, 1, 0.3] }}
                                                transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                                            />
                                        ))}
                                    </span>
                                )}
                                {isComplete && <CheckCircle2 className="w-3 h-3" />}
                            </div>
                        );
                    })}
                </div>
            </div>

            {/* Real-time Logs Stream */}
            <div className="flex-1 overflow-hidden flex flex-col">
                <div className="flex items-center justify-between px-4 py-2 text-sm text-muted-foreground border-b border-border/30">
                    <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4" />
                        <span>执行日志</span>
                        <span className="px-1.5 py-0.5 rounded bg-muted text-xs font-mono">
                            {allLogs.length}
                        </span>
                    </div>
                    <button
                        onClick={() => setAutoScroll(!autoScroll)}
                        className={cn(
                            "text-xs px-2 py-0.5 rounded",
                            autoScroll ? "bg-primary/20 text-primary" : "bg-muted"
                        )}
                    >
                        {autoScroll ? '自动滚动' : '已暂停'}
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-3 space-y-1 font-mono text-xs">
                    <AnimatePresence mode="popLayout">
                        {allLogs.map((log, index) => (
                            <LogLine key={index} log={log} />
                        ))}
                    </AnimatePresence>
                    <div ref={logsEndRef} />
                </div>
            </div>

            {/* Footer Status */}
            {(isRunning || isCompleted) && (
                <div className={cn(
                    "p-3 border-t border-border text-center text-sm",
                    isCompleted ? "text-green-400" : "text-primary"
                )}>
                    {isCompleted ? (
                        <div className="flex items-center justify-center gap-2">
                            <CheckCircle2 className="w-4 h-4" />
                            <span>分析完成 ({(iteration ?? 0) + 1} 轮迭代)</span>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center gap-2">
                            <Zap className="w-4 h-4 animate-pulse" />
                            <span>处理中...</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

const LogLine = React.forwardRef<HTMLDivElement, { log: StageLog }>(
    function LogLine({ log }, ref) {
        const Icon = logIcons[log.level] || Info;
        const colorClass = logColors[log.level] || 'text-gray-400';

        return (
            <motion.div
                ref={ref}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-start gap-2 py-0.5"
            >
                <Icon className={cn("w-3 h-3 mt-0.5 shrink-0", colorClass)} />
                <span className="text-muted-foreground break-all leading-relaxed">
                    {log.message}
                </span>
            </motion.div>
        );
    }
);

interface StatCardProps {
    label: string;
    value: number;
    color: string;
}

function StatCard({ label, value, color }: StatCardProps) {
    return (
        <div className="bg-muted/30 rounded-lg p-2 text-center">
            <div className={cn("text-lg font-mono font-bold", color)}>
                {value}
            </div>
            <div className="text-xs text-muted-foreground">{label}</div>
        </div>
    );
}
