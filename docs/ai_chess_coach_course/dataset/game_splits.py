from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


def _game_stratify_labels(
    dataset: pd.DataFrame,
    *,
    game_id_column: str = "game_id",
    target_column: str = "error_label",
) -> pd.Series:
    grouped = dataset.groupby(game_id_column)[target_column]
    return grouped.apply(lambda values: values.mode().iloc[0])


def split_by_game_id(
    dataset: pd.DataFrame,
    *,
    game_id_column: str = "game_id",
    target_column: str = "error_label",
    test_size: float = 0.30,
    val_size_within_holdout: float = 0.50,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if dataset.empty:
        empty = dataset.copy()
        return empty, empty, empty

    if game_id_column not in dataset.columns:
        raise ValueError(f"Missing required column for game split: {game_id_column}")

    game_labels = _game_stratify_labels(
        dataset,
        game_id_column=game_id_column,
        target_column=target_column,
    )
    games = game_labels.index.to_numpy()
    labels = game_labels.to_numpy()

    train_games, holdout_games, _, holdout_labels = train_test_split(
        games,
        labels,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )
    val_games, test_games = train_test_split(
        holdout_games,
        test_size=val_size_within_holdout,
        random_state=random_state,
        stratify=holdout_labels,
    )

    train_ids = set(train_games)
    val_ids = set(val_games)
    test_ids = set(test_games)

    train_df = dataset[dataset[game_id_column].isin(train_ids)].copy()
    val_df = dataset[dataset[game_id_column].isin(val_ids)].copy()
    test_df = dataset[dataset[game_id_column].isin(test_ids)].copy()
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def save_game_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str | Path,
    *,
    stem: str = "course",
) -> dict[str, Path]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    paths = {
        "train": destination / f"{stem}_train.parquet",
        "validation": destination / f"{stem}_validation.parquet",
        "test": destination / f"{stem}_test.parquet",
    }
    train_df.to_parquet(paths["train"], index=False)
    val_df.to_parquet(paths["validation"], index=False)
    test_df.to_parquet(paths["test"], index=False)
    return paths
