from pathlib import Path
import sys

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from dataset.feature_engineering import (
    encode_training_features,
    prepare_feature_frame,
    resolve_model_feature_columns,
    sanitize_ml_feature_names,
    split_features_and_target,
)


def _prepared_frame() -> pd.DataFrame:
    raw = pd.DataFrame(
        [
            {
                "game_id": "g1",
                "move_number": 10,
                "player_color": 1,
                "white_elo": 1800,
                "black_elo": 1750,
                "source": "personal",
                "time_control": "600+0",
                "opening": "C20",
                "phase": "middlegame",
                "material_total": 30.0,
                "num_pieces": 20,
                "king_safety": 2,
                "center_control": 5,
                "has_castling_rights": 1,
                "is_pawn_endgame": 0,
                "score_cp": 120,
                "score_diff": 120,
                "depth_score_diff": 0,
                "mate_in": 0,
                "error_label": "good",
            },
            {
                "game_id": "g1",
                "move_number": 11,
                "player_color": 1,
                "white_elo": 1800,
                "black_elo": 1750,
                "source": "personal",
                "time_control": "600+0",
                "opening": "C20",
                "phase": "endgame",
                "material_total": 18.0,
                "num_pieces": 8,
                "king_safety": -4,
                "center_control": 1,
                "has_castling_rights": 0,
                "is_pawn_endgame": 1,
                "score_cp": -350,
                "score_diff": -350,
                "depth_score_diff": 0,
                "mate_in": 0,
                "error_label": "blunder",
            },
        ]
    )
    return prepare_feature_frame(raw)


def test_resolve_model_feature_columns_proxy_includes_engine():
    encoded = encode_training_features(_prepared_frame())
    proxy_columns = resolve_model_feature_columns(encoded, feature_set="proxy")
    human_columns = resolve_model_feature_columns(encoded, feature_set="human")

    assert "score_cp" in proxy_columns
    assert "score_cp" not in human_columns
    assert "player_elo" in proxy_columns
    assert "player_elo" in human_columns
    assert any(column.startswith("opening_") for column in proxy_columns)
    assert any(column.startswith("phase_") for column in human_columns)


def test_split_features_and_target_returns_xy():
    encoded = encode_training_features(_prepared_frame())
    feature_columns = resolve_model_feature_columns(encoded, feature_set="human")
    features, target = split_features_and_target(
        encoded,
        feature_columns=feature_columns,
    )

    assert len(features) == 2
    assert list(target) == ["good", "blunder"]
    assert "error_label" not in features.columns


def test_sanitize_ml_feature_names_strips_lightgbm_special_chars():
    frame = pd.DataFrame({"opening_A: B, C": [1], "score_cp": [2]})
    sanitized = sanitize_ml_feature_names(frame)
    assert ":" not in sanitized.columns[0]
    assert "," not in sanitized.columns[0]
