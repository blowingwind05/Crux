"""CLI entrypoint for Crux evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.crux.evaluation.datasets import load_evaluation_cases
from src.crux.evaluation.evaluators import (
    AdjudicationEvaluator,
    PipelineEvaluator,
    RetrievalEvaluator,
    StrategyEvaluator,
    UnderstandingEvaluator,
)
from src.crux.evaluation.report import write_evaluation_report


EVALUATORS = {
    "understanding": UnderstandingEvaluator,
    "retrieval": RetrievalEvaluator,
    "adjudication": AdjudicationEvaluator,
    "strategy": StrategyEvaluator,
    "pipeline": PipelineEvaluator,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Crux evaluation suites")
    parser.add_argument(
        "--module",
        choices=["all", *EVALUATORS.keys()],
        default="all",
        help="Which evaluator to run",
    )
    parser.add_argument(
        "--dataset-root",
        default="data/evaluation",
        help="Directory containing evaluation JSON files",
    )
    parser.add_argument(
        "--output-dir",
        default="data/evaluation/reports",
        help="Directory to write JSON and Markdown reports",
    )
    args = parser.parse_args()

    dataset_root = Path(args.dataset_root)
    selected = EVALUATORS.keys() if args.module == "all" else [args.module]

    for module in selected:
        cases = load_evaluation_cases(dataset_root / f"{module}.json", module=module)
        summary = EVALUATORS[module]().run(cases)
        write_evaluation_report(summary, args.output_dir)
        print(
            f"[{module}] cases={summary.total_cases} passed={summary.passed_cases} failed={summary.failed_cases}"
        )


if __name__ == "__main__":
    main()
