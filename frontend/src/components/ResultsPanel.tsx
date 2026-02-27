import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    FileText,
    ExternalLink,
    CheckCircle,
    User,
    Calendar,
    ChevronDown,
    ChevronRight,
    Quote,
    RefreshCw,
    Layers,
    Brain,
    Search,
    Scale,
    Target,
    AlertTriangle,
    Filter,
    Lightbulb,
    FileSearch,
} from 'lucide-react';
import type { PipelineState, CandidateDoc, Evidence, FinalReport, IterationResult, IntentObject, GapAnalysis, RejectedDoc } from '@/types/crux';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ResultsPanelProps {
    state: PipelineState;
}

// 5阶段标签定义
const stageTabs = [
    { id: 'understand', label: '意图理解', icon: Brain, color: 'text-stage-understand' },
    { id: 'retrieve', label: '混合召回', icon: Search, color: 'text-stage-retrieve' },
    { id: 'judge', label: '深度研判', icon: Scale, color: 'text-stage-judge' },
    { id: 'analyze', label: '缺口分析', icon: Target, color: 'text-stage-analyze' },
    { id: 'report', label: '报告生成', icon: FileText, color: 'text-stage-report' },
] as const;

type TabId = typeof stageTabs[number]['id'];

export function ResultsPanel({ state }: ResultsPanelProps) {
    const { stages, isCompleted, iterations } = state;
    const [activeTab, setActiveTab] = React.useState<TabId>('understand');

    // 各阶段数据
    const understandStage = stages.find(s => s.id === 'understand');
    const reportStage = stages.find(s => s.id === 'report');

    const intentOutput = understandStage?.output as IntentObject | undefined;
    const report = reportStage?.output as FinalReport | undefined;

    // 计算各阶段数量（用于标签显示）
    const stageCounts = React.useMemo(() => {
        const totalCandidates = iterations.reduce((sum, iter) => sum + iter.candidates.length, 0);
        const totalEvidence = iterations.reduce((sum, iter) => sum + iter.evidence.length, 0);
        const gapCount = iterations.filter(iter => iter.gapStatus).length;

        return {
            understand: intentOutput ? 1 : 0,
            retrieve: totalCandidates,
            judge: totalEvidence,
            analyze: gapCount,
            report: report ? 1 : 0,
        };
    }, [iterations, intentOutput, report]);

    // 追踪用户是否手动切换过 tab
    const userInteractedRef = React.useRef(false);
    const prevIsCompletedRef = React.useRef(isCompleted);

    // 用户手动切换 tab 的处理函数
    const handleTabChange = React.useCallback((tabId: TabId) => {
        userInteractedRef.current = true;
        setActiveTab(tabId);
    }, []);

    // 自动切换到当前阶段 - 跟随管线执行自动切换
    React.useEffect(() => {
        // 如果用户已手动交互，且管线已完成，则不再自动切换
        if (userInteractedRef.current && isCompleted) {
            return;
        }

        // 管线刚完成时，自动切换到报告（仅首次）
        if (report && isCompleted && !prevIsCompletedRef.current) {
            setActiveTab('report');
            prevIsCompletedRef.current = true;
            return;
        }

        // 管线执行中：跟随 currentStage 自动切换（包括回环到 retrieve）
        if (!isCompleted && state.currentStage) {
            const stageToTab: Record<string, TabId> = {
                'understand': 'understand',
                'retrieve': 'retrieve',
                'judge': 'judge',
                'analyze': 'analyze',
                'report': 'report',
            };
            const targetTab = stageToTab[state.currentStage];
            if (targetTab && targetTab !== activeTab) {
                // 自动切换时不设置 userInteracted
                setActiveTab(targetTab);
            }
        }

        prevIsCompletedRef.current = isCompleted;
    }, [state.currentStage, report, isCompleted, activeTab]);

    // 重置状态（新查询时）
    React.useEffect(() => {
        if (!isCompleted && iterations.length === 0) {
            userInteractedRef.current = false;
            prevIsCompletedRef.current = false;
            setActiveTab('understand');
        }
    }, [isCompleted, iterations.length]);

    return (
        <div className="h-full flex flex-col bg-background">
            {/* 5-Stage Tab Header */}
            <div className="flex items-center gap-1 p-2 border-b border-border bg-muted/30 overflow-x-auto">
                {stageTabs.map((tab, index) => {
                    const Icon = tab.icon;
                    const count = stageCounts[tab.id];
                    const isActive = activeTab === tab.id;
                    const stage = stages.find(s => s.id === tab.id);
                    const isCompleted = stage?.status === 'completed';
                    const isProcessing = stage?.status === 'processing';

                    return (
                        <button
                            key={tab.id}
                            onClick={() => handleTabChange(tab.id)}
                            className={cn(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors whitespace-nowrap",
                                isActive
                                    ? "bg-primary text-primary-foreground"
                                    : "text-muted-foreground hover:text-foreground hover:bg-muted",
                                isProcessing && !isActive && "animate-pulse"
                            )}
                        >
                            <Icon className={cn("w-3.5 h-3.5", isActive ? "" : tab.color)} />
                            <span>{tab.label}</span>
                            {count > 0 && (
                                <span className={cn(
                                    "ml-1 px-1.5 py-0.5 rounded text-xs",
                                    isActive
                                        ? "bg-primary-foreground/20 text-primary-foreground"
                                        : "bg-muted text-muted-foreground"
                                )}>
                                    {count}
                                </span>
                            )}
                            {isCompleted && !isActive && (
                                <CheckCircle className="w-3 h-3 text-green-400" />
                            )}
                        </button>
                    );
                })}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {activeTab === 'understand' && (
                    <IntentView intent={intentOutput} />
                )}
                {activeTab === 'retrieve' && (
                    <RetrieveView iterations={iterations} />
                )}
                {activeTab === 'judge' && (
                    <JudgeView iterations={iterations} />
                )}
                {activeTab === 'analyze' && (
                    <AnalyzeView iterations={iterations} stages={stages} />
                )}
                {activeTab === 'report' && (
                    <ReportView report={report} iterations={iterations} />
                )}
            </div>
        </div>
    );
}

// ============ 1. 意图理解视图 ============
function IntentView({ intent }: { intent?: IntentObject }) {
    if (!intent) {
        return (
            <EmptyState
                icon={Brain}
                title="暂无意图解析结果"
                subtitle="执行查询后将在此显示意图理解结果"
            />
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
        >
            {/* User Goal */}
            <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-stage-understand" />
                <span className="text-sm text-muted-foreground">用户目标:</span>
                <Badge variant="outline" className="text-stage-understand border-stage-understand/30">
                    {intent.user_goal}
                </Badge>
                {intent.cognitive_strategy && (
                    <>
                        <span className="text-muted-foreground">→</span>
                        <Badge variant="outline" className="text-xs">
                            {intent.cognitive_strategy.reasoning_topology}
                        </Badge>
                    </>
                )}
            </div>

            {/* Keywords */}
            {intent.keywords_bm25 && intent.keywords_bm25.length > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Filter className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">BM25 关键词:</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {intent.keywords_bm25.map((kw, i) => (
                            <Badge key={i} variant="secondary" className="font-mono text-xs">
                                {kw}
                            </Badge>
                        ))}
                    </div>
                </div>
            )}

            {/* Vector Queries */}
            {intent.queries_vector && intent.queries_vector.length > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <FileSearch className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">向量检索语句:</span>
                    </div>
                    <div className="bg-muted/30 rounded-lg p-3 space-y-1">
                        {intent.queries_vector.map((q, i) => (
                            <div key={i} className="text-xs">
                                <span className="text-primary">[{i + 1}]</span> {q}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Facets */}
            {intent.information_facets && intent.information_facets.length > 0 && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Lightbulb className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">信息面 (Facets):</span>
                    </div>
                    <div className="space-y-2">
                        {intent.information_facets.map((facet) => (
                            <div
                                key={facet.facet_id}
                                className="flex items-start gap-2 text-sm p-2 rounded bg-muted/30"
                            >
                                <Badge variant="outline" className="font-mono text-xs shrink-0">
                                    {facet.facet_id}
                                </Badge>
                                <span className="text-muted-foreground">{facet.facet_type}:</span>
                                <span>{facet.description}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Rubric */}
            {intent.rubric && (
                <div>
                    <div className="flex items-center gap-2 mb-2">
                        <Scale className="w-4 h-4 text-muted-foreground" />
                        <span className="text-sm text-muted-foreground">研判准则:</span>
                    </div>
                    <div className="bg-muted/30 rounded-lg p-3 text-sm text-muted-foreground">
                        {intent.rubric}
                    </div>
                </div>
            )}
        </motion.div>
    );
}

// ============ 2. 混合召回视图 ============
function RetrieveView({ iterations }: { iterations: IterationResult[] }) {
    const [expandedIter, setExpandedIter] = React.useState<number | 'all'>('all');

    if (iterations.length === 0 || iterations.every(iter => iter.candidates.length === 0)) {
        return (
            <EmptyState
                icon={Search}
                title="暂无召回文档"
                subtitle="执行检索后将在此显示候选文档"
            />
        );
    }

    return (
        <div className="space-y-4">
            {/* 迭代选择器 */}
            {iterations.length > 1 && (
                <IterationSelector
                    iterations={iterations}
                    selected={expandedIter}
                    onChange={setExpandedIter}
                    countKey="candidates"
                />
            )}

            {/* 候选文档列表 */}
            <div className="space-y-3">
                {iterations.map((iter, iterIndex) => {
                    if (expandedIter !== 'all' && expandedIter !== iterIndex) return null;
                    if (iter.candidates.length === 0) return null;

                    return (
                        <IterationGroup
                            key={iterIndex}
                            iterationIndex={iterIndex}
                            totalIterations={iterations.length}
                            title={`第 ${iterIndex + 1} 轮召回`}
                            count={iter.candidates.length}
                        >
                            {iter.candidates.map((doc, index) => (
                                <CandidateCard key={doc.doc_id || index} doc={doc} index={index} />
                            ))}
                        </IterationGroup>
                    );
                })}
            </div>
        </div>
    );
}

// ============ 3. 深度研判视图 ============
function JudgeView({ iterations }: { iterations: IterationResult[] }) {
    const [expandedIter, setExpandedIter] = React.useState<number | 'all'>('all');

    const hasAnyData = iterations.some(iter =>
        iter.evidence.length > 0 || (iter.rejectedDocs && iter.rejectedDocs.length > 0)
    );

    if (iterations.length === 0 || !hasAnyData) {
        return (
            <EmptyState
                icon={Scale}
                title="暂无研判结果"
                subtitle="深度研判后将在此显示采纳和拒绝的文档"
            />
        );
    }

    return (
        <div className="space-y-4">
            {/* 迭代选择器 */}
            {iterations.length > 1 && (
                <IterationSelector
                    iterations={iterations}
                    selected={expandedIter}
                    onChange={setExpandedIter}
                    countKey="evidence"
                />
            )}

            {/* 研判结果列表 */}
            <div className="space-y-4">
                {iterations.map((iter, iterIndex) => {
                    if (expandedIter !== 'all' && expandedIter !== iterIndex) return null;

                    const hasEvidence = iter.evidence.length > 0;
                    const hasRejected = iter.rejectedDocs && iter.rejectedDocs.length > 0;
                    if (!hasEvidence && !hasRejected) return null;

                    const acceptedCount = iter.evidence.length;
                    const rejectedCount = iter.rejectedDocs?.length || 0;

                    return (
                        <IterationGroup
                            key={iterIndex}
                            iterationIndex={iterIndex}
                            totalIterations={iterations.length}
                            title={`第 ${iterIndex + 1} 轮研判`}
                            count={acceptedCount + rejectedCount}
                            subtitle={`采纳 ${acceptedCount} / 拒绝 ${rejectedCount}`}
                        >
                            {/* 采纳的证据 */}
                            {hasEvidence && (
                                <div className="space-y-2">
                                    <div className="flex items-center gap-2 text-sm font-medium text-green-400">
                                        <CheckCircle className="w-4 h-4" />
                                        <span>采纳证据 ({acceptedCount})</span>
                                    </div>
                                    {iter.evidence.map((ev, index) => (
                                        <EvidenceCard key={ev.doc_id || index} evidence={ev} index={index} />
                                    ))}
                                </div>
                            )}

                            {/* 拒绝的文档 */}
                            {hasRejected && (
                                <div className="space-y-2 mt-4">
                                    <div className="flex items-center gap-2 text-sm font-medium text-red-400">
                                        <AlertTriangle className="w-4 h-4" />
                                        <span>拒绝文档 ({rejectedCount})</span>
                                    </div>
                                    {iter.rejectedDocs!.map((doc, index) => (
                                        <RejectedDocCard key={doc.doc_id || index} doc={doc} index={index} />
                                    ))}
                                </div>
                            )}
                        </IterationGroup>
                    );
                })}
            </div>
        </div>
    );
}

// 被拒绝文档卡片
function RejectedDocCard({ doc, index }: { doc: RejectedDoc; index: number }) {
    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-red-500/5 border border-red-500/20 rounded-lg p-3"
        >
            <div className="flex items-start justify-between gap-3">
                <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm text-red-300 truncate">{doc.title || doc.doc_id}</h4>
                    {doc.abstract && (
                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{doc.abstract}</p>
                    )}
                </div>
            </div>
            <div className="mt-2 text-xs text-red-400/80 bg-red-500/10 rounded px-2 py-1">
                <span className="font-medium">拒绝原因:</span> {doc.reason}
            </div>
        </motion.div>
    );
}

// ============ 4. 缺口分析视图 ============
function AnalyzeView({ iterations, stages }: { iterations: IterationResult[]; stages: PipelineState['stages'] }) {
    const analyzeStage = stages.find(s => s.id === 'analyze');
    const gapOutput = analyzeStage?.output as GapAnalysis | undefined;

    const iterationsWithGap = iterations.filter(iter => iter.gapStatus);

    if (iterationsWithGap.length === 0 && !gapOutput) {
        return (
            <EmptyState
                icon={Target}
                title="暂无缺口分析"
                subtitle="信息缺口分析后将在此显示结果"
            />
        );
    }

    return (
        <div className="space-y-4">
            {/* 各轮次缺口状态 */}
            {iterations.map((iter, iterIndex) => {
                if (!iter.gapStatus) return null;
                const isSufficient = iter.gapStatus === 'sufficient';

                return (
                    <motion.div
                        key={iterIndex}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: iterIndex * 0.1 }}
                        className={cn(
                            "p-4 rounded-lg border",
                            isSufficient
                                ? "border-green-500/30 bg-green-500/5"
                                : "border-yellow-500/30 bg-yellow-500/5"
                        )}
                    >
                        <div className="flex items-center gap-3 mb-3">
                            <span className="font-mono text-xs bg-muted px-2 py-0.5 rounded">
                                第 {iterIndex + 1} 轮
                            </span>
                            {isSufficient ? (
                                <>
                                    <CheckCircle className="w-4 h-4 text-green-400" />
                                    <span className="text-green-400 font-medium">信息充足</span>
                                </>
                            ) : (
                                <>
                                    <AlertTriangle className="w-4 h-4 text-yellow-400" />
                                    <span className="text-yellow-400 font-medium">检测到缺口 → 继续检索</span>
                                </>
                            )}
                            <span className="ml-auto text-xs text-muted-foreground">
                                证据: {iter.evidence.length} 条
                            </span>
                        </div>

                        {/* 显示每轮的覆盖度 */}
                        {iter.coverageScore !== undefined && (
                            <div className="flex items-center gap-2 text-sm mb-2">
                                <span className="text-muted-foreground">覆盖度:</span>
                                <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden max-w-[200px]">
                                    <div
                                        className={cn(
                                            "h-full transition-all",
                                            isSufficient ? "bg-green-500" : "bg-yellow-500"
                                        )}
                                        style={{ width: `${(iter.coverageScore * 100).toFixed(0)}%` }}
                                    />
                                </div>
                                <span className="font-mono text-xs">{(iter.coverageScore * 100).toFixed(0)}%</span>
                            </div>
                        )}

                        {/* 显示缺口原因 */}
                        {iter.gapReason && !isSufficient && (
                            <div className="mt-2 text-xs text-yellow-300/80 bg-yellow-500/10 rounded p-2">
                                <span className="font-medium">缺失信息:</span> {iter.gapReason}
                            </div>
                        )}
                    </motion.div>
                );
            })}

            {/* 最终缺口分析详情 */}
            {gapOutput && (
                <div className="mt-4 p-4 rounded-lg bg-muted/30 border border-border">
                    <h4 className="text-sm font-medium mb-3">最终分析</h4>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span className="text-muted-foreground">覆盖度:</span>
                            <span className="ml-2 font-mono">{((gapOutput.coverage_score || 0) * 100).toFixed(0)}%</span>
                        </div>
                        <div>
                            <span className="text-muted-foreground">迭代次数:</span>
                            <span className="ml-2 font-mono">{iterations.length}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// ============ 5. 报告生成视图 ============
function ReportView({ report, iterations }: { report?: FinalReport; iterations: IterationResult[] }) {
    if (!report) {
        return (
            <EmptyState
                icon={FileText}
                title="暂无分析报告"
                subtitle="管线完成后将在此显示最终报告"
            />
        );
    }

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
        >
            {/* Summary */}
            <div className="p-4 rounded-lg bg-gradient-to-br from-primary/10 to-transparent border border-primary/20">
                <div className="flex items-center gap-2 mb-3">
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                    <span className="font-medium text-primary">分析结论</span>
                    <span className="ml-auto text-xs font-mono text-muted-foreground">
                        置信度: {((report.confidence_score ?? 0.9) * 100).toFixed(0)}%
                    </span>
                </div>
                <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">
                    {report.summary || '分析完成'}
                </p>
            </div>

            {/* Iteration Summary */}
            {iterations.length > 1 && (
                <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-3 flex items-center gap-2">
                        <RefreshCw className="w-4 h-4" />
                        迭代过程 ({iterations.length} 轮)
                    </h3>
                    <div className="space-y-2">
                        {iterations.map((iter, i) => (
                            <div key={i} className="flex items-center gap-3 text-sm p-2 rounded bg-muted/30">
                                <span className="font-mono text-primary">#{i + 1}</span>
                                <span>召回 {iter.candidates.length} 篇</span>
                                <span className="text-green-400">采纳 {iter.evidence.length} 条证据</span>
                                {iter.gapStatus && (
                                    <Badge
                                        variant="outline"
                                        className={cn(
                                            "ml-auto text-xs",
                                            iter.gapStatus === 'sufficient'
                                                ? "text-green-400 border-green-500/30"
                                                : "text-yellow-400 border-yellow-500/30"
                                        )}
                                    >
                                        {iter.gapStatus === 'sufficient' ? '充足' : '不足 → 回流'}
                                    </Badge>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Key Findings */}
            {report.key_findings && report.key_findings.length > 0 && (
                <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-3">核心发现</h3>
                    <div className="space-y-2">
                        {report.key_findings.map((finding: string, index: number) => (
                            <motion.div
                                key={index}
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ delay: index * 0.1 }}
                                className="flex items-start gap-2 text-sm"
                            >
                                <span className="font-mono text-primary shrink-0">[{index + 1}]</span>
                                <span className="text-foreground">{finding}</span>
                            </motion.div>
                        ))}
                    </div>
                </div>
            )}

            {/* Citations */}
            {report.citations && report.citations.length > 0 && (
                <div>
                    <h3 className="text-sm font-medium text-muted-foreground mb-3">引用来源</h3>
                    <div className="flex flex-wrap gap-2">
                        {report.citations.map((cite: string, index: number) => (
                            <Badge key={index} variant="outline" className="text-xs font-normal">
                                {cite}
                            </Badge>
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    );
}

// ============ 通用组件 ============

function EmptyState({ icon: Icon, title, subtitle }: { icon: React.ElementType; title: string; subtitle: string }) {
    return (
        <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <Icon className="w-12 h-12 mb-3 opacity-50" />
            <p>{title}</p>
            <p className="text-sm">{subtitle}</p>
        </div>
    );
}

function IterationSelector({
    iterations,
    selected,
    onChange,
    countKey
}: {
    iterations: IterationResult[];
    selected: number | 'all';
    onChange: (v: number | 'all') => void;
    countKey: 'candidates' | 'evidence';
}) {
    return (
        <div className="flex items-center gap-2 p-2 bg-muted/30 rounded-lg">
            <Layers className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">轮次:</span>
            <div className="flex gap-1">
                <button
                    onClick={() => onChange('all')}
                    className={cn(
                        "px-2 py-0.5 rounded text-xs transition-colors",
                        selected === 'all' ? "bg-primary text-primary-foreground" : "bg-muted hover:bg-muted/80"
                    )}
                >
                    全部
                </button>
                {iterations.map((iter, i) => (
                    <button
                        key={i}
                        onClick={() => onChange(i)}
                        className={cn(
                            "px-2 py-0.5 rounded text-xs transition-colors",
                            selected === i ? "bg-primary text-primary-foreground" : "bg-muted hover:bg-muted/80"
                        )}
                    >
                        #{i + 1} ({iter[countKey].length})
                    </button>
                ))}
            </div>
        </div>
    );
}

function IterationGroup({
    iterationIndex,
    totalIterations,
    title,
    count,
    subtitle,
    children
}: {
    iterationIndex: number;
    totalIterations: number;
    title: string;
    count: number;
    subtitle?: string;
    children: React.ReactNode;
}) {
    const [isExpanded, setIsExpanded] = React.useState(true);

    return (
        <div className="border border-border rounded-lg overflow-hidden">
            {totalIterations > 1 && (
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="w-full flex items-center gap-2 p-3 bg-muted/30 hover:bg-muted/50 transition-colors"
                >
                    {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                    ) : (
                        <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    )}
                    <span className="font-medium text-sm">{title}</span>
                    {subtitle && (
                        <span className="text-xs text-muted-foreground">({subtitle})</span>
                    )}
                    <Badge variant="outline" className="ml-auto text-xs">
                        {count} 条
                    </Badge>
                </button>
            )}
            <AnimatePresence>
                {(isExpanded || totalIterations === 1) && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="p-3 space-y-3"
                    >
                        {children}
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function CandidateCard({ doc, index }: { doc: CandidateDoc; index: number }) {
    const [isExpanded, setIsExpanded] = React.useState(index < 3);

    const sourceColors: Record<string, string> = {
        bm25: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
        vector: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
        hybrid: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.03 }}
            layout
            className="border border-border rounded-lg overflow-hidden bg-card hover:border-primary/30 transition-colors"
        >
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full flex items-start gap-3 p-3 text-left hover:bg-muted/30"
            >
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-foreground line-clamp-1">
                            {doc.title || '无标题'}
                        </h3>
                        {doc.url && (
                            <a
                                href={doc.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={e => e.stopPropagation()}
                                className="text-muted-foreground hover:text-primary"
                            >
                                <ExternalLink className="w-3.5 h-3.5" />
                            </a>
                        )}
                    </div>

                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Badge
                            variant="outline"
                            className={cn("text-xs", sourceColors[doc.source] || sourceColors.hybrid)}
                        >
                            {doc.source}
                        </Badge>
                        {doc.year && (
                            <span className="flex items-center gap-1">
                                <Calendar className="w-3 h-3" />
                                {doc.year}
                            </span>
                        )}
                        {doc.authors && doc.authors.length > 0 && (
                            <span className="flex items-center gap-1">
                                <User className="w-3 h-3" />
                                {doc.authors[0]}{doc.authors.length > 1 && ` +${doc.authors.length - 1}`}
                            </span>
                        )}
                    </div>
                </div>

                <div className="text-right shrink-0">
                    <div className="font-mono text-lg text-primary">
                        {((doc.score ?? 0) * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-muted-foreground">相似度</div>
                </div>

                {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground mt-1" />
                ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground mt-1" />
                )}
            </button>

            <AnimatePresence>
                {isExpanded && doc.abstract && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="px-3 pb-3 border-t border-border/50"
                    >
                        <p className="text-sm text-muted-foreground pt-3 leading-relaxed">
                            {doc.abstract}
                        </p>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

function EvidenceCard({ evidence, index }: { evidence: Evidence; index: number }) {
    const metadata = (evidence.metadata || {}) as Record<string, unknown>;

    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.08 }}
            layout
            className="border border-green-500/30 rounded-lg p-4 bg-green-500/5"
        >
            <div className="flex items-start gap-3">
                <Quote className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />

                <div className="flex-1 min-w-0">
                    <p className="text-sm leading-relaxed italic text-foreground mb-3">
                        "{evidence.content}"
                    </p>

                    <div className="flex flex-wrap items-center gap-2 text-xs">
                        {evidence.facet_id && (
                            <Badge variant="outline" className="text-green-400 border-green-500/30">
                                {evidence.facet_id}
                            </Badge>
                        )}

                        {metadata.title && (
                            <span className="text-muted-foreground truncate max-w-xs">
                                来源: {String(metadata.title)}
                            </span>
                        )}

                        <span className="ml-auto font-mono text-green-400">
                            {((evidence.relevance_score ?? 0.8) * 100).toFixed(0)}% 有用性
                        </span>
                    </div>

                    {evidence.reason && (
                        <div className="mt-2 text-xs text-muted-foreground">
                            <span className="text-green-400">判定理由:</span> {evidence.reason}
                        </div>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
