from __future__ import annotations

import os
from pathlib import Path
from typing import Sequence

import pandas as pd

from .features_repository import (
    DEFAULT_DB_ENV_VAR,
    CourseFeaturesRepository,
    resolve_course_db_url,
)


class CourseDataHelper:
    def __init__(self, db_url: os.PathLike[str] | str | None = None) -> None:
        self.repository = CourseFeaturesRepository(db_url)

    @property
    def db_url(self) -> str:
        return self.repository.db_url

    @property
    def sqlite_path(self) -> Path | None:
        return self.repository.sqlite_path

    def feature_count(self) -> int:
        return self.repository.feature_count()

    def game_count(self) -> int:
        return self.repository.game_count()

    def load_features(
        self,
        *,
        columns: Sequence[str] | None = None,
        error_labels: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        return self.repository.load_features(columns=columns, error_labels=error_labels, limit=limit)

    def load_games(
        self,
        *,
        columns: Sequence[str] | None = None,
        player: str | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        return self.repository.load_games(columns=columns, player=player, limit=limit)

    def error_label_distribution(self) -> pd.DataFrame:
        labels = self.load_features(columns=["error_label"])
        if labels.empty:
            return pd.DataFrame(columns=["error_label", "count"])
        return (
            labels.fillna({"error_label": "unknown"})
            .groupby("error_label", dropna=False)
            .size()
            .reset_index(name="count")
            .sort_values(["count", "error_label"], ascending=[False, True])
            .reset_index(drop=True)
        )

    def build_training_dataset(self, output_path: os.PathLike[str] | str | None = None) -> pd.DataFrame:
        from dataset.build_training_dataset import build_training_dataset

        return build_training_dataset(db_url=self.db_url, output_path=output_path)


def get_course_data_helper(db_url: os.PathLike[str] | str | None = None) -> CourseDataHelper:
    return CourseDataHelper(db_url=db_url)


def load_features_dataframe(
    *,
    db_url: os.PathLike[str] | str | None = None,
    columns: Sequence[str] | None = None,
    error_labels: Sequence[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    return CourseDataHelper(db_url).load_features(
        columns=columns,
        error_labels=error_labels,
        limit=limit,
    )


def load_games_dataframe(
    *,
    db_url: os.PathLike[str] | str | None = None,
    columns: Sequence[str] | None = None,
    player: str | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    return CourseDataHelper(db_url).load_games(columns=columns, player=player, limit=limit)


__all__ = [
    "CourseDataHelper",
    "DEFAULT_DB_ENV_VAR",
    "get_course_data_helper",
    "load_features_dataframe",
    "load_games_dataframe",
    "resolve_course_db_url",
]
