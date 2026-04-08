# Crux

An agentic RAG framework powered by deep intent understanding.

---

## 整体流程

```
用户查询 (user_query)
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  Module 1 · understand  (执行一次，不参与循环)         │
│                                                     │
│  Stage 1 (并行)                                     │
│    1a. query  →  CognitiveState                     │
│          认知模式 (exploratory / deep_thinking /     │
│                   verification / action)            │
│          逻辑依赖 (independent_parallel /           │
│                   chain_dependent /                 │
│                   conflict_resolution)              │
│    1b. query  →  Constraints                        │
│          结构化元数据约束 + 文本模式约束              │
│                                                     │
│  Stage 2 (串行)                                     │
│    query + CognitiveState  →  AgentPlan             │
│          InformationFacets (F1, F2, ...)            │
│            每个 Facet 内嵌 RelevanceRubric           │
│          CompletionCriteria (全局完成标准)           │
│                                                     │
│  Stage 3 (每个 Facet 并行)                          │
│    每个 Facet  →  FacetExpansion                    │
│          facet_query   (dense 检索句)               │
│          sparse_keywords (BM25 关键词)              │
│          hypothetical_document (HyDE)               │
│                                                     │
│  输出: IntentObject → AgentState.intent             │
└─────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  Module 2 · retrieve                                │
│                                                     │
│  读取 intent["expansions"]（仅未满足 Facet 的        │
│  Expansion，第一轮为全量）                          │
│                                                     │
│  每个 FacetExpansion 并行执行：                     │
│    BM25：  facet_query + sparse_keywords            │
│    Dense： facet_query + hypothetical_document      │
│    RRF 融合 两路结果 → 该 Facet TopK 文档           │
│                                                     │
│  Flatten，每篇文档附加 facet_id 标签                │
│  输出: candidate_docs                               │
└─────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  Module 3 · judge                                   │
│                                                     │
│  过滤 seen_doc_ids（已研判文档不重复送判）            │
│                                                     │
│  按 facet_id 分组，每组并行调用 LLM：               │
│    Prompt: Facet 描述 + RelevanceRubric + 文档列表  │
│    输出:   FacetJudgments                           │
│      每篇文档 → doc_id / summary /                  │
│                relevance_level / reason             │
│                                                     │
│  relevance_level = high / medium → verified_evidence│
│  relevance_level = low / irrelevant → rejected_docs │
│  所有研判文档 ID 写入 seen_doc_ids                  │
└─────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  Module 4 · analyze  (GapAnalysisNode)              │
│                                                     │
│  跳过已满足的 Facet (satisfied_facets 累积)         │
│  对剩余 Facet 聚合 verified_evidence                │
│                                                     │
│  调用 LLM (Verification Agent)：                    │
│    Prompt: CompletionCriteria + Facets & Evidence   │
│    输出:   FacetSufficiencyResult                   │
│      每个 Facet → satisfied (true/false) + reason   │
│                                                     │
│  新满足 Facet → 写入 satisfied_facets (set 并集)    │
│                                                     │
│  ┌─ 仍有未满足 Facet 且未达最大迭代次数 ────────────┐│
│  │  裁剪 intent["expansions"]                      ││
│  │  只保留未满足 Facet → 回流到 retrieve           ││
│  └──────────────────────────────────────────────── ┘│
│                                                     │
│  ┌─ 全部满足 或 达到最大迭代次数 ───────────────────┐│
│  │  gap_analysis_result = "sufficient"             ││
│  │  → 进入 report                                  ││
│  └──────────────────────────────────────────────── ┘│
└─────────────────────────────────────────────────────┘
      │  insufficient: 裁剪后的 intent 回流
      │  ┌──────────────────────────────┐
      │  │  仅检索未满足 Facet          │
      │  │  seen_doc_ids 去重研判       │
      │  │  satisfied_facets 累积       │
      └──┘  (最多 max_iterations 轮)
      │  sufficient
      ▼
┌─────────────────────────────────────────────────────┐
│  Module 4 · report  (ReportNode)                    │
│                                                     │
│  verified_evidence 按 Facet 分组                    │
│  输出结构化文本报告 (final_report)                  │
└─────────────────────────────────────────────────────┘
```

---

## 核心数据结构

### IntentObject（understand 输出）

```
IntentObject
├── cognitive_state
│   ├── cognitive_mode       exploratory | deep_thinking | verification | action
│   └── logical_dependency   independent_parallel | chain_dependent | conflict_resolution
│
├── agent_plan
│   ├── facets: List[InformationFacet]
│   │   ├── facet_id         F1, F2, ...
│   │   ├── description      该分面的信息需求描述
│   │   ├── dependency       前置 facet_id（chain_dependent 时使用）
│   │   └── rubric: RelevanceRubric
│   │       ├── tolerance_level       high | medium | low
│   │       ├── quality_preference    偏好文档类型列表
│   │       └── content_requirements  文档必须满足的内容特征列表
│   │
│   └── criteria: CompletionCriteria
│       ├── metric_type          coverage | precision | consistency | actionability
│       ├── threshold_description  完成条件的自然语言描述
│       └── specific_conditions    Verification Agent 逐条检查的判断项列表
│
├── expansions: List[FacetExpansion]  （与 facets 1-to-1，按 facet_id 对应）
│   ├── facet_id
│   ├── facet_query           dense 检索句
│   ├── sparse_keywords       BM25 关键词列表
│   └── hypothetical_document HyDE 假设答案文档
│
└── constraints: Constraints
    ├── structured_metadata           字段级过滤条件（year / category / source）
    └── unstructured_content_patterns 文本模式约束（精确短语 / 正则 / 通配符）
```

### AgentState（LangGraph 全局状态）

| 字段 | 类型 | 说明 |
|---|---|---|
| `user_query` | `str` | 原始用户查询 |
| `intent` | `Dict` | `IntentObject.model_dump()` |
| `candidate_docs` | `List[dict]` | 当前轮检索结果，含 `facet_id` 标签 |
| `verified_evidence` | `List[dict]` *(累积)* | judge 采纳的文档，含 `facet_id` / `summary` / `relevance_level` / `reason` |
| `rejected_docs` | `List[dict]` *(累积)* | judge 拒绝的文档 |
| `satisfied_facets` | `Set[str]` *(并集)* | 已满足的 Facet ID，跨迭代累积 |
| `seen_doc_ids` | `Set[str]` *(并集)* | 已研判文档 ID，避免重复送判 |
| `gap_analysis_result` | `"sufficient" \| "insufficient"` | 控制条件边走向 |
| `search_iteration` | `int` | 当前迭代轮次 |
| `final_report` | `str` | 最终报告文本 |

---

## 目录结构

```
src/crux/
├── state.py                   # AgentState (LangGraph TypedDict)
├── graph.py                   # AgentGraph (LangGraph StateGraph)
├── config.py                  # CruxConfig
│
├── state/                     # Pydantic 模型定义
│   ├── cognitive.py           # CognitiveModeType, LogicalDependencyType, CognitiveState
│   ├── constraints.py         # StructuredConstraint, ContentConstraint, Constraints
│   ├── plan.py                # RelevanceRubric, InformationFacet, CompletionCriteria, AgentPlan
│   ├── expansion.py           # FacetExpansion
│   ├── intent.py              # IntentObject
│   └── retrieval.py           # DocumentJudgment, FacetJudgments,
│                              # FacetSufficiency, FacetSufficiencyResult
│
├── modules/
│   ├── understanding/
│   │   ├── node.py            # UnderstandingNode (4-stage pipeline)
│   │   └── prompts.py         # COGNITIVE_STATE_PROMPT, CONSTRAINTS_PROMPT,
│   │                          # AGENT_PLAN_PROMPT, FACET_EXPANSION_PROMPT
│   ├── retrieval/
│   │   └── node.py            # RetrievalNode (Per-Facet BM25 + Dense + RRF)
│   ├── judge/
│   │   ├── node.py            # JudgeNode (Per-Facet 研判)
│   │   └── prompts.py         # FACET_JUDGE_PROMPT
│   └── strategy/
│       ├── node.py            # GapAnalysisNode + ReportNode
│       └── prompts.py         # FACET_SUFFICIENCY_PROMPT
│
├── context/
│   └── builder.py             # ContextBuilder (prompt 构建 + 认知/依赖指导文本注入)
│
├── utils/
│   ├── base.py                # BaseNode
│   └── llm_client.py          # LLMClient (call_object / call_json / batch_* + mock)
│
└── data/                      # 数据加载层
    └── loaders/
        ├── base.py
        ├── json_loader.py
        └── ...
```

---

## 运行命令

```bash
# 后端
python backend/main.py

# 前端
cd frontend && npm install && npm run dev
```