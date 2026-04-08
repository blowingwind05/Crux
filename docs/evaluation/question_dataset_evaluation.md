# 基于问题集的评测说明

## 适用范围

该评测流程适用于只有 `question` 列、没有 ground truth 的问题集。

当前数据集场景为：

- 数据文件：`data/evaluation_dataset.xlsx`
- 核心字段：`question`
- 数据特点：没有标准答案，无法进行传统答案比对

因此，当前评测采用 `LLM-as-a-Judge` 的方式进行语义评估。

## 评测思路

整体流程如下：

1. 使用 `pandas` 从 `data/evaluation_dataset.xlsx` 中读取问题
2. 对每个问题运行真实的 Crux pipeline
3. 收集最终报告、证据和执行轨迹
4. 使用 Judge LLM 对结果进行语义评分
5. 输出单模型评测报告和多模型 leaderboard

## 评测内容

当前每条样本主要从以下维度进行评估：

- `query_understanding`：问题理解是否准确
- `evidence_relevance`：证据是否相关
- `answer_completeness`：回答是否完整
- `answer_faithfulness`：回答是否忠于证据
- `answer_clarity`：回答是否清晰
- `trace_coherence`：执行链路是否连贯

Judge 模型会输出：

- `overall_score`
- `pass_recommendation`
- `summary`
- `strengths`
- `issues`
- `dimensions`

## 通过条件

当前默认通过条件为：

- 最终报告存在
- `overall_score >= pass_threshold`
- `pass_recommendation == true`

## 支持的模型类型

当前评测程序支持所有通过 OpenAI-compatible API 暴露的大模型。

评测中有两个角色：

- `candidate model`：被测模型，即 Crux 执行时实际使用的模型
- `judge model`：裁判模型，用于对结果进行语义评分

建议将被测模型和裁判模型分开配置。

## 单模型运行方式

```bash
python -m src.crux.evaluation.cli ^
  --dataset-xlsx data/evaluation_dataset.xlsx ^
  --question-column question ^
  --output-dir data/evaluation/reports ^
  --model-name qwen32b ^
  --model Qwen/Qwen3-32B
```

如果不显式传入模型参数，则默认使用当前 `config.yaml` 中的 LLM 配置。

## 多模型运行方式

先准备一个 JSON 或 YAML 配置文件，然后运行：

```bash
python -m src.crux.evaluation.cli ^
  --dataset-xlsx data/evaluation_dataset.xlsx ^
  --question-column question ^
  --models-config docs/evaluation/models.example.yaml ^
  --output-dir data/evaluation/reports
```

## 输出结果

对于每个候选模型，都会输出：

- `<model>_question_eval.json`
- `<model>_question_eval.md`
- `<model>_question_eval.xlsx`

全局对比输出：

- `question_eval_leaderboard.json`
- `question_eval_leaderboard.md`
- `question_eval_leaderboard.xlsx`

## 当前框架说明

当前 question-only 评测流程的核心结构为：

1. 数据加载层
   - 从 Excel 中读取 `question`

2. 执行层
   - 运行 Crux 全链路
   - 执行顺序为 `understand -> retrieve -> judge -> analyze -> report`

3. 评判层
   - 由 Judge LLM 对结果做语义评分

4. 报告层
   - 汇总 case 结果
   - 输出结构化评测报告

## 当前使用情况

当前已经实现并可运行：

- 基于 Excel 问题集的评测流程
- 对 `question` 列逐条评测
- 候选模型与 Judge 模型分离配置
- 单模型评测报告输出
- 多模型 leaderboard 输出
- 本地 smoke test 验证

当前主流程可以概括为：

`Excel问题集 -> Crux执行 -> Judge语义评估 -> 结构化报告输出`

## 说明

- 当前实现最适合 OpenAI-compatible provider
- 如果某些 provider 不支持 structured output parse，系统会自动退化为 JSON 模式校验
- 如果只想做本地 smoke test，可以设置 `mock_llm=true`，并切换到本地 JSON 数据源
