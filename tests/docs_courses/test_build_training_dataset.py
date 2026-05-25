from pathlib import Path
import sys

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "courses"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository
from dataset.build_training_dataset import build_training_dataset



def test_build_training_dataset_filters_and_encodes(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    repository.replace_course_slice(
        games=pd.DataFrame(
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
        ),
        features=pd.DataFrame(
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
                    "tags": {},
                },
                {
                    "game_id": "g1",
                    "move_number": 2,
                    "fen": "fen-2",
                    "elo": 1800,
                    "opening": None,
                    "material_total": 31.0,
                    "num_pieces": 31,
                    "king_safety": 0.6,
                    "center_control": 0.3,
                    "has_castling_rights": False,
                    "is_pawn_endgame": True,
                    "score_cp": -80,
                    "mate_in": 3,
                    "depth_score_diff": None,
                    "error_label": "blunder",
                    "tags": {},
                },
                {
                    "game_id": "g1",
                    "move_number": 3,
                    "fen": "fen-3",
                    "elo": 1800,
                    "opening": "C20",
                    "material_total": 31.0,
                    "num_pieces": 31,
                    "king_safety": 0.6,
                    "center_control": 0.3,
                    "has_castling_rights": False,
                    "is_pawn_endgame": True,
                    "score_cp": -10,
                    "mate_in": None,
                    "depth_score_diff": None,
                    "error_label": "unknown",
                    "tags": {},
                },
            ]
        ),
    )

    dataset = build_training_dataset(db_url=db_path)

    assert list(dataset["error_label"]) == ["good", "blunder"]
    assert dataset["has_castling_rights"].tolist() == [1, 0]
    assert dataset["is_pawn_endgame"].tolist() == [0, 1]
    assert any(column.startswith("opening_") for column in dataset.columns)
    assert "opening_unknown" in dataset.columns
