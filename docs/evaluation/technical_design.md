# Crux 评测体系技术设计文档

## 1. 文档目标

本文档用于说明 Crux 项目评测体系的技术设计、实现结构、执行流程和扩展方式。目标是将当前的模块级评测与端到端流水线评测标准化，支持后续的数据集扩充、持续集成接入和模块能力优化。

本文档对应的实现位于：

- `src/crux/evaluation/`
- `data/evaluation/`
- `docs/evaluation/`

## 2. 设计目标

Crux 评测体系围绕以下目标设计：

- 标准化：统一评测对象、评测输入、评测输出、指标定义与报告格式。
- 模块化：支持 Understanding、Retrieval、Adjudication、Strategy 分模块独立评测。
- 可追踪：端到端流水线评测需要采集完整执行轨迹。
- 可扩展：新增评测模块、新增指标、新增数据集时不需要重写整套框架。
- 可离线复现：通过 stub 化 LLM 输出，保证本地评测稳定、可重复。
- 可集成：便于后续接入 CI、性能基准和可视化看板。

## 3. 评测范围

当前评测体系覆盖两类评测：

### 3.1 模块级评测

- Understanding：意图识别、约束抽取、关键词与查询生成、Schema 字段合规性。
- Retrieval：召回质量、排序质量、Top-K 命中率、检索延迟。
- Adjudication：相关性判断准确率、证据提取质量、通过率。
- Strategy：缺口识别正确率、缺失信息识别、覆盖度评分。

### 3.2 端到端流水线评测

覆盖完整链路：

`understand -> retrieve -> judge -> analyze -> ... -> report`

流水线评测不仅校验最终结果，还记录：

- 每个阶段的输入快照
- 每个阶段的输出快照
- 每个阶段执行后的合并状态
- 每个阶段日志
- 每个阶段耗时
- 迭代轮次与回流路径

## 4. 总体架构

评测框架目录如下：

```text
src/crux/evaluation/
├── __init__.py
├── base.py
├── cli.py
├── helpers.py
├── fixtures.py
├── trace.py
├── datasets/
│   ├── __init__.py
│   └── loader.py
├── metrics/
│   ├── __init__.py
│   ├── common.py
│   └── retrieval.py
├── evaluators/
│   ├── __init__.py
│   ├── understanding.py
│   ├── retrieval.py
│   ├── adjudication.py
│   ├── strategy.py
│   └── pipeline.py
└── report/
    ├── __init__.py
    └── generator.py
```

## 5. 核心组件设计

### 5.1 `BaseEvaluator`

文件：`src/crux/evaluation/base.py`

职责：

- 统一评测器接口
- 定义单 case 的执行入口
- 聚合多个 case 的结果
- 生成标准化 `EvaluationSummary`

核心数据结构：

- `EvaluationCase`
- `EvaluationResult`
- `EvaluationSummary`

其中：

- `EvaluationCase` 定义输入、期望输出、stub 数据和元信息。
- `EvaluationResult` 表示单个 case 的评测结果。
- `EvaluationSummary` 表示整个模块的一次评测摘要。

### 5.2 Dataset Loader

文件：`src/crux/evaluation/datasets/loader.py`

职责：

- 从 `data/evaluation/*.json` 加载评测数据
- 将 JSON 转换为统一的 `EvaluationCase`
- 支持按模块过滤 case

### 5.3 Metrics

文件：

- `src/crux/evaluation/metrics/common.py`
- `src/crux/evaluation/metrics/retrieval.py`

职责：

- 提供通用指标计算函数
- 将“评测器逻辑”和“指标计算逻辑”解耦

已实现指标：

- `precision / recall / f1`
- `binary_accuracy`
- `set_match_metrics`
- `text_overlap_f1`
- `Recall@K`
- `Precision@K`
- `MRR`
- `NDCG@K`

### 5.4 Fixtures 与 Stub

文件：`src/crux/evaluation/fixtures.py`

职责：

- 提供内存版数据加载器 `InMemoryDataLoader`
- 提供离线可复现的 `StubLLMClient`

设计原因：

- 模块评测和流水线评测不应依赖真实在线 LLM 服务。
- 真实 LLM 输出不稳定，不适合作为标准化回归测试基线。
- 通过 stub 方式可以把问题收敛到“模块逻辑”与“结果判定”本身。

### 5.5 Trace Recorder

文件：`src/crux/evaluation/trace.py`

职责：

- 记录端到端流水线每一阶段的轨迹
- 支持后续问题定位、评测看板和调试分析

核心结构：

- `StageTrace`
- `PipelineTrace`
- `TraceRecorder`

`StageTrace` 包含以下字段：

- `stage`
- `iteration`
- `started_at`
- `ended_at`
- `duration_ms`
- `input_snapshot`
- `output_snapshot`
- `state_after`
- `logs`
- `error`

### 5.6 Report Generator

文件：`src/crux/evaluation/report/generator.py`

职责：

- 将评测摘要输出为 JSON
- 将评测摘要输出为 Markdown

输出目录默认是：

`data/evaluation/reports/`

## 6. 各模块评测实现

### 6.1 UnderstandingEvaluator

文件：`src/crux/evaluation/evaluators/understanding.py`

评测对象：

- `UnderstandingNode`

输入来源：

- 用户查询
- stub 化的 `intent_response`

核心评测项：

- `intent_accuracy`
- `constraint_precision`
- `constraint_recall`
- `constraint_f1`
- `sparse_keyword_precision`
- `sparse_keyword_recall`
- `dense_query_precision`
- `dense_query_recall`
- `invalid_constraint_field_count`
- `latency_ms`

额外约束：

- 基于 schema 或 fixture 中的 `allowed_constraint_fields` 检查字段合规性。
- 这直接对应当前项目里已知问题：意图理解模块偶尔生成 Schema 外字段，导致检索过滤失败。

### 6.2 RetrievalEvaluator

文件：`src/crux/evaluation/evaluators/retrieval.py`

评测对象：

- `RetrievalNode`

输入来源：

- query
- intent
- 文档集合 `documents`

执行方式：

- 使用 `InMemoryDataLoader` 替换真实数据源
- 保持检索节点逻辑不变

核心评测项：

- `recall_at_k`
- `precision_at_k`
- `mrr`
- `ndcg_at_k`
- `latency_ms`
- `retrieved_count`

### 6.3 AdjudicationEvaluator

文件：`src/crux/evaluation/evaluators/adjudication.py`

评测对象：

- `AdjudicationNode`

输入来源：

- query
- intent 中的研判 rubric
- candidate docs
- stub 化批量研判结果 `judgement_batch`

核心评测项：

- `relevance_accuracy`
- `relevance_precision`
- `relevance_recall`
- `relevance_f1`
- `evidence_quality`
- `acceptance_rate`
- `latency_ms`

证据质量评估方法：

- 使用 `text_overlap_f1` 对 gold evidence 与抽取 evidence 做文本重叠度比较。

### 6.4 StrategyEvaluator

文件：`src/crux/evaluation/evaluators/strategy.py`

评测对象：

- `GapAnalysisNode`

输入来源：

- query
- verified evidence
- intent 中的信息面定义
- stub 化 gap 分析结果 `gap_response`

核心评测项：

- `gap_detection_accuracy`
- `missing_precision`
- `missing_recall`
- `missing_f1`
- `coverage_score`
- `coverage_error`
- `latency_ms`

## 7. 端到端流水线评测实现

### 7.1 PipelineEvaluator

文件：`src/crux/evaluation/evaluators/pipeline.py`

该评测器基于 `TraceablePipelineRunner` 实现完整链路评测。

### 7.2 TraceablePipelineRunner

职责：

- 实例化各模块节点
- 使用 stub 替换节点内部依赖
- 按真实工作流顺序执行阶段
- 在每个阶段结束后记录 trace

执行流程如下：

1. 初始化 state
2. 执行 `understand`
3. 执行 `retrieve`
4. 执行 `judge`
5. 执行 `analyze`
6. 若 `gap_analysis_result == insufficient`，则回流到 `retrieve`
7. 否则进入 `report`
8. 输出最终 state 和完整 trace

### 7.3 流水线指标

当前已实现：

- `total_latency_ms`
- `iteration_count`
- `trace_stage_count`
- `trace_completeness`
- `final_evidence_recall`
- `report_present`
- `gap_path_accuracy`

其中：

- `trace_completeness` 用于判断每个阶段是否都记录了输入、输出和耗时。
- `gap_path_accuracy` 用于判断实际迭代路径是否和期望路径一致。

## 8. 评测数据格式

评测数据位于：

- `data/evaluation/understanding.json`
- `data/evaluation/retrieval.json`
- `data/evaluation/adjudication.json`
- `data/evaluation/strategy.json`
- `data/evaluation/pipeline.json`

统一格式如下：

```json
{
  "cases": [
    {
      "case_id": "unique_case_id",
      "module": "understanding",
      "name": "case description",
      "input": {},
      "expected": {},
      "stubs": {},
      "metadata": {}
    }
  ]
}
```

字段说明：

- `input`：模块输入或流水线输入
- `expected`：gold label、阈值和期望路径
- `stubs`：用于替代真实 LLM 返回的固定输出
- `metadata`：评测器附加参数，如 `k`、`max_iterations`、允许字段列表等

## 9. CLI 与使用方式

入口文件：

`src/crux/evaluation/cli.py`

运行全部评测：

```bash
python -m src.crux.evaluation.cli --module all
```

运行单个模块：

```bash
python -m src.crux.evaluation.cli --module understanding
python -m src.crux.evaluation.cli --module retrieval
python -m src.crux.evaluation.cli --module adjudication
python -m src.crux.evaluation.cli --module strategy
python -m src.crux.evaluation.cli --module pipeline
```

指定数据集目录和输出目录：

```bash
python -m src.crux.evaluation.cli \
  --module all \
  --dataset-root data/evaluation \
  --output-dir data/evaluation/reports
```

## 10. 报告输出

每个模块会生成两类报告：

- JSON 报告
- Markdown 报告

默认输出路径：

`data/evaluation/reports/`

例如：

- `understanding_report.json`
- `understanding_report.md`
- `pipeline_report.json`
- `pipeline_report.md`

Markdown 报告主要用于人工查看，JSON 报告主要用于：

- CI 存档
- 看板展示
- 趋势分析
- 自动告警

## 11. 与现有 Crux 代码的集成点

### 11.1 对节点接口的复用

当前评测框架直接复用了现有节点的 `process()` 接口，因此不需要重构现有模块结构。

### 11.2 对日志体系的复用

评测框架通过节点返回结果中的：

- `_stage_logs`
- `_stage_duration_ms`

采集阶段级日志与耗时。

### 11.3 对 Strategy 模块的增强

为支持 Strategy 和流水线评测，当前已将以下信息写回 state：

- `gap_analysis_details.coverage_score`
- `gap_analysis_details.missing_info`
- `gap_analysis_details.suggested_queries`
- `gap_analysis_details.raw_analysis`

### 11.4 对 LLMClient 的增强

为支持对象型返回的离线评测，`call_json_with_object()` 已支持：

- mock 响应映射到 Pydantic 对象
- fallback 响应映射到 Pydantic 对象

## 12. 当前已验证能力

当前样例集已经完成以下验证：

- 4 个模块级评测器可独立执行
- 1 个端到端流水线评测可闭环执行
- 流水线 trace 可以完整记录多轮迭代过程
- 报告可自动导出到 Markdown 和 JSON

当前样例评测结果已验证：

- 模块级评测可通过
- 流水线评测可通过
- 端到端 trace 完整率为 1.0

## 13. 当前局限

当前实现仍有以下边界：

- 数据集仍以样例 fixture 为主，尚未接入大规模真实标注集。
- 部分质量指标仍采用文本重叠近似，而非更严格的结构化人工标注。
- 流水线性能评测尚未区分 CPU、GPU、外部 API 延迟等细项。
- 评测结果尚未接入 CI 门禁与趋势看板。
- Understanding 的 prompt 侧 schema 约束仍然不足，评测已能暴露该问题，但业务侧还未彻底修复。

## 14. 后续演进建议

建议按以下顺序继续推进：

### 14.1 数据层

- 将真实标注集接入 `data/evaluation/`
- 为每个模块扩充正常场景、边界场景、异常场景
- 建立统一标注规范

### 14.2 指标层

- 增加模块级置信度分析
- 增加端到端报告质量打分
- 增加延迟分布统计，如 P50、P95、P99
- 增加资源消耗指标，如内存、CPU、GPU 使用率

### 14.3 工程层

- 接入 GitHub Actions
- 将评测结果上传为 artifact
- 增加回归阈值校验
- 在 PR 阶段自动触发 smoke evaluation

### 14.4 产品化层

- 建立评测结果 Dashboard
- 支持按时间、分支、模块查看历史趋势
- 支持对比不同 prompt、参数、模型版本的评测结果

## 15. 总结

本次评测体系实现为 Crux 建立了一个标准化的技术底座：

- 通过统一数据结构和评测器接口实现模块级标准评测
- 通过可追踪流水线 runner 实现端到端闭环评测
- 通过 stub 化依赖实现本地可复现、可离线回归
- 通过报告导出能力为 CI、看板和后续优化提供基础

这意味着后续的模块优化工作可以进入“评测 -> 分析 -> 优化 -> 回归验证”的闭环，而不再依赖零散的人工示例测试。
