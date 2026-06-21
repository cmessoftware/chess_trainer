"""Pre-export validation for Kaggle CSV files."""

from __future__ import annotations

import pandas as pd

from kaggle_package.config import FORBIDDEN_EXPORT_COLUMNS, TARGET_COLUMN


def assert_no_leakage_columns(frame: pd.DataFrame, *, label: str) -> list[str]:
    forbidden = sorted(FORBIDDEN_EXPORT_COLUMNS.intersection(frame.columns))
    if forbidden:
        raise ValueError(f"{label} contains forbidden columns: {forbidden}")
    return forbidden


def assert_disjoint_game_splits(train: pd.DataFrame, test: pd.DataFrame) -> None:
    if "game_id" not in train.columns or "game_id" not in test.columns:
        return
    overlap = set(train["game_id"]).intersection(set(test["game_id"]))
    if overlap:
        raise ValueError(f"Train/test game_id overlap: {len(overlap)} games")


def build_eda_summary(train: pd.DataFrame) -> dict[str, object]:
    summary: dict[str, object] = {}
    if TARGET_COLUMN in train.columns:
        summary["error_label_distribution"] = (
            train[TARGET_COLUMN].value_counts(normalize=True).round(4).to_dict()
        )
    if "elo_band" in train.columns:
        summary["elo_band_distribution"] = (
            train["elo_band"].value_counts(normalize=True).round(4).to_dict()
        )
    if "time_control_bucket" in train.columns:
        summary["time_control_distribution"] = (
            train["time_control_bucket"].value_counts(normalize=True).round(4).to_dict()
        )
    summary["train_rows"] = int(len(train))
    return summary
