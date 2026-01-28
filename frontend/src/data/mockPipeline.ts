// 模拟 Crux 管道数据

import type { 
  IntentObject, 
  CandidateDoc, 
  Evidence, 
  GapAnalysis, 
  FinalReport,
  PipelineStage 
} from '@/types/crux';

export const initialStages: PipelineStage[] = [
  {
    id: 'understand',
    name: 'Intent Understanding',
    nameCn: '意图理解',
    description: 'Schema感知的深度意图解析，将自然语言转化为结构化 IntentObject',
    status: 'pending',
  },
  {
    id: 'retrieve',
    name: 'Hybrid Retrieval',
    nameCn: '混合召回',
    description: '并行执行字段过滤、BM25稀疏检索和向量语义检索',
    status: 'pending',
  },
  {
    id: 'judge',
    name: 'Deep Adjudication',
    nameCn: '深度研判',
    description: '准则引导的证据级评估，去噪并提取高价值证据',
    status: 'pending',
  },
  {
    id: 'analyze',
    name: 'Gap Analysis',
    nameCn: '缺口分析',
    description: '检测信息覆盖度，识别缺口并决定是否回流补充检索',
    status: 'pending',
  },
  {
    id: 'report',
    name: 'Report Generation',
    nameCn: '报告生成',
    description: '合成最终深度报告，附带证据链和置信度评估',
    status: 'pending',
  },
];

// 根据查询生成模拟数据
export function generateMockIntent(query: string): IntentObject {
  // 检测查询类型
  const isInvestigative = query.includes('为什么') || query.includes('如何') || query.includes('原因');
  const isComparative = query.includes('对比') || query.includes('区别') || query.includes('比较');
  const isDebug = query.includes('报错') || query.includes('问题') || query.includes('失败');
  
  let userGoal = 'FACTUAL';
  if (isInvestigative) userGoal = 'INVESTIGATIVE';
  else if (isComparative) userGoal = 'COMPARATIVE';
  else if (isDebug) userGoal = 'DEBUGGING';

  // 提取关键词
  const keywords = query
    .replace(/[，。？！、]/g, ' ')
    .split(/\s+/)
    .filter(w => w.length > 1)
    .slice(0, 5);

  return {
    user_goal: userGoal,
    constraints: {
      structured_metadata: [
        { field: 'category', operator: 'in', value: ['AI', 'LLM', 'RAG'] },
        { field: 'year', operator: 'gte', value: 2023 },
      ],
      unstructured_content_patterns: [
        {
          pattern: keywords[0] || 'agent',
          pattern_type: 'exact_phrase',
          scope: 'full_text',
          is_negative: false,
          rationale: '核心查询关键词',
        },
      ],
    },
    keywords_bm25: keywords,
    queries_vector: [
      query,
      `${keywords.join(' ')} 技术原理`,
      `${keywords.join(' ')} 最新研究`,
    ],
    rubric: '文档需直接回答用户查询，包含具体技术细节或实验数据',
    cognitive_strategy: {
      user_goal: userGoal as any,
      reasoning_topology: isInvestigative ? 'CAUSAL_CHAIN' : 'FLAT_LIST',
      depth_requirement: 'DEEP',
    },
    information_facets: [
      { facet_id: 'F1', facet_type: 'DEFINITION', description: '核心概念定义' },
      { facet_id: 'F2', facet_type: 'SOLUTION', description: '技术方案描述', dependency: 'F1' },
      { facet_id: 'F3', facet_type: 'EVIDENCE', description: '实验验证数据', dependency: 'F2' },
    ],
  };
}

export function generateMockCandidates(intent: IntentObject): CandidateDoc[] {
  const papers = [
    {
      title: 'NestBrowse: 面向智能体信息搜寻的嵌套式浏览器操作学习',
      abstract: '提出了一种嵌套的浏览器使用框架，将交互解耦为外循环和内循环，简化代理推理的同时有效获取深层网页信息...',
      source: 'vector' as const,
    },
    {
      title: 'ReAct: Synergizing Reasoning and Acting in Language Models',
      abstract: '通过交织推理轨迹和特定任务动作，使LLM能够以更可解释的方式解决复杂任务...',
      source: 'bm25' as const,
    },
    {
      title: 'Chain-of-Thought Prompting for Complex Reasoning',
      abstract: '证明了思维链提示能显著提升大型语言模型在算术和符号推理任务上的表现...',
      source: 'hybrid' as const,
    },
    {
      title: 'Retrieval-Augmented Generation for Knowledge-Intensive NLP',
      abstract: 'RAG 模型将预训练的序列到序列模型与可微分检索器结合，在开放域问答任务上取得了 SOTA...',
      source: 'vector' as const,
    },
    {
      title: 'Self-RAG: Learning to Retrieve, Generate, and Critique',
      abstract: '通过自我反思标记实现按需检索和自我评估，提高生成质量和事实准确性...',
      source: 'hybrid' as const,
    },
  ];

  return papers.map((p, i) => ({
    doc_id: `doc_${i + 1}`,
    title: p.title,
    abstract: p.abstract,
    score: 0.95 - i * 0.08 + Math.random() * 0.05,
    source: p.source,
    metadata: { year: 2024, category: 'AI' },
  }));
}

export function generateMockEvidence(candidates: CandidateDoc[]): Evidence[] {
  return candidates.slice(0, 3).map((doc, i) => ({
    doc_id: doc.doc_id,
    content: `"${doc.abstract.slice(0, 100)}..." —— 该段落直接支持用户查询的核心问题。`,
    reason: i === 0 
      ? '高度相关：直接回答了技术方案问题' 
      : i === 1 
        ? '补充证据：提供了理论基础' 
        : '实验支撑：包含定量评估数据',
    source: doc.title,
    relevance_score: 0.92 - i * 0.1,
    facet_id: `F${i + 1}`,
  }));
}

export function generateMockGapAnalysis(iteration: number): GapAnalysis {
  // 第一次迭代可能发现缺口，后续迭代通常足够
  const isInsufficient = iteration === 1 && Math.random() > 0.6;
  
  return {
    status: isInsufficient ? 'insufficient' : 'sufficient',
    coverage_score: isInsufficient ? 0.65 : 0.92,
    missing_facets: isInsufficient ? ['F3: 实验验证数据'] : [],
    suggested_queries: isInsufficient ? ['实验结果对比分析', '性能评估benchmark'] : undefined,
    iteration,
  };
}

export function generateMockReport(evidence: Evidence[], query: string): FinalReport {
  return {
    summary: `基于对 ${evidence.length} 篇高质量文献的深度分析，针对"${query.slice(0, 30)}..."这一问题，我们得出以下结论：当前 AgenticRAG 技术通过四阶段闭环架构（意图理解→混合召回→深度研判→缺口分析）实现了从浅层匹配到深度推理的演进。核心创新在于 Schema 感知的意图解析和准则引导的证据研判机制。`,
    key_findings: [
      '嵌套式浏览器框架可将交互复杂度降低 40%，同时保持信息获取完整性',
      '混合检索策略（BM25 + 向量）相比单一方法提升召回率 23%',
      '深度研判阶段可过滤 60-70% 的语义相似但事实无关文档',
      '闭环缺口分析机制确保信息覆盖度达到 95% 以上',
    ],
    evidence_chain: evidence,
    confidence_score: 0.89,
    citations: evidence.map(e => e.source || e.doc_id),
  };
}
