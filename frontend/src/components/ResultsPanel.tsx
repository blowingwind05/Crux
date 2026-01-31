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
} from 'lucide-react';
import type { PipelineState, CandidateDoc, Evidence, FinalReport, IterationResult } from '@/types/crux';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ResultsPanelProps {
    state: PipelineState;
}

export function ResultsPanel({ state }: ResultsPanelProps) {
    const { stages, isCompleted, iterations } = state;
    const [activeTab, setActiveTab] = React.useState<'candidates' | 'evidence' | 'report'>('candidates');
    const [selectedIteration, setSelectedIteration] = React.useState<number | 'all'>('all');

    // Get report from final stage
    const reportStage = stages.find(s => s.id === 'report');
    const report = reportStage?.output as FinalReport | undefined;

    // Aggregate candidates and evidence across iterations
    const allCandidates = React.useMemo(() => {
        if (selectedIteration === 'all') {
            // De-duplicate by doc_id, keep latest
            const map = new Map<string, CandidateDoc>();
            iterations.forEach(iter => {
                iter.candidates.forEach(c => map.set(c.doc_id, c));
            });
            return Array.from(map.values());
        }
        return iterations[selectedIteration]?.candidates ?? [];
    }, [iterations, selectedIteration]);

    const allEvidence = React.useMemo(() => {
        if (selectedIteration === 'all') {
            // Aggregate all evidence
            const map = new Map<string, Evidence>();
            iterations.forEach(iter => {
                iter.evidence.forEach(e => map.set(e.doc_id, e));
            });
            return Array.from(map.values());
        }
        return iterations[selectedIteration]?.evidence ?? [];
    }, [iterations, selectedIteration]);

    // Auto-switch to evidence tab when evidence exists
    React.useEffect(() => {
        if (allEvidence.length > 0 && activeTab === 'candidates') {
            setActiveTab('evidence');
        }
        if (report && isCompleted) {
            setActiveTab('report');
        }
    }, [allEvidence.length, report, isCompleted, activeTab]);

    const tabs = [
        { id: 'candidates', label: '召回文档', count: allCandidates.length },
        { id: 'evidence', label: '已验证证据', count: allEvidence.length },
        { id: 'report', label: '分析报告', count: report ? 1 : 0 },
    ];

    return (
        <div className="h-full flex flex-col bg-background">
            {/* Tab Header */}
            <div className="flex items-center gap-1 p-2 border-b border-border bg-muted/30">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as typeof activeTab)}
                        className={cn(
                            "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                            activeTab === tab.id
                                ? "bg-primary text-primary-foreground"
                                : "text-muted-foreground hover:text-foreground hover:bg-muted"
                        )}
                    >
                        {tab.label}
                        {tab.count > 0 && (
                            <span className={cn(
                                "ml-1.5 px-1.5 py-0.5 rounded text-xs",
                                activeTab === tab.id
                                    ? "bg-primary-foreground/20 text-primary-foreground"
                                    : "bg-muted text-muted-foreground"
                            )}>
                                {tab.count}
                            </span>
                        )}
                    </button>
                ))}

                {/* Iteration Selector */}
                {iterations.length > 1 && activeTab !== 'report' && (
                    <div className="ml-auto flex items-center gap-1">
                        <Layers className="w-4 h-4 text-muted-foreground" />
                        <select
                            value={selectedIteration}
                            onChange={(e) => setSelectedIteration(e.target.value === 'all' ? 'all' : Number(e.target.value))}
                            className="bg-muted border-none text-xs rounded px-2 py-1"
                        >
                            <option value="all">全部轮次</option>
                            {iterations.map((_, i) => (
                                <option key={i} value={i}>第 {i + 1} 轮</option>
                            ))}
                        </select>
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {activeTab === 'candidates' && (
                    <CandidatesList candidates={allCandidates} />
                )}
                {activeTab === 'evidence' && (
                    <EvidenceList evidence={allEvidence} />
                )}
                {activeTab === 'report' && (
                    <ReportView report={report} iterations={iterations} />
                )}
            </div>
        </div>
    );
}

// Candidates List Component
function CandidatesList({ candidates }: { candidates: CandidateDoc[] }) {
    if (candidates.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                <FileText className="w-12 h-12 mb-3 opacity-50" />
                <p>暂无召回文档</p>
                <p className="text-sm">执行查询后将在此显示候选文档</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            <AnimatePresence mode="popLayout">
                {candidates.map((doc, index) => (
                    <CandidateCard key={doc.doc_id || index} doc={doc} index={index} />
                ))}
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
            exit={{ opacity: 0, y: -10 }}
            transition={{ delay: index * 0.03 }}
            layout
            className="border border-border rounded-lg overflow-hidden bg-card hover:border-primary/30 transition-colors"
        >
            {/* Header */}
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
                    <div className="text-xs text-muted-foreground">相关度</div>
                </div>

                {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-muted-foreground mt-1" />
                ) : (
                    <ChevronRight className="w-4 h-4 text-muted-foreground mt-1" />
                )}
            </button>

            {/* Expanded Content */}
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

// Evidence List Component
function EvidenceList({ evidence }: { evidence: Evidence[] }) {
    if (evidence.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                <CheckCircle className="w-12 h-12 mb-3 opacity-50" />
                <p>暂无验证证据</p>
                <p className="text-sm">深度研判后将在此显示通过验证的证据</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <AnimatePresence mode="popLayout">
                {evidence.map((ev, index) => (
                    <EvidenceCard key={ev.doc_id || index} evidence={ev} index={index} />
                ))}
            </AnimatePresence>
        </div>
    );
}

function EvidenceCard({ evidence, index }: { evidence: Evidence; index: number }) {
    const metadata = (evidence.metadata || {}) as Record<string, unknown>;

    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 10 }}
            transition={{ delay: index * 0.08 }}
            layout
            className="border border-green-500/30 rounded-lg p-4 bg-green-500/5"
        >
            <div className="flex items-start gap-3">
                <Quote className="w-5 h-5 text-green-400 shrink-0 mt-0.5" />

                <div className="flex-1 min-w-0">
                    {/* Evidence Content */}
                    <p className="text-sm leading-relaxed italic text-foreground mb-3">
                        "{evidence.content}"
                    </p>

                    {/* Metadata */}
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
                            {((evidence.relevance_score ?? 0.8) * 100).toFixed(0)}% 相关
                        </span>
                    </div>

                    {/* Reason */}
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

// Report View Component
function ReportView({ report, iterations }: { report?: FinalReport; iterations: IterationResult[] }) {
    if (!report) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                <FileText className="w-12 h-12 mb-3 opacity-50" />
                <p>暂无分析报告</p>
                <p className="text-sm">管线完成后将在此显示最终报告</p>
            </div>
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
