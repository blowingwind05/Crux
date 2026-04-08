"""JSON and Markdown report generation."""

from __future__ import annotations

import json
from pathlib import Path

from src.crux.evaluation.base import EvaluationSummary


def build_markdown_report(summary: EvaluationSummary) -> str:
    lines = [
        f"# {summary.module} evaluation report",
        "",
        f"- Generated at: `{summary.generated_at}`",
        f"- Total cases: `{summary.total_cases}`",
        f"- Passed: `{summary.passed_cases}`",
        f"- Failed: `{summary.failed_cases}`",
        f"- Average duration: `{summary.average_duration_ms:.2f} ms`",
        "",
        "## Aggregate metrics",
    ]

    if summary.aggregate_metrics:
        for key, value in sorted(summary.aggregate_metrics.items()):
            if isinstance(value, float):
                lines.append(f"- `{key}`: `{value:.4f}`")
            else:
                lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- No aggregate metrics available")

    lines.append("")
    lines.append("## Case results")
    for result in summary.case_results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"- `{result.case_id}` {status} `{result.duration_ms:.2f} ms`")

    return "\n".join(lines)


def write_evaluation_report(summary: EvaluationSummary, output_dir: str | Path) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / f"{summary.module}_report.json"
    md_path = output_path / f"{summary.module}_report.md"

    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(summary.to_dict(), handle, ensure_ascii=False, indent=2)

    with open(md_path, "w", encoding="utf-8") as handle:
        handle.write(build_markdown_report(summary))
