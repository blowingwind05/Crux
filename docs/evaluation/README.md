# Crux Evaluation

Crux now includes a local evaluation framework under `src/crux/evaluation`.

It covers:

- `understanding`: intent parsing quality, constraint extraction quality, schema field compliance
- `retrieval`: `Recall@K`, `Precision@K`, `MRR`, `NDCG@K`, retrieval latency
- `adjudication`: relevance accuracy, evidence quality, acceptance rate
- `strategy`: gap detection accuracy, missing-info overlap, coverage score
- `pipeline`: end-to-end execution, iteration path validation, full execution trace capture

## Run

```bash
python -m src.crux.evaluation.cli --module all
```

Reports are written to `data/evaluation/reports/` by default.

## Dataset format

Each suite is a JSON file under `data/evaluation/`.

- `input`: module input payload
- `expected`: gold labels and pass thresholds
- `stubs`: deterministic LLM outputs for offline evaluation
- `metadata`: evaluator-specific config such as `k`, `max_iterations`, or allowed fields

## Pipeline trace

Pipeline evaluation writes a full stage trace per case, including:

- input snapshot before each stage
- stage output snapshot
- merged state after the stage
- stage logs
- stage duration

This is intended to support the closed-loop workflow of `understand -> retrieve -> judge -> analyze -> ... -> report`.
