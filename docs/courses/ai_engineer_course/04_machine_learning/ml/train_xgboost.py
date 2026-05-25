from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_dataset(path: str) -> pd.DataFrame:
    dataset_path = Path(path)
    if dataset_path.suffix == ".csv":
        return pd.read_csv(dataset_path)
    return pd.read_parquet(dataset_path)


def train(dataset_path: str) -> str:
    df = load_dataset(dataset_path)
    if "error_label" not in df.columns:
        raise ValueError("Dataset must contain error_label")
    return "XGBClassifier starter ready ({len(df)} rows loaded)"
