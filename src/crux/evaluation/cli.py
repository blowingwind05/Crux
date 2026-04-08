"""CLI entrypoint for Crux evaluation."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.crux.evaluation.question_eval import ModelSpec, run_question_dataset_evaluation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Crux evaluation suites")

    parser.add_argument(
        "--module",
        choices=["all", "understanding", "retrieval", "adjudication", "strategy", "pipeline"],
        default="all",
        help="Which fixture evaluator to run",
    )
    parser.add_argument(
        "--dataset-root",
        default="data/evaluation",
        help="Directory containing fixture JSON files",
    )
    parser.add_argument(
        "--output-dir",
        default="data/evaluation/reports",
        help="Directory to write reports",
    )

    parser.add_argument(
        "--dataset-xlsx",
        help="Path to an Excel dataset containing a question column",
    )
    parser.add_argument(
        "--question-column",
        default="question",
        help="Question column name in the Excel dataset",
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        help="Only evaluate the first N valid Excel rows",
    )
    parser.add_argument(
        "--models-config",
        help="Optional JSON/YAML file describing judge_model and models[]",
    )
    parser.add_argument("--model-name", default="default", help="Single candidate model label")
    parser.add_argument("--model", help="Single candidate model id")
    parser.add_argument("--base-url", help="Single candidate model OpenAI-compatible base URL")
    parser.add_argument("--api-key", help="Single candidate model API key")
    parser.add_argument("--api-key-env", help="Environment variable containing the candidate API key")

    parser.add_argument("--judge-name", default="judge", help="Judge model label")
    parser.add_argument("--judge-model", help="Judge model id")
    parser.add_argument("--judge-base-url", help="Judge model OpenAI-compatible base URL")
    parser.add_argument("--judge-api-key", help="Judge model API key")
    parser.add_argument("--judge-api-key-env", help="Environment variable containing the judge API key")
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.75,
        help="Minimum LLM-as-a-judge overall score required to pass",
    )

    return parser


def run_fixture_evaluation(args: argparse.Namespace) -> None:
    from src.crux.evaluation.datasets import load_evaluation_cases
    from src.crux.evaluation.evaluators import (
        AdjudicationEvaluator,
        PipelineEvaluator,
        RetrievalEvaluator,
        StrategyEvaluator,
        UnderstandingEvaluator,
    )
    from src.crux.evaluation.report import write_evaluation_report

    evaluators = {
        "understanding": UnderstandingEvaluator,
        "retrieval": RetrievalEvaluator,
        "adjudication": AdjudicationEvaluator,
        "strategy": StrategyEvaluator,
        "pipeline": PipelineEvaluator,
    }

    dataset_root = Path(args.dataset_root)
    selected = evaluators.keys() if args.module == "all" else [args.module]

    for module in selected:
        cases = load_evaluation_cases(dataset_root / f"{module}.json", module=module)
        summary = evaluators[module]().run(cases)
        write_evaluation_report(summary, args.output_dir)
        print(
            f"[{module}] cases={summary.total_cases} passed={summary.passed_cases} failed={summary.failed_cases}"
        )


def run_excel_evaluation(args: argparse.Namespace) -> None:
    default_model = None
    if not args.models_config:
        default_model = ModelSpec(
            name=args.model_name,
            model=args.model,
            base_url=args.base_url,
            api_key=args.api_key,
            api_key_env=args.api_key_env,
        )

    default_judge_model = None
    if any([args.judge_model, args.judge_base_url, args.judge_api_key, args.judge_api_key_env]):
        default_judge_model = ModelSpec(
            name=args.judge_name,
            model=args.judge_model,
            base_url=args.judge_base_url,
            api_key=args.judge_api_key,
            api_key_env=args.judge_api_key_env,
        )

    leaderboard = run_question_dataset_evaluation(
        dataset_xlsx=args.dataset_xlsx,
        output_dir=args.output_dir,
        question_column=args.question_column,
        limit=args.max_cases,
        models_config=args.models_config,
        default_model=default_model,
        default_judge_model=default_judge_model,
        pass_threshold=args.pass_threshold,
    )

    for item in leaderboard:
        print(
            f"[question_eval] model={item['model_name']} "
            f"avg_score={item['avg_llm_overall_score']:.4f} "
            f"pass_rate={item['pass_rate']:.4f} "
            f"cases={item['cases']}"
        )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.dataset_xlsx:
        run_excel_evaluation(args)
        return

    run_fixture_evaluation(args)


if __name__ == "__main__":
    main()
