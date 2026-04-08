"""Helpers for loading question-only Excel evaluation datasets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class QuestionDatasetRow:
    """One Excel row used for question-only evaluation."""

    row_id: int
    question: str
    raw: Dict[str, Any]

    @property
    def case_id(self) -> str:
        return f"question_{self.row_id:04d}"


def load_question_dataset(
    path: str | Path,
    question_column: str = "question",
    limit: Optional[int] = None,
) -> List[QuestionDatasetRow]:
    """Load an XLSX file and extract non-empty questions."""
    file_path = Path(path)
    dataframe = pd.read_excel(file_path)

    if question_column not in dataframe.columns:
        raise ValueError(
            f"Question column '{question_column}' not found in {file_path}. "
            f"Available columns: {list(dataframe.columns)}"
        )

    dataframe = dataframe.where(pd.notna(dataframe), None)
    rows: List[QuestionDatasetRow] = []

    for index, payload in enumerate(dataframe.to_dict(orient="records"), start=1):
        question = str(payload.get(question_column, "") or "").strip()
        if not question:
            continue

        rows.append(
            QuestionDatasetRow(
                row_id=index,
                question=question,
                raw=payload,
            )
        )
        if limit is not None and len(rows) >= limit:
            break

    return rows
