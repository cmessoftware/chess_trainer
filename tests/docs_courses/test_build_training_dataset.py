from pathlib import Path
import sys

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository
from dataset.build_training_dataset import build_training_dataset


def _sample_games() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_id": "g1",
                "pgn": "",
                "source": "personal",
                "white_player": "cmess1315",
                "black_player": "other",
                "white_elo": "1800",
                "black_elo": "1750",
                "result": "1-0",
                "time_control": "600+0",
                "opening": "C20",
                "eco": "C20",
                "date_played": "2025-01-01",
                "created_at": "2025-01-01T00:00:00",
                "import_batch_id": "batch-1",
                "source_filename": "games.pgn",
                "imported_by": "course-test",
            }
        ]
    )


def _sample_features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_id": "g1",
                "move_number": 1,
                "player_color": 1,
                "fen": "fen-1",
                "error_label": "good",
                "material_total": 32.0,
                "num_pieces": 32,
                "has_castling_rights": True,
                "is_pawn_endgame": False,
                "score_diff": 20,
                "tags": {},
            },
            {
                "game_id": "g1",
                "move_number": 2,
                "player_color": 1,
                "fen": "fen-2",
                "error_label": "blunder",
                "material_total": 31.0,
                "num_pieces": 31,
                "has_castling_rights": False,
                "is_pawn_endgame": True,
                "score_diff": -80,
                "tags": {},
            },
            {
                "game_id": "g1",
                "move_number": 3,
                "player_color": 1,
                "fen": "fen-3",
                "error_label": "unknown",
                "material_total": 31.0,
                "num_pieces": 31,
                "has_castling_rights": False,
                "is_pawn_endgame": True,
                "score_diff": -10,
                "tags": {},
            },
        ]
    )


def test_build_training_dataset_filters_and_encodes(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    repository.replace_course_slice(
        games=_sample_games(),
        features=_sample_features(),
    )

    dataset = build_training_dataset(db_url=db_path, validate_quality=False)

    assert list(dataset["error_label"]) == ["good", "blunder"]
    assert dataset["has_castling_rights"].tolist() == [1, 0]
    assert dataset["is_pawn_endgame"].tolist() == [0, 1]
    assert "player_elo" in dataset.columns
    assert any(column.startswith("opening_") for column in dataset.columns)
    assert any(column.startswith("time_control_bucket_") for column in dataset.columns)


def test_export_excludes_stockfish_games(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    games = _sample_games().copy()
    stockfish_game = pd.DataFrame(
        [
            {
                "game_id": "sf-1",
                "pgn": "",
                "source": "stockfish",
                "white_player": "engine",
                "black_player": "engine",
                "white_elo": None,
                "black_elo": None,
                "result": "1-0",
                "time_control": "600+0",
                "opening": "A00",
                "eco": "A00",
                "date_played": "2025-01-01",
                "created_at": "2025-01-01T00:00:00",
                "import_batch_id": "batch-1",
                "source_filename": "games.pgn",
                "imported_by": "course-test",
            }
        ]
    )
    repository.replace_course_slice(
        games=pd.concat([stockfish_game, games], ignore_index=True),
        features=_sample_features(),
    )

    loaded = repository.load_games(exclude_sources=("stockfish",))
    assert list(loaded["game_id"]) == ["g1"]
