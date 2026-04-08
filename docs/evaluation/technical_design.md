# Crux 评测体系技术设计文档

## 1. 文档目标

本文档说明 Crux 当前评测体系的技术设计、实现结构、执行流程和扩展方式。

本次文档更新的重点是：

- 评测方法已从“规则硬匹配为主”升级为“规则指标 + LLM 语义裁判”
- 评测主判断逻辑已切换为基于 `LLMClient` 的结构化语义评分
- 模块级与流水线级评测都支持语义等价判断，不再过度依赖 `==`、集合交集或简单文本重叠

对应实现位于：

- `src/crux/evaluation/`
- `data/evaluation/`
- `docs/evaluation/`

## 2. 设计目标

Crux 评测体系围绕以下目标设计：

- 标准化：统一评测对象、输入格式、输出格式、指标定义与报告格式
- 模块化：支持 Understanding、Retrieval、Adjudication、Strategy 分模块独立评测
- 可追踪：支持端到端流水线执行轨迹采集
- 语义化：支持基于大模型的语义判断，避免脆弱的字符串硬匹配
- 可离线复现：支持用 stub 固定模块输出和评测输出，保障本地稳定回归
- 可集成：为后续 CI、看板和趋势分析保留标准接口

## 3. 评测方法总览

当前采用“双轨评测”：

### 3.1 结构化指标

结构化指标仍然保留，但定位已经调整为：

- 辅助指标
- 硬约束指标
- 可解释统计指标

典型指标包括：

- `Recall@K`
- `Precision@K`
- `MRR`
- `NDCG@K`
- 延迟
- Schema 字段合法性
- Trace 完整度

这些指标适合做确定性检查，但不再作为所有模块的唯一通过依据。

### 3.2 LLM 语义裁判

新增语义裁判层，由 `LLMClient` 驱动。

每个评测器会把以下信息交给大模型：

- 原始输入
- 期望输出或参考答案
- 实际模块输出
- 必要的上下文约束

大模型返回统一结构化结果：

- `overall_score`
- `pass_recommendation`
- `summary`
- `strengths`
- `issues`
- `dimensions[]`

其中每个 `dimension` 都包含：

- `name`
- `score`
- `reasoning`

这使得评测从“机械匹配”转向“语义评分 + 原因解释”。

## 4. 总体架构

评测框架目录如下：

```text
src/crux/evaluation/
├── __init__.py
├── base.py
├── cli.py
├── helpers.py
├── fixtures.py
├── llm_judge.py
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
- 定义单 case 执行入口
- 聚合多个 case 的结果
- 生成 `EvaluationSummary`

核心数据结构：

- `EvaluationCase`
- `EvaluationResult`
- `EvaluationSummary`

### 5.2 Dataset Loader

文件：`src/crux/evaluation/datasets/loader.py`

职责：

- 从 `data/evaluation/*.json` 加载评测数据
- 将 JSON 转换为统一 `EvaluationCase`
- 支持模块过滤
- 兼容 `utf-8-sig`，避免 BOM 导致的解析失败

### 5.3 Metrics

文件：

- `src/crux/evaluation/metrics/common.py`
- `src/crux/evaluation/metrics/retrieval.py`

职责：

- 提供确定性结构化指标
- 为 LLM 评测提供辅助数值信号

当前仍保留的指标包括：

- `precision / recall / f1`
- `binary_accuracy`
- `set_match_metrics`
- `text_overlap_f1`
- `Recall@K`
- `Precision@K`
- `MRR`
- `NDCG@K`

说明：

- 这些函数仍然有效，但已不再适合作为所有模块的唯一主评判方式。
- 当前它们更多用于辅助分析、硬约束和趋势跟踪。

### 5.4 Fixtures 与 Stub

文件：`src/crux/evaluation/fixtures.py`

职责：

- 提供 `InMemoryDataLoader`
- 提供 `StubLLMClient`

当前 stub 分两类：

- 模块执行 stub：替代真实业务阶段的模型返回
- 评测裁判 stub：替代真实评测模型返回

这样可以在不调用外部模型的情况下完整跑通整个评测框架。

### 5.5 `LLMEvaluationJudge`

文件：`src/crux/evaluation/llm_judge.py`

这是本次重构新增的核心组件。

职责：

- 基于 `LLMClient` 构建统一评测裁判
- 生成结构化评测 prompt
- 要求模型按统一 JSON 格式返回评分结果
- 对缺失维度做补齐与归一化

核心模型：

- `EvaluationDimension`
- `LLMJudgeVerdict`
- `LLMEvaluationJudge`

`LLMJudgeVerdict` 字段包括：

- `overall_score`
- `pass_recommendation`
- `summary`
- `strengths`
- `issues`
- `dimensions`

### 5.6 Helper 层

文件：`src/crux/evaluation/helpers.py`

新增职责：

- 构建评测用 `CruxConfig`
- 构建语义裁判 `build_evaluation_judge()`
- 扁平化维度分数 `dimension_scores()`
- 合并阶段状态
- 清洗轨迹输出

### 5.7 Trace Recorder

文件：`src/crux/evaluation/trace.py`

职责：

- 记录端到端流水线每一阶段的执行轨迹
- 支持后续问题定位、回放、看板分析

`StageTrace` 记录：

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

### 5.8 Report Generator

文件：`src/crux/evaluation/report/generator.py`

职责：

- 输出 JSON 报告
- 输出 Markdown 报告

默认输出目录：

`data/evaluation/reports/`

## 6. 模块评测设计

## 6.1 UnderstandingEvaluator

文件：`src/crux/evaluation/evaluators/understanding.py`

评测对象：

- `UnderstandingNode`

评测方法：

- 先执行模块，得到 `intent`
- 再调用 `LLMEvaluationJudge` 做语义评分
- 规则指标仅保留为辅助与硬约束

保留的结构化指标：

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

新增 LLM 评分维度：

- `intent_alignment`
- `constraint_semantics`
- `retrieval_plan_quality`
- `rubric_quality`

当前通过条件：

- `llm_overall_score >= min_llm_overall_score`
- `pass_recommendation == true`
- `invalid_constraint_field_count == 0`

说明：

- 这专门用于解决当前已知问题：Schema 外字段不一定能通过简单语义相似度判断，因此仍保留硬性字段合法性检查。

## 6.2 RetrievalEvaluator

文件：`src/crux/evaluation/evaluators/retrieval.py`

评测对象：

- `RetrievalNode`

执行方式：

- 使用 `InMemoryDataLoader`
- 保持真实检索节点逻辑不变
- 结果由 LLM 评估“是否真正满足检索需求”

保留的结构化指标：

- `recall_at_k`
- `precision_at_k`
- `mrr`
- `ndcg_at_k`
- `latency_ms`
- `retrieved_count`

新增 LLM 评分维度：

- `topk_relevance`
- `ranking_quality`
- `coverage_of_need`
- `constraint_alignment`

当前通过条件：

- `llm_overall_score >= min_llm_overall_score`
- `pass_recommendation == true`
- `recall_at_k >= min_recall_at_k`

说明：

- Retrieval 仍然保留 `Recall@K` 等指标，因为这类指标在检索任务中具有稳定解释性。
- 但是否“真正满足查询需求”，交由 LLM 做语义评审。

## 6.3 AdjudicationEvaluator

文件：`src/crux/evaluation/evaluators/adjudication.py`

评测对象：

- `AdjudicationNode`

保留的结构化指标：

- `relevance_accuracy`
- `relevance_precision`
- `relevance_recall`
- `relevance_f1`
- `evidence_quality`
- `acceptance_rate`
- `latency_ms`

新增 LLM 评分维度：

- `relevance_decision_quality`
- `evidence_quality`
- `rejection_quality`
- `rubric_alignment`

说明：

- 这里的结构化 `evidence_quality` 仍使用文本重叠近似。
- 但最终判断转交给 LLM，因为真实场景里证据通常存在改写、压缩和释义。

当前通过条件：

- `llm_overall_score >= min_llm_overall_score`
- `pass_recommendation == true`
- `relevance_accuracy >= min_relevance_accuracy`

## 6.4 StrategyEvaluator

文件：`src/crux/evaluation/evaluators/strategy.py`

评测对象：

- `GapAnalysisNode`

保留的结构化指标：

- `gap_detection_accuracy`
- `missing_precision`
- `missing_recall`
- `missing_f1`
- `coverage_score`
- `coverage_error`
- `latency_ms`

新增 LLM 评分维度：

- `gap_decision_quality`
- `missing_info_quality`
- `suggested_query_quality`
- `coverage_assessment_quality`

当前通过条件：

- `gap_detection_accuracy == 1.0`
- `llm_overall_score >= min_llm_overall_score`
- `pass_recommendation == true`

说明：

- Strategy 是最容易被硬匹配误伤的模块之一。
- “缺失信息是否表达等价”“建议查询是否合理”本质上更适合交给 LLM 做评判。

## 7. 端到端流水线评测

### 7.1 PipelineEvaluator

文件：`src/crux/evaluation/evaluators/pipeline.py`

职责：

- 评估完整链路
- 记录完整 trace
- 使用 LLM 评估最终报告与整个轨迹是否合理

### 7.2 TraceablePipelineRunner

职责：

- 实例化各模块节点
- 注入模块 stub
- 按真实流程执行
- 每个阶段记录 trace

执行流程：

1. 初始化 state
2. 执行 `understand`
3. 执行 `retrieve`
4. 执行 `judge`
5. 执行 `analyze`
6. 若 `gap_analysis_result == insufficient`，则回流到 `retrieve`
7. 否则执行 `report`
8. 输出最终 state 和 trace

### 7.3 保留的结构化指标

- `total_latency_ms`
- `iteration_count`
- `trace_stage_count`
- `trace_completeness`
- `final_evidence_recall`
- `report_present`
- `gap_path_accuracy`

### 7.4 新增 LLM 评分维度

- `goal_satisfaction`
- `report_quality`
- `evidence_support`
- `iteration_strategy`
- `trace_coherence`

### 7.5 当前通过条件

- `report_present == true`
- `gap_path_accuracy == 1.0`
- `trace_completeness == 1.0`
- `llm_overall_score >= min_llm_overall_score`
- `pass_recommendation == true`

说明：

- 流水线最终不再只看“最终文档 id 是否命中”。
- 会同时看最终报告是否真正满足需求、证据是否支撑、迭代是否合理、轨迹是否自洽。

## 8. 评测数据格式

评测数据位于：

- `data/evaluation/understanding.json`
- `data/evaluation/retrieval.json`
- `data/evaluation/adjudication.json`
- `data/evaluation/strategy.json`
- `data/evaluation/pipeline.json`

统一格式：

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

字段含义：

- `input`：模块输入或流水线输入
- `expected`：参考答案、阈值和期望路径
- `stubs`：模块执行 stub 与评测裁判 stub
- `metadata`：附加参数，如 `k`、`max_iterations` 等

### 8.1 评测 stub 分类

当前 `stubs` 中可能出现两类字段：

- 模块输出 stub
  - 如 `intent_response`
  - `judgement_batch`
  - `gap_response`

- 评测裁判 stub
  - 如 `understanding_evaluator_judgement`
  - `retrieval_evaluator_judgement`
  - `adjudication_evaluator_judgement`
  - `strategy_evaluator_judgement`
  - `pipeline_evaluator_judgement`

如果没有提供 evaluator judgement stub，则评测器会回退到真实 `LLMClient`。

## 9. CLI 与使用方式

入口：

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

指定数据目录和输出目录：

```bash
python -m src.crux.evaluation.cli \
  --module all \
  --dataset-root data/evaluation \
  --output-dir data/evaluation/reports
```

## 10. 报告输出

每个模块会输出：

- JSON 报告
- Markdown 报告

默认输出目录：

`data/evaluation/reports/`

例如：

- `understanding_report.json`
- `retrieval_report.json`
- `pipeline_report.json`

报告中现在会同时包含：

- 结构化指标
- `llm_overall_score`
- `llm_pass_recommendation`
- 各维度语义分数
- LLM `summary / issues`

## 11. 与现有 Crux 代码的集成点

### 11.1 对节点接口的复用

评测框架直接复用现有节点 `process()` 接口，不要求重构业务模块。

### 11.2 对日志体系的复用

评测框架复用节点输出中的：

- `_stage_logs`
- `_stage_duration_ms`

### 11.3 对 Strategy 模块的增强

为支持评测与轨迹分析，当前已将以下信息写回 state：

- `gap_analysis_details.coverage_score`
- `gap_analysis_details.missing_info`
- `gap_analysis_details.suggested_queries`
- `gap_analysis_details.raw_analysis`

### 11.4 对 LLMClient 的复用

评测体系没有重新造模型调用层，而是直接复用项目已有的 `LLMClient`。

当前支持：

- 在线评测：调用真实评测模型
- 离线评测：通过 `StubLLMClient` 固定裁判输出

### 11.5 对 `call_json_with_object()` 的依赖

语义评测依赖 `LLMClient.call_json_with_object()` 返回结构化对象。
当前该方法已支持：

- mock 场景返回 Pydantic 对象
- fallback 场景返回 Pydantic 对象

## 12. 当前已验证能力

当前样例集已经验证：

- 4 个模块级评测器可独立执行
- 1 个端到端流水线评测可闭环执行
- 流水线 trace 可完整记录多轮迭代
- LLM Judge 评测流可在 stub 模式下离线跑通
- 报告可导出为 Markdown 和 JSON

## 13. 当前局限

当前实现仍有以下边界：

- 样例数据仍偏小，尚未接入大规模真实标注集
- LLM 裁判本身也可能带来模型偏差，需要后续校准 prompt 和评分标准
- 部分结构化指标仍是近似指标，不适合单独代表模块真实质量
- 流水线性能评测尚未细分到 P50/P95、CPU/GPU、外部 API 开销
- 评测结果尚未接入 CI 门禁与长期趋势看板

## 14. 后续演进建议

### 14.1 数据层

- 接入真实标注集
- 扩充正常、边界、异常场景
- 建立模块级标注规范和评测 rubric

### 14.2 评测层

- 继续细化各模块的 judge prompt
- 区分严格评审与宽松评审两套模式
- 增加多裁判投票或裁判一致性分析

### 14.3 工程层

- 接入 GitHub Actions
- 自动产出评测 artifact
- 对关键阈值设置回归门禁

### 14.4 产品化层

- 建立 Dashboard
- 支持跨分支、跨版本、跨模型对比
- 支持历史趋势追踪

## 15. 总结

当前 Crux 评测体系已经从“规则硬匹配主导”升级为“结构化指标 + LLM 语义裁判”的混合架构。

这套架构的价值在于：

- 保留确定性指标的稳定性与可解释性
- 引入语义评测，避免因表述差异造成误判
- 支持模块级与流水线级统一评测
- 支持本地离线回归与在线真实评测两种模式

这意味着后续模块优化可以进入更可靠的闭环：

`评测 -> 分析 -> 优化 -> 回归验证`
