"""Tests for Module 05 training runner helpers."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository
from experiment_tracking.training_runner import load_encoded_dataset
from tests.docs_courses.test_build_training_dataset import (
    _sample_features,
    _sample_games,
)


def test_load_encoded_dataset_refreshes_stale_parquet(tmp_path: Path) -> None:
    db_path = tmp_path / "course.sqlite"
    parquet_path = tmp_path / "course_training_dataset.parquet"

    repository = CourseFeaturesRepository(db_path)
    repository.replace_course_slice(games=_sample_games(), features=_sample_features())

    stale = pd.DataFrame(
        {
            "move_number": [1, 2],
            "error_label": ["good", "blunder"],
            "material_total": [32.0, 31.0],
        }
    )
    stale.to_parquet(parquet_path, index=False)

    loaded = load_encoded_dataset(parquet_path, db_url=db_path)
    assert "game_id" in loaded.columns
    assert loaded["game_id"].nunique() == 1
    assert list(loaded["error_label"]) == ["good", "blunder"]

    refreshed = pd.read_parquet(parquet_path)
    assert "game_id" in refreshed.columns
