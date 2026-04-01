# Crux 项目评测体系建设汇报

## 1. 项目背景

Crux 是一个基于 LangGraph 构建的 Agentic RAG 框架，核心流程包括：

- Understanding：Schema 感知的意图理解
- Retrieval：意图增强的混合召回
- Adjudication：准则引导的深度研判
- Strategy：信息缺口识别与迭代决策

当前项目已经完成基础框架和核心功能实现，但在评测体系方面仍存在明显短板，导致模块优化和版本迭代缺乏统一基准。

## 2. 当前问题

现阶段主要存在以下问题：

- 缺乏统一的评测框架，不同模块主要依赖零散示例测试
- 缺乏模块级量化指标，难以比较不同版本能力变化
- 缺乏标准化测试数据集，边界场景和异常场景覆盖不足
- 缺乏端到端评测手段，无法完整观察整个 Agent 工作流
- 缺乏执行轨迹采集机制，出现问题时排查成本较高
- 缺乏自动化报告输出，不利于后续接入 CI 和趋势分析

## 3. 建设目标

本轮工作目标是建立一套可复用、可扩展、可回归的评测体系，支撑 Crux 后续的模块优化与版本治理。

具体目标包括：

- 建立统一评测框架
- 支持四个核心模块的独立评测
- 支持完整流水线的端到端评测
- 为流水线评测记录完整执行轨迹
- 统一评测报告格式，支持 Markdown 和 JSON 输出
- 为后续 CI 集成和评测看板预留接口

## 4. 方案概览

本次采用“模块评测 + 流水线评测”的双层评测方案。

### 4.1 模块级评测

分别针对 Understanding、Retrieval、Adjudication、Strategy 构建独立评测器。

评测重点如下：

- Understanding：意图识别准确率、约束抽取质量、Schema 字段合法性
- Retrieval：Recall@K、Precision@K、MRR、NDCG、延迟
- Adjudication：相关性判断准确率、证据质量、通过率
- Strategy：缺口识别准确率、覆盖度、缺失信息识别质量

### 4.2 端到端流水线评测

覆盖完整工作流：

`understand -> retrieve -> judge -> analyze -> ... -> report`

重点不只是看最终结果，而是完整记录每个阶段：

- 输入状态
- 输出结果
- 合并后的全局状态
- 阶段日志
- 阶段耗时
- 迭代路径

## 5. 技术实现

本轮已新增评测模块目录：

```text
src/crux/evaluation/
```

已完成的核心能力包括：

- 通用评测基类 `BaseEvaluator`
- 统一评测数据结构 `EvaluationCase / EvaluationResult / EvaluationSummary`
- 通用指标计算模块
- 数据集加载器
- 内存版检索数据加载器
- Stub 化 LLM 客户端
- 执行轨迹采集器 `TraceRecorder`
- Markdown / JSON 报告生成器
- 命令行入口 `python -m src.crux.evaluation.cli`

## 6. 已完成内容

本轮已完成以下交付：

### 6.1 评测框架

- 已实现统一评测抽象层
- 已支持单模块和多 case 聚合执行
- 已支持统一报告输出

### 6.2 模块评测器

已实现以下评测器：

- `UnderstandingEvaluator`
- `RetrievalEvaluator`
- `AdjudicationEvaluator`
- `StrategyEvaluator`

### 6.3 流水线评测器

已实现：

- `PipelineEvaluator`
- `TraceablePipelineRunner`

支持多轮迭代场景下的轨迹采集与路径校验。

### 6.4 样例评测数据

已补充样例数据集：

- `data/evaluation/understanding.json`
- `data/evaluation/retrieval.json`
- `data/evaluation/adjudication.json`
- `data/evaluation/strategy.json`
- `data/evaluation/pipeline.json`

### 6.5 文档

已输出：

- 技术设计文档
- 评测说明文档

## 7. 本轮实现的关键价值

### 7.1 从“示例测试”升级为“标准评测”

过去更多依赖单点 demo 验证，现在已经能基于统一 case 结构进行标准化评测。

### 7.2 从“结果导向”升级为“过程可观察”

流水线评测支持全阶段轨迹记录，后续不仅能看结果对不对，还能定位在哪一阶段偏离预期。

### 7.3 从“手工检查”升级为“可回归”

评测入口和报告格式已经统一，后续可以稳定接入 CI 或版本对比流程。

### 7.4 能直接服务当前问题定位

以 Understanding 为例，当前已知问题是：

- 改写字段偶尔超出 Schema 字段范围

目前评测器已经把这一点显式纳入检查项，可直接用于验证优化效果。

## 8. 当前验证结果

基于当前样例数据，评测框架已经完成一次端到端验证。

已验证通过：

- 4 个模块级评测
- 1 个端到端流水线评测

流水线样例结果显示：

- `final_evidence_recall = 1.0`
- `gap_path_accuracy = 1.0`
- `trace_completeness = 1.0`
- `trace_stage_count = 8`

说明当前框架已经具备：

- 模块独立评测能力
- 多轮迭代流程评测能力
- 完整轨迹采集能力
- 自动报告导出能力

## 9. 当前不足

虽然框架已经搭建完成，但仍有以下不足：

- 当前数据集仍以样例 fixture 为主，规模较小
- 部分指标仍是近似评估，尚未引入更严格人工标注
- 性能评测尚未细化到 P50、P95、资源占用等层面
- 评测结果尚未接入 GitHub Actions 和长期趋势看板
- 业务模块本身的问题只是“被评测到”，还未全部完成优化

## 10. 下一阶段建议

建议下一阶段分三条线推进。

### 10.1 数据集建设

- 引入真实标注样本
- 扩充正常、边界、异常场景
- 建立统一标注规范

### 10.2 模块优化

优先处理：

- Understanding 的 Schema 字段越界问题
- Retrieval 的融合参数与召回质量
- Adjudication 的阈值与证据质量
- Strategy 的缺口识别稳定性

### 10.3 工程化落地

- 接入 CI 自动评测
- 建立评测结果 Dashboard
- 支持版本对比与趋势分析

## 11. 后续预期产出

若继续推进，预期可形成以下成果：

- 标准化评测数据集
- 模块能力基准报告
- 端到端性能基线报告
- 自动化评测流程
- 评测结果可视化看板
- 一套稳定的“评测-优化-回归”闭环

## 12. 总结

本轮工作已经把 Crux 的评测能力从“零散测试”推进到“结构化评测”阶段。

当前已经具备：

- 统一评测框架
- 模块级评测能力
- 端到端流水线评测能力
- 完整执行轨迹采集能力
- 标准化报告输出能力

这为后续模块优化、版本回归、CI 集成和对外汇报提供了可持续的基础。
