// Crux Agent 类型定义

export type StageStatus = 'pending' | 'processing' | 'completed' | 'error';

export type StageId = 'understand' | 'retrieve' | 'judge' | 'analyze' | 'report';

export type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'DEBUG';

export interface StageLog {
  level: LogLevel;
  message: string;
  timestamp: number;
  details?: Record<string, unknown>;
  iteration?: number;
}

export interface ExecutionStats {
  totalCandidates: number;
  verifiedCount: number;
  rejectedCount: number;
  tokensUsed: number;
  processingTimeMs: number;
  iterationCount: number;
}

export interface CognitiveStrategy {
  user_goal: 'INVESTIGATIVE' | 'FACTUAL' | 'DEBUGGING' | 'COMPARATIVE';
  reasoning_topology: 'CAUSAL_CHAIN' | 'TEMPORAL_SEQUENCE' | 'FLAT_LIST';
  depth_requirement: 'DEEP' | 'SHALLOW';
}

export interface InformationFacet {
  facet_id: string;
  facet_type: 'CAUSE' | 'CONSEQUENCE' | 'DEFINITION' | 'SOLUTION' | 'EVIDENCE';
  description: string;
  dependency?: string;
}

export interface StructuredConstraint {
  field: string;
  operator: 'eq' | 'neq' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'range';
  value: string | number | string[] | number[];
}

export interface ContentPattern {
  pattern: string;
  pattern_type: 'regex' | 'exact_phrase' | 'wildcard';
  scope: 'full_text' | 'title' | 'abstract';
  is_negative: boolean;
  rationale?: string;
}

export interface IntentObject {
  user_goal: string;
  constraints: {
    structured_metadata: StructuredConstraint[];
    unstructured_content_patterns: ContentPattern[];
  };
  keywords_bm25: string[];
  queries_vector: string[];
  rubric: string;
  cognitive_strategy?: CognitiveStrategy;
  information_facets?: InformationFacet[];
}

export interface CandidateDoc {
  doc_id: string;
  title: string;
  abstract: string;
  score: number;
  source: 'bm25' | 'vector' | 'hybrid';
  authors?: string[];
  year?: string;
  url?: string;
  metadata?: Record<string, unknown>;
}

export interface Evidence {
  doc_id: string;
  content: string;
  reason: string;
  source?: string;
  relevance_score: number;
  facet_id?: string;
  metadata?: Record<string, unknown>;
}

export interface GapAnalysis {
  status: 'sufficient' | 'insufficient';
  coverage_score: number;
  missing_facets: string[];
  suggested_queries?: string[];
  iteration: number;
  should_loop_back?: boolean;
}

export interface FinalReport {
  summary: string;
  key_findings: string[];
  evidence_chain: Evidence[];
  confidence_score: number;
  citations: string[];
  total_iterations?: number;
}

// Stage output types
export interface StageOutput {
  understand?: IntentObject;
  retrieve?: {
    candidates: CandidateDoc[];
    total_retrieved: number;
    iteration?: number;
  };
  judge?: {
    verified_evidence: Evidence[];
    new_evidence_count?: number;
    total_evidence?: number;
    iteration?: number;
  };
  analyze?: GapAnalysis;
  report?: FinalReport;
}

// 每轮迭代的结果
export interface IterationResult {
  iteration: number;
  candidates: CandidateDoc[];
  evidence: Evidence[];
  gapStatus?: 'sufficient' | 'insufficient';
}

export interface PipelineStage {
  id: StageId;
  name: string;
  nameCn: string;
  description: string;
  status: StageStatus;
  startTime?: number;
  endTime?: number;
  output?: StageOutput[StageId];
  logs?: StageLog[];
}

export interface PipelineState {
  query: string;
  stages: PipelineStage[];
  currentStageIndex: number;
  iteration: number;
  isRunning: boolean;
  isCompleted: boolean;
  error?: string;
  stats?: ExecutionStats;
  // 按轮次存储的日志
  allLogs: StageLog[];
  // 按轮次存储的结果
  iterations: IterationResult[];
}
