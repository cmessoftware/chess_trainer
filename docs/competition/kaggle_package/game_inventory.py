"""Load course SQLite games and assign Kaggle elo_band labels."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from kaggle_package.config import COURSE_ROOT, EXCLUDED_SOURCES

if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository  # noqa: E402
from dataset.feature_engineering import (  # noqa: E402
    derive_elo_band,
    derive_time_control_bucket,
    parse_time_control_seconds,
)
from dataset.skill_groups import representative_game_elo  # noqa: E402


def load_human_games(db_url: str | Path | None = None) -> pd.DataFrame:
    repository = CourseFeaturesRepository(db_url)
    games = repository.load_games(
        columns=[
            "game_id",
            "source",
            "white_elo",
            "black_elo",
            "time_control",
            "skill_group",
        ],
        exclude_sources=tuple(EXCLUDED_SOURCES),
    )
    if games.empty:
        return games

    frame = games.copy()
    frame["representative_elo"] = frame.apply(
        lambda row: representative_game_elo(row["white_elo"], row["black_elo"]),
        axis=1,
    )
    frame = frame.dropna(subset=["representative_elo"]).copy()
    frame["elo_band"] = derive_elo_band(frame["representative_elo"]).astype(str)
    frame["time_control_seconds"] = frame["time_control"].map(parse_time_control_seconds)
    frame["time_control_bucket"] = frame["time_control_seconds"].map(derive_time_control_bucket)
    return frame.reset_index(drop=True)


def count_feature_rows(db_url: str | Path | None = None) -> int:
    repository = CourseFeaturesRepository(db_url)
    if not repository.has_table("features"):
        return 0
    return repository.feature_count()
