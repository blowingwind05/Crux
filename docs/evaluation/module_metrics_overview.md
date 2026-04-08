# Crux 评测模块指标总览

本文梳理 `src/crux/evaluation` 中各评测模块当前代码实际使用的评估指标，包括：

- 结构化指标
- LLM 语义评估维度
- 通过条件
- 适用场景

对应源码位置：

- `src/crux/evaluation/evaluators/understanding.py`
- `src/crux/evaluation/evaluators/retrieval.py`
- `src/crux/evaluation/evaluators/adjudication.py`
- `src/crux/evaluation/evaluators/strategy.py`
- `src/crux/evaluation/evaluators/pipeline.py`
- `src/crux/evaluation/question_eval.py`

---

## 1. 指标体系总说明

当前评测体系采用两类指标：

### 1.1 结构化指标

用于衡量可直接计算的结果，包括：

- 准确率
- Precision / Recall / F1
- Recall@K / Precision@K / MRR / NDCG@K
- 覆盖率
- trace 完整性
- 延迟

这类指标适合做确定性检查和回归分析。

### 1.2 LLM 语义指标

用于衡量语义合理性，由 Judge LLM 输出：

- `llm_overall_score`
- `llm_pass_recommendation`
- `llm_<dimension>_score`

其中 `llm_<dimension>_score` 来自不同模块定义的语义维度。

### 1.3 统一特征

几乎所有模块都会输出：

- 一个或多个结构化指标
- `llm_overall_score`
- `llm_pass_recommendation`
- 若干 `llm_维度_score`
- 延迟指标

---

## 2. UnderstandingEvaluator

源码：

- `src/crux/evaluation/evaluators/understanding.py`

### 2.1 评估目标

评估意图理解模块是否正确解析：

- 用户目标
- 约束条件
- 检索规划
- 研判 rubric

### 2.2 结构化指标

- `intent_accuracy`
  - 用户目标是否命中预期
- `constraint_precision`
- `constraint_recall`
- `constraint_f1`
- `constraint_exact_match`
  - 结构化约束集合是否完全一致
- `sparse_keyword_precision`
- `sparse_keyword_recall`
- `sparse_keyword_f1`
  - 稀疏检索关键词质量
- `dense_query_precision`
- `dense_query_recall`
- `dense_query_f1`
  - 稠密检索查询质量
- `invalid_constraint_field_count`
  - 是否出现 schema 外字段
- `latency_ms`

### 2.3 LLM 语义维度

- `intent_alignment`
- `constraint_semantics`
- `retrieval_plan_quality`
- `rubric_quality`

### 2.4 通过条件

默认通过条件为：

- `llm_overall_score >= min_llm_overall_score`，默认 `0.75`
- `llm_pass_recommendation == true`
- `invalid_constraint_field_count == 0`

### 2.5 适用场景

- 意图理解模块单测
- schema 合法性检查
- retrieval plan 质量分析

---

## 3. RetrievalEvaluator

源码：

- `src/crux/evaluation/evaluators/retrieval.py`

### 3.1 评估目标

评估检索模块是否召回并排序了合适的文档。

### 3.2 结构化指标

- `recall_at_k`
- `precision_at_k`
- `mrr`
- `ndcg_at_k`
- `latency_ms`
- `retrieved_count`

说明：

- `recall_at_k`：相关文档召回率
- `precision_at_k`：Top-K 结果中相关文档比例
- `mrr`：首个相关文档平均倒数排名
- `ndcg_at_k`：排序质量

### 3.3 LLM 语义维度

- `topk_relevance`
- `ranking_quality`
- `coverage_of_need`
- `constraint_alignment`

### 3.4 通过条件

默认通过条件为：

- `llm_overall_score >= min_llm_overall_score`，默认 `0.7`
- `llm_pass_recommendation == true`
- `recall_at_k >= min_recall_at_k`

### 3.5 适用场景

- 检索召回评估
- Top-K 排序评估
- 检索结果语义覆盖分析

---

## 4. AdjudicationEvaluator

源码：

- `src/crux/evaluation/evaluators/adjudication.py`

### 4.1 评估目标

评估研判模块是否正确：

- 接受相关文档
- 拒绝不相关文档
- 抽取有效证据

### 4.2 结构化指标

- `relevance_accuracy`
  - 接受/拒绝决策总体准确率
- `relevance_precision`
- `relevance_recall`
- `relevance_f1`
- `evidence_quality`
  - 证据文本与参考证据的重叠质量
- `acceptance_rate`
  - 候选文档被接受比例
- `latency_ms`

### 4.3 LLM 语义维度

- `relevance_decision_quality`
- `evidence_quality`
- `rejection_quality`
- `rubric_alignment`

说明：

- 这里同时存在一个结构化 `evidence_quality`
- 也存在一个 LLM 维度 `llm_evidence_quality_score`

二者含义不同：

- 前者是基于文本重叠的确定性指标
- 后者是基于语义判断的主观评分

### 4.4 通过条件

默认通过条件为：

- `llm_overall_score >= min_llm_overall_score`，默认 `0.75`
- `llm_pass_recommendation == true`
- `relevance_accuracy >= min_relevance_accuracy`

### 4.5 适用场景

- 证据筛选质量评估
- accept/reject 决策分析
- rubric 对齐分析

---

## 5. StrategyEvaluator

源码：

- `src/crux/evaluation/evaluators/strategy.py`

### 5.1 评估目标

评估 gap analysis 模块是否正确判断：

- 当前证据是否充分
- 缺失了哪些信息
- 是否提出了合理的后续查询

### 5.2 结构化指标

- `gap_detection_accuracy`
  - `sufficient / insufficient` 是否判断正确
- `missing_precision`
- `missing_recall`
- `missing_f1`
  - 缺失信息识别质量
- `coverage_score`
  - 当前覆盖率
- `coverage_error`
  - 与期望覆盖率之间的误差
- `latency_ms`

### 5.3 LLM 语义维度

- `gap_decision_quality`
- `missing_info_quality`
- `suggested_query_quality`
- `coverage_assessment_quality`

### 5.4 通过条件

默认通过条件为：

- `gap_detection_accuracy == 1.0`
- `llm_overall_score >= min_llm_overall_score`，默认 `0.75`
- `llm_pass_recommendation == true`

### 5.5 适用场景

- 多轮检索策略评估
- gap analysis 质量分析
- follow-up query 设计质量评估

---

## 6. PipelineEvaluator

源码：

- `src/crux/evaluation/evaluators/pipeline.py`

### 6.1 评估目标

评估端到端 pipeline 是否整体满足用户目标，包括：

- 最终报告是否生成
- 证据是否足够
- 迭代路径是否正确
- trace 是否完整

### 6.2 结构化指标

- `total_latency_ms`
  - 全链路耗时
- `iteration_count`
  - analyze 阶段出现次数
- `trace_stage_count`
  - trace 中记录的阶段数
- `trace_completeness`
  - trace 输入/输出/时长记录完整度
- `final_evidence_recall`
  - 最终证据对参考证据集合的召回率
- `report_present`
  - 是否生成最终报告
- `gap_path_accuracy`
  - 实际 gap 状态路径是否与预期一致

### 6.3 LLM 语义维度

- `goal_satisfaction`
- `report_quality`
- `evidence_support`
- `iteration_strategy`
- `trace_coherence`

### 6.4 通过条件

默认通过条件为：

- `report_present == true`
- `gap_path_accuracy == 1.0`
- `trace_completeness == 1.0`
- `llm_overall_score >= min_llm_overall_score`，默认 `0.75`
- `llm_pass_recommendation == true`

### 6.5 适用场景

- 端到端整体质量评估
- 迭代链路验证
- trace 可解释性与完整性检查

---

## 7. Question Eval

源码：

- `src/crux/evaluation/question_eval.py`

### 7.1 评估目标

这是当前面向 `evaluation_dataset.xlsx` 的问题集端到端评测流程。

适用特点：

- 数据集只有 `question`
- 没有 ground truth
- 通过 Judge LLM 做整体效果评估

### 7.2 结构化指标

- `total_latency_ms`
  - 单条问题全链路耗时
- `iteration_count`
  - analyze 阶段轮数
- `trace_stage_count`
  - trace 记录的阶段数
- `evidence_count`
  - 最终证据条数
- `unique_evidence_count`
  - 去重后的证据文档数
- `report_present`
  - 是否生成最终报告

### 7.3 LLM 语义维度

- `query_understanding`
- `evidence_relevance`
- `answer_completeness`
- `answer_faithfulness`
- `answer_clarity`
- `trace_coherence`

### 7.4 通过条件

默认通过条件为：

- `report_present == true`
- `llm_overall_score >= pass_threshold`，默认 `0.75`
- `llm_pass_recommendation == true`

### 7.5 适用场景

- Excel 问题集评测
- 无标准答案场景
- 多模型横向对比
- 真实链路质量评估

---

## 8. 各模块指标对比表

| 模块 | 结构化指标重点 | LLM 语义维度重点 | 通过条件重点 |
| --- | --- | --- | --- |
| Understanding | intent、constraint、query 质量 | 意图、约束、检索计划、rubric | LLM分数 + schema字段合法 |
| Retrieval | Recall@K、Precision@K、MRR、NDCG | Top-K 相关性、排序、覆盖 | LLM分数 + Recall@K |
| Adjudication | accept/reject 准确率、证据质量 | 决策质量、证据质量、拒绝质量 | LLM分数 + 决策准确率 |
| Strategy | gap 检测、missing info、coverage | sufficiency 判断、缺口识别、建议查询 | LLM分数 + 状态判断正确 |
| Pipeline | trace、迭代、最终证据、报告 | 目标满足度、报告质量、trace连贯性 | 报告存在 + trace完整 + 路径正确 + LLM分数 |
| Question Eval | 耗时、轮数、证据条数、报告存在 | 理解、证据、完整性、忠实性、清晰度 | 报告存在 + LLM分数 |

---

## 9. 总结

当前 `src/crux/evaluation` 的指标体系呈现出以下特点：

- 模块级评测：保留结构化指标，方便做回归和定位
- 端到端评测：强化 LLM 语义评估，更适合真实问题集
- 所有模块都采用“结构化指标 + LLM Judge”混合模式
- `question_eval` 是当前最贴合 `evaluation_dataset.xlsx` 的主评测流程

如果后续要做 PPT 或汇报，建议把指标分成两类表达：

- 确定性指标：准确率、召回率、trace、延迟
- 语义指标：理解、相关性、完整性、忠实性、报告质量
