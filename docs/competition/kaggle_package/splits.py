"""Train/test split by game_id for Kaggle export."""

from __future__ import annotations

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


def split_train_test_by_game_id(
    dataset: pd.DataFrame,
    *,
    test_size: float = 0.20,
    random_state: int = 42,
    game_id_column: str = "game_id",
    target_column: str = "error_label",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if dataset.empty:
        empty = dataset.copy()
        return empty, empty

    game_labels = _game_stratify_labels(
        dataset,
        game_id_column=game_id_column,
        target_column=target_column,
    )
    games = game_labels.index.to_numpy()
    labels = game_labels.to_numpy()

    train_games, test_games = train_test_split(
        games,
        test_size=test_size,
        random_state=random_state,
        stratify=labels,
    )

    train_ids = set(train_games)
    test_ids = set(test_games)
    train_df = dataset[dataset[game_id_column].isin(train_ids)].copy()
    test_df = dataset[dataset[game_id_column].isin(test_ids)].copy()
    return train_df.reset_index(drop=True), test_df.reset_index(drop=True)
