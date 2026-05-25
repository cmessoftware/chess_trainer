from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

COURSE_ROOT = Path(__file__).resolve().parents[1] / "docs" / "courses" / "ai_engineer_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import FeaturesRepository
from dataset.build_training_dataset import (
    TARGET_LABELS,
    build_from_repository,
    build_training_dataset,
)


def _seed_sqlite(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE games (
            game_id TEXT PRIMARY KEY,
            opening TEXT,
            eco TEXT,
            white_elo TEXT,
            black_elo TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE features (
            game_id TEXT,
            move_number INTEGER,
            player_color INTEGER,
            error_label TEXT,
            material_balance REAL,
            material_total REAL,
            num_pieces INTEGER,
            branching_factor INTEGER,
            self_mobility INTEGER,
            opponent_mobility INTEGER,
            phase TEXT,
            has_castling_rights INTEGER,
            move_number_global INTEGER,
            is_repetition INTEGER,
            is_low_mobility INTEGER,
            is_center_controlled INTEGER,
            is_pawn_endgame INTEGER,
            score_diff REAL,
            tags TEXT
        )
        """
    )

    conn.executemany(
        "INSERT INTO games(game_id, opening, eco, white_elo, black_elo) VALUES (?, ?, ?, ?, ?)",
        [
            ("g1", "Sicilian Defense", "B20", "1500", "1480"),
            ("g2", "French Defense", "C00", "1600", "1590"),
        ],
    )

    conn.executemany(
        """
        INSERT INTO features(
            game_id, move_number, player_color, error_label, material_balance,
            material_total, num_pieces, branching_factor, self_mobility,
            opponent_mobility, phase, has_castling_rights, move_number_global,
            is_repetition, is_low_mobility, is_center_controlled, is_pawn_endgame,
            score_diff, tags
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("g1", 1, 1, "good", 0.0, 39, 32, 22, 16, 15, "opening", 1, 1, 0, 0, 1, 0, 5.0, "[]"),
            ("g1", 8, 0, "blunder", -3.0, 30, 18, 35, 8, 19, "middlegame", 0, 16, 0, 1, 0, 0, -240.0, "[]"),
            ("g2", 2, 1, "unknown", 0.5, 38, 30, 18, 14, 13, "opening", 1, 3, 0, 0, 1, 0, -5.0, "[]"),
        ],
    )

    conn.commit()
    conn.close()


def test_features_repository_loads_expected_labels(tmp_path: Path) -> None:
    db_path = tmp_path / "course.db"
    _seed_sqlite(db_path)

    repo = FeaturesRepository(db_url=f"sqlite:///{db_path}")
    df = repo.load_features_for_training(labels=TARGET_LABELS)

    assert not df.empty
    assert set(df["error_label"].str.lower()) == {"good", "blunder"}
    assert "opening" in df.columns
    assert "elo" in df.columns


def test_build_training_dataset_filters_and_encodes(tmp_path: Path) -> None:
    db_path = tmp_path / "course.db"
    _seed_sqlite(db_path)

    output_csv = tmp_path / "training_dataset.csv"
    training_df = build_from_repository(
        db_url=f"sqlite:///{db_path}",
        output_path=output_csv,
        limit=None,
    )

    assert output_csv.exists()
    assert set(training_df["error_label"].unique()) == {"good", "blunder"}
    assert any(col.startswith("opening_") for col in training_df.columns)
    assert any(col.startswith("phase_") for col in training_df.columns)


def test_build_training_dataset_rejects_empty_input() -> None:
    with pytest.raises(ValueError):
        build_training_dataset(pd.DataFrame())
