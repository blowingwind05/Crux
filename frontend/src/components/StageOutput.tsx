import React from 'react';
import { motion } from 'framer-motion';
import type { StageId, StageOutput as StageOutputType, IntentObject, CandidateDoc, Evidence, GapAnalysis, FinalReport } from '@/types/crux';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Target,
  Filter,
  FileSearch,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  Quote,
  ArrowRight,
} from 'lucide-react';

interface StageOutputProps {
  stageId: StageId;
  output: any;
}

export function StageOutput({ stageId, output }: StageOutputProps) {
  switch (stageId) {
    case 'understand':
      return <IntentOutput data={output as IntentObject} />;
    case 'retrieve':
      return <RetrieveOutput data={output} />;
    case 'judge':
      return <JudgeOutput data={output} />;
    case 'analyze':
      return <AnalyzeOutput data={output as GapAnalysis} />;
    case 'report':
      return <ReportOutput data={output as FinalReport} />;
    default:
      return null;
  }
}

function IntentOutput({ data }: { data: IntentObject }) {
  return (
    <div className="space-y-4">
      {/* User Goal */}
      <div className="flex items-center gap-2">
        <Target className="w-4 h-4 text-stage-understand" />
        <span className="text-sm text-muted-foreground">用户目标:</span>
        <Badge variant="outline" className="stage-understand border-stage-understand/30">
          {data.user_goal}
        </Badge>
        {data.cognitive_strategy && (
          <>
            <ArrowRight className="w-3 h-3 text-muted-foreground" />
            <Badge variant="outline" className="text-xs">
              {data.cognitive_strategy.reasoning_topology}
            </Badge>
          </>
        )}
      </div>

      {/* Keywords */}
      {data.keywords_bm25 && data.keywords_bm25.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">BM25 关键词:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {data.keywords_bm25.map((kw, i) => (
              <Badge key={i} variant="secondary" className="font-mono text-xs">
                {kw}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Vector Queries */}
      {data.queries_vector && data.queries_vector.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <FileSearch className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">向量检索语句:</span>
          </div>
          <div className="code-block space-y-1">
            {data.queries_vector.map((q, i) => (
              <div key={i} className="text-xs">
                <span className="text-primary">[{i + 1}]</span> {q}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Facets */}
      {data.information_facets && data.information_facets.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Lightbulb className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">信息面 (Facets):</span>
          </div>
          <div className="space-y-2">
            {data.information_facets.map((facet) => (
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
    </div>
  );
}

function RetrieveOutput({ data }: { data: { candidates: CandidateDoc[]; total_retrieved: number; retrieval_methods: string[] } }) {
  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-muted-foreground">召回文档:</span>
        <span className="font-mono text-stage-retrieve">{data.total_retrieved}</span>
        <span className="text-muted-foreground">检索方式:</span>
        <div className="flex gap-2">
          {data.retrieval_methods.map((m, i) => (
            <Badge key={i} variant="outline" className="text-xs">
              {m}
            </Badge>
          ))}
        </div>
      </div>

      {/* Candidates */}
      <div className="space-y-2">
        {data.candidates.slice(0, 4).map((doc, i) => (
          <motion.div
            key={doc.doc_id}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-3 rounded-lg bg-muted/30 border border-border/50"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-muted-foreground">
                    #{doc.doc_id}
                  </span>
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs",
                      doc.source === 'vector' && "text-stage-retrieve border-stage-retrieve/30",
                      doc.source === 'bm25' && "text-stage-report border-stage-report/30",
                      doc.source === 'hybrid' && "text-stage-judge border-stage-judge/30"
                    )}
                  >
                    {doc.source}
                  </Badge>
                </div>
                <h4 className="font-medium text-sm mt-1 line-clamp-1">{doc.title}</h4>
                <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                  {doc.abstract}
                </p>
              </div>
              <div className="text-right shrink-0">
                <div className="font-mono text-sm text-stage-retrieve">
                  {(doc.score * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground">相关度</div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function JudgeOutput({ data }: { data: { verified_evidence: Evidence[]; rejected_count: number; acceptance_rate: number } }) {
  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="flex items-center gap-6 text-sm">
        <div>
          <span className="text-muted-foreground">验证通过:</span>
          <span className="ml-2 font-mono text-stage-judge">{data.verified_evidence.length}</span>
        </div>
        <div>
          <span className="text-muted-foreground">淘汰:</span>
          <span className="ml-2 font-mono text-destructive">{data.rejected_count}</span>
        </div>
        <div>
          <span className="text-muted-foreground">通过率:</span>
          <span className="ml-2 font-mono text-stage-judge">
            {(data.acceptance_rate * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Evidence */}
      <div className="space-y-3">
        {data.verified_evidence.map((ev, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.15 }}
            className="p-3 rounded-lg border border-stage-judge/30 bg-stage-judge/5"
          >
            <div className="flex items-start gap-3">
              <Quote className="w-4 h-4 text-stage-judge shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm italic">{ev.content}</p>
                <div className="flex items-center gap-3 mt-2 text-xs">
                  <Badge variant="outline" className="text-stage-judge border-stage-judge/30">
                    {ev.facet_id}
                  </Badge>
                  <span className="text-muted-foreground">{ev.reason}</span>
                  <span className="ml-auto font-mono text-stage-judge">
                    {(ev.relevance_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function AnalyzeOutput({ data }: { data: GapAnalysis }) {
  const isSufficient = data.status === 'sufficient';

  return (
    <div className="space-y-4">
      {/* Status */}
      <div className={cn(
        "flex items-center gap-3 p-3 rounded-lg border",
        isSufficient
          ? "border-stage-report/30 bg-stage-report/10"
          : "border-accent/30 bg-accent/10"
      )}>
        {isSufficient ? (
          <CheckCircle className="w-5 h-5 text-stage-report" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-accent" />
        )}
        <div>
          <div className={cn(
            "font-medium",
            isSufficient ? "text-stage-report" : "text-accent"
          )}>
            {isSufficient ? '信息覆盖充足' : '检测到信息缺口'}
          </div>
          <div className="text-sm text-muted-foreground">
            覆盖率: {(data.coverage_score * 100).toFixed(0)}% | 迭代: {data.iteration}
          </div>
        </div>
      </div>

      {/* Missing facets */}
      {!isSufficient && data.missing_facets && data.missing_facets.length > 0 && (
        <div>
          <div className="text-sm text-muted-foreground mb-2">缺失信息面:</div>
          <div className="space-y-1">
            {data.missing_facets.map((f, i) => (
              <div key={i} className="text-sm text-accent flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-accent" />
                {f}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suggested queries */}
      {data.suggested_queries && data.suggested_queries.length > 0 && (
        <div>
          <div className="text-sm text-muted-foreground mb-2">建议补充查询:</div>
          <div className="code-block space-y-1">
            {data.suggested_queries.map((q, i) => (
              <div key={i} className="text-xs">
                <span className="text-accent">→</span> {q}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ReportOutput({ data }: { data: FinalReport }) {
  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="p-4 rounded-lg bg-gradient-to-br from-stage-report/10 to-transparent border border-stage-report/20">
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-stage-report animate-pulse" />
          <span className="text-sm font-medium text-stage-report">分析结论</span>
          <span className="ml-auto text-xs font-mono text-muted-foreground">
            置信度: {(data.confidence_score * 100).toFixed(0)}%
          </span>
        </div>
        <p className="text-sm leading-relaxed">{data.summary}</p>
      </div>

      {/* Key findings */}
      <div>
        <div className="text-sm text-muted-foreground mb-2">核心发现:</div>
        <div className="space-y-2">
          {data.key_findings.map((finding, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className="flex items-start gap-2 text-sm"
            >
              <span className="font-mono text-stage-report shrink-0">[{i + 1}]</span>
              <span>{finding}</span>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Citations */}
      <div>
        <div className="text-sm text-muted-foreground mb-2">引用来源:</div>
        <div className="flex flex-wrap gap-2">
          {data.citations.map((cite, i) => (
            <Badge key={i} variant="outline" className="text-xs font-normal">
              {cite}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
}
