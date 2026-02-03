from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pandas as pd

from .models import AppError

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

UCI_DATASETS: Dict[str, Dict[str, str]] = {
    "iris": {
        "file": "iris.csv",
        "description": "Iris flower measurements",
    },
    "wine": {
        "file": "wine.csv",
        "description": "Wine chemistry and class",
    },
    "auto_mpg": {
        "file": "auto_mpg.csv",
        "description": "Auto MPG dataset",
    },
}


def load_uci_dataset(dataset_id: str) -> pd.DataFrame:
    dataset = UCI_DATASETS.get(dataset_id)
    if not dataset:
        raise AppError("dataset_not_found", f"Unknown dataset_id '{dataset_id}'.")

    file_path = DATA_DIR / dataset["file"]
    if not file_path.exists():
        raise AppError("dataset_missing", f"Dataset file not found for '{dataset_id}'.")

    return pd.read_csv(file_path)


def preview_dataframe(df: pd.DataFrame, sample_count: int = 5) -> Dict[str, Any]:
    preview = df.head(sample_count)
    return {
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "rows": preview.to_dict(orient="records"),
        "row_count": int(len(df)),
        "sample_count": int(len(preview)),
    }
