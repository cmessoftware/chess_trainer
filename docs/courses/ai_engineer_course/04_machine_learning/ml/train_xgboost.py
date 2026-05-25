from __future__ import annotations

from ._dataset_io import load_dataset


def train(dataset_path: str) -> str:
    df = load_dataset(dataset_path)
    if "error_label" not in df.columns:
        raise ValueError("Dataset must contain error_label")
    return f"XGBClassifier starter ready ({len(df)} rows loaded)"
