# Crux 评估框架流程图

## 1. 总体流程

```mermaid
flowchart TD
    A[开始: 触发评估 CLI 或 CI] --> B[加载评测数据集<br/>data/evaluation/*.json]
    B --> C[解析 EvaluationCase]
    C --> D{评估类型}

    D -->|模块级评估| E[选择模块评测器<br/>Understanding / Retrieval / Adjudication / Strategy]
    D -->|端到端评估| F[选择 PipelineEvaluator]

    E --> G[构建评测配置 CruxConfig]
    F --> G

    G --> H{是否存在 Stub}
    H -->|是| I[注入 StubLLMClient / InMemoryDataLoader]
    H -->|否| J[使用真实 LLMClient]

    I --> K[执行模块或流水线]
    J --> K

    K --> L[收集结构化输出]
    L --> M[计算规则指标<br/>Recall@K / F1 / Latency / Trace Completeness ...]
    M --> N[调用 LLM Judge 做语义评估]
    N --> O[融合规则指标 + LLM 评分]
    O --> P[生成 EvaluationResult]
    P --> Q[聚合为 EvaluationSummary]
    Q --> R[导出 JSON / Markdown 报告]
    R --> S[结束]
```

## 2. 模块级评估流程

```mermaid
flowchart TD
    A[读取单个 EvaluationCase] --> B[构建对应 Evaluator]
    B --> C[执行目标模块 Node.process]
    C --> D[拿到实际输出 actual]
    D --> E[计算辅助规则指标]
    E --> F[组织评测 Payload<br/>query / expected / actual / constraints]
    F --> G[LLMEvaluationJudge]
    G --> H[返回结构化裁判结果<br/>overall_score / dimensions / issues]
    H --> I[判定是否通过]
    I --> J[写入单 case EvaluationResult]
```

## 3. 端到端流水线评估流程

```mermaid
flowchart TD
    A[读取 Pipeline Case] --> B[初始化 TraceablePipelineRunner]
    B --> C[初始化全局 State]
    C --> D[understand]
    D --> E[retrieve]
    E --> F[judge]
    F --> G[analyze]
    G --> H{gap_analysis_result 是否 insufficient}
    H -->|是| E
    H -->|否| I[report]
    I --> J[输出 final_state]
    J --> K[生成完整 trace<br/>stage input/output/state/logs/duration]
    K --> L[计算规则指标<br/>gap_path_accuracy / final_evidence_recall / trace_completeness]
    L --> M[LLM Judge 评估最终报告与轨迹质量]
    M --> N[合成 Pipeline EvaluationResult]
```

## 4. LLM Judge 内部流程

```mermaid
flowchart TD
    A[接收 task_name / instructions / payload / dimensions] --> B[构建评测 Prompt]
    B --> C[调用 LLMClient.call_json_with_object]
    C --> D[返回 LLMJudgeVerdict]
    D --> E[标准化维度结果]
    E --> F[输出<br/>overall_score / pass_recommendation / summary / dimensions]
```

## 5. 评估框架分层结构

```mermaid
flowchart LR
    A[数据层<br/>data/evaluation/*.json] --> B[执行层<br/>Evaluators / Runner]
    B --> C[指标层<br/>metrics/*.py]
    B --> D[语义裁判层<br/>llm_judge.py]
    B --> E[轨迹层<br/>trace.py]
    C --> F[结果聚合层<br/>base.py]
    D --> F
    E --> F
    F --> G[报告输出层<br/>report/generator.py]
```

## 6. 使用建议

- 文档中直接粘贴第 1 张和第 3 张图，适合技术说明。
- 汇报场景优先使用第 1 张和第 5 张图，信息密度更合适。
- 如果要做 PPT，我建议把第 1 张图再压缩成“输入 -> 执行 -> 评分 -> 报告”四段式。
