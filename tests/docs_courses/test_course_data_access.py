from pathlib import Path
import sys

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "courses"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository
from notebook_data_helper import CourseDataHelper



def _sample_games() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_id": "g1",
                "pgn": "1. e4 e5",
                "source": "personal",
                "white_player": "cmess1315",
                "black_player": "opponent",
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
                "fen": "fen-1",
                "elo": 1800,
                "opening": "C20",
                "material_total": 32.0,
                "num_pieces": 32,
                "king_safety": 0.8,
                "center_control": 0.4,
                "has_castling_rights": True,
                "is_pawn_endgame": False,
                "score_cp": 20,
                "mate_in": None,
                "depth_score_diff": 0.1,
                "error_label": "good",
                "tags": {"phase": "opening"},
            },
            {
                "game_id": "g1",
                "move_number": 2,
                "fen": "fen-2",
                "elo": 1800,
                "opening": "C20",
                "material_total": 30.0,
                "num_pieces": 30,
                "king_safety": 0.7,
                "center_control": 0.3,
                "has_castling_rights": False,
                "is_pawn_endgame": False,
                "score_cp": -40,
                "mate_in": 0,
                "depth_score_diff": 0.2,
                "error_label": "mistake",
                "tags": {"phase": "middlegame"},
            },
        ]
    )



def test_sqlite_repository_and_helper_load_data(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    repository.replace_course_slice(games=_sample_games(), features=_sample_features())

    helper = CourseDataHelper(db_path)

    assert helper.game_count() == 1
    assert helper.feature_count() == 2

    label_distribution = helper.error_label_distribution()
    assert list(label_distribution["error_label"]) == ["good", "mistake"]
    assert list(label_distribution["count"]) == [1, 1]

    features = helper.load_features(columns=["game_id", "move_number", "error_label"])
    assert list(features.columns) == ["game_id", "move_number", "error_label"]
    assert set(features["error_label"]) == {"good", "mistake"}



def test_repository_filters_games_by_player(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    repository.replace_course_slice(games=_sample_games(), features=_sample_features())

    matching = repository.fetch_games_for_player("cmess1315")
    missing = repository.fetch_games_for_player("someone-else")

    assert len(matching) == 1
    assert missing.empty
