"""Pre-export validation for Kaggle CSV files."""

from __future__ import annotations

import numpy as np
import pandas as pd

from kaggle_package.config import FORBIDDEN_EXPORT_COLUMNS, RANDOM_STATE, TARGET_COLUMN


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


def build_kaggle_solution_file(
    test_frame: pd.DataFrame,
    *,
    target_column: str = TARGET_COLUMN,
    id_column: str = "id",
    game_id_column: str = "game_id",
    public_fraction: float = 0.5,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Build Kaggle host solution CSV: Usage, row id, label column(s)."""
    required = {id_column, target_column, game_id_column}
    missing = required - set(test_frame.columns)
    if missing:
        raise ValueError(f"test_frame missing columns for solution export: {sorted(missing)}")

    game_ids = test_frame[game_id_column].unique()
    rng = np.random.default_rng(random_state)
    n_public_games = max(1, int(round(len(game_ids) * public_fraction)))
    public_games = set(rng.choice(game_ids, size=n_public_games, replace=False))

    usage = np.where(test_frame[game_id_column].isin(public_games), "Public", "Private")
    return pd.DataFrame(
        {
            "Usage": usage,
            id_column: test_frame[id_column].values,
            target_column: test_frame[target_column].values,
        }
    )
