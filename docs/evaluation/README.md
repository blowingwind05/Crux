# Crux Evaluation

Crux now includes an evaluation framework under `src/crux/evaluation`.

## What it evaluates

- `understanding`: intent parsing quality, constraint extraction quality, schema field compliance
- `retrieval`: retrieval coverage, ranking quality, semantic relevance, latency
- `adjudication`: relevance decision quality, evidence quality, rejection quality
- `strategy`: gap detection quality, missing-info quality, suggested query quality
- `pipeline`: end-to-end execution, iteration path, final report quality, full execution trace

## Evaluation method

The framework now uses a dual-track approach:

- Structural metrics: exact or semi-structured checks such as `Recall@K`, latency, schema field legality, and trace completeness
- LLM judge metrics: semantic scoring produced by `LLMClient` using structured JSON outputs

This is intended to avoid brittle evaluation based only on exact equality or token overlap.

## Run

```bash
python -m src.crux.evaluation.cli --module all
```

Reports are written to `data/evaluation/reports/` by default.

## Offline verification

Sample datasets under `data/evaluation/` include stubbed module outputs and stubbed evaluator judgements, so the framework can be verified locally without calling an external model.

## Live LLM judging

If a case does not provide an evaluator-judgement stub, the evaluator will fall back to the real `LLMClient` configuration from Crux and use the configured model as the semantic judge.

## Pipeline trace

Pipeline evaluation writes a full stage trace per case, including:

- input snapshot before each stage
- stage output snapshot
- merged state after the stage
- stage logs
- stage duration
