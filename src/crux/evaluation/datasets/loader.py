"""Utilities to load evaluation cases from JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from src.crux.evaluation.base import EvaluationCase


def load_evaluation_cases(path: str | Path, module: Optional[str] = None) -> List[EvaluationCase]:
    """Load cases from a JSON file or a directory of JSON files."""
    source = Path(path)
    files = [source] if source.is_file() else sorted(source.glob("*.json"))

    cases: List[EvaluationCase] = []
    for file_path in files:
        with open(file_path, "r", encoding="utf-8-sig") as handle:
            raw = json.load(handle)

        raw_cases = raw.get("cases", []) if isinstance(raw, dict) else raw
        for item in raw_cases:
            case = EvaluationCase(
                case_id=item["case_id"],
                module=item["module"],
                name=item.get("name", item["case_id"]),
                input=item.get("input", {}),
                expected=item.get("expected", {}),
                stubs=item.get("stubs", {}),
                metadata=item.get("metadata", {}),
            )
            if module and case.module != module:
                continue
            cases.append(case)

    return cases
