// Crux Agent 类型定义

export type StageStatus = 'pending' | 'processing' | 'completed' | 'error';

export type StageId = 'understand' | 'retrieve' | 'judge' | 'analyze' | 'report';

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
  metadata?: Record<string, unknown>;
}

export interface Evidence {
  doc_id: string;
  content: string;
  reason: string;
  source?: string;
  relevance_score: number;
  facet_id?: string;
}

export interface GapAnalysis {
  status: 'sufficient' | 'insufficient';
  coverage_score: number;
  missing_facets: string[];
  suggested_queries?: string[];
  iteration: number;
}

export interface FinalReport {
  summary: string;
  key_findings: string[];
  evidence_chain: Evidence[];
  confidence_score: number;
  citations: string[];
}

// Stage output types
export interface StageOutput {
  understand?: IntentObject;
  retrieve?: {
    candidates: CandidateDoc[];
    total_retrieved: number;
    retrieval_methods: string[];
  };
  judge?: {
    verified_evidence: Evidence[];
    rejected_count: number;
    acceptance_rate: number;
  };
  analyze?: GapAnalysis;
  report?: FinalReport;
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
}

export interface PipelineState {
  query: string;
  stages: PipelineStage[];
  currentStageIndex: number;
  iteration: number;
  isRunning: boolean;
  isCompleted: boolean;
  error?: string;
}
