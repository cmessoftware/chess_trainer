from pathlib import Path
import sys

import pandas as pd
import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from dataset.feature_engineering import (
    DatasetQualityError,
    derive_time_control_bucket,
    encode_training_features,
    parse_time_control_seconds,
    prepare_feature_frame,
    validate_dataset_quality,
)
from dataset.game_splits import split_by_game_id


def _sample_rows() -> pd.DataFrame:
    rows = []
    for game_index in range(3):
        for move_number in (1, 2):
            rows.append(
                {
                    "game_id": f"g{game_index}",
                    "move_number": move_number,
                    "player_color": 1,
                    "white_elo": "1800",
                    "black_elo": "1750",
                    "source": "personal",
                    "time_control": "600+0",
                    "opening": "C20",
                    "material_total": 32.0,
                    "num_pieces": 32,
                    "king_safety": 1,
                    "center_control": 4,
                    "has_castling_rights": 1,
                    "is_pawn_endgame": 0,
                    "score_cp": 20,
                    "mate_in": 0,
                    "depth_score_diff": 0,
                    "error_label": "blunder" if move_number == 2 else "good",
                }
            )
    return pd.DataFrame(rows)


def test_parse_time_control_seconds():
    assert parse_time_control_seconds("600+0") == 600
    assert parse_time_control_seconds("1800+0") == 1800
    assert parse_time_control_seconds("1 day per move") is None
    assert parse_time_control_seconds("-") is None


def test_derive_time_control_bucket():
    assert derive_time_control_bucket(60) == "bullet"
    assert derive_time_control_bucket(300) == "blitz"
    assert derive_time_control_bucket(900) == "rapid"
    assert derive_time_control_bucket(7200) == "classical"


def test_prepare_feature_frame_excludes_stockfish_and_builds_player_elo():
    frame = pd.concat(
        [
            _sample_rows(),
            pd.DataFrame(
                [
                    {
                        "game_id": "stockfish-1",
                        "move_number": 1,
                        "player_color": 1,
                        "white_elo": None,
                        "black_elo": None,
                        "source": "stockfish",
                        "time_control": "600+0",
                        "opening": "A00",
                        "material_total": 32.0,
                        "num_pieces": 32,
                        "king_safety": 1,
                        "center_control": 4,
                        "has_castling_rights": 1,
                        "is_pawn_endgame": 0,
                        "score_cp": 10,
                        "error_label": "good",
                    }
                ]
            ),
        ],
        ignore_index=True,
    )

    prepared = prepare_feature_frame(frame)
    assert "stockfish-1" not in set(prepared["game_id"])
    assert "player_elo" in prepared.columns
    assert "skill_group" in prepared.columns
    assert "export_skill_group" not in prepared.columns
    assert "skill_group_description" in prepared.columns
    assert prepared.loc[0, "skill_group"] == "Advanced Amateur"
    assert prepared.loc[0, "skill_group_description"] == "Advanced Amateur (1600-1999)"
    assert "time_control_bucket" in prepared.columns
    assert prepared.loc[0, "time_control_bucket"] == "rapid"


def test_encode_training_features_drops_reporting_only_columns():
    prepared = prepare_feature_frame(_sample_rows())
    encoded = encode_training_features(prepared)
    assert "source" not in encoded.columns
    assert "elo_band" not in encoded.columns
    assert "skill_group" not in encoded.columns
    assert "skill_group_description" not in encoded.columns
    assert "player_elo" in encoded.columns
    assert any(column.startswith("time_control_bucket_") for column in encoded.columns)


def test_prepare_feature_frame_keeps_export_skill_group_separate_from_player_band():
    frame = pd.DataFrame(
        [
            {
                "game_id": "g1",
                "move_number": 1,
                "player_color": 1,
                "white_elo": "1300",
                "black_elo": "1800",
                "source": "fide",
                "skill_group": "Intermediate",
                "time_control": "600+0",
                "opening": "C20",
                "material_total": 32.0,
                "num_pieces": 32,
                "king_safety": 1,
                "center_control": 4,
                "has_castling_rights": 1,
                "is_pawn_endgame": 0,
                "score_cp": 20,
                "mate_in": 0,
                "depth_score_diff": 0,
                "error_label": "good",
            },
            {
                "game_id": "g1",
                "move_number": 2,
                "player_color": 0,
                "white_elo": "1300",
                "black_elo": "1800",
                "source": "fide",
                "skill_group": "Intermediate",
                "time_control": "600+0",
                "opening": "C20",
                "material_total": 32.0,
                "num_pieces": 32,
                "king_safety": 1,
                "center_control": 4,
                "has_castling_rights": 1,
                "is_pawn_endgame": 0,
                "score_cp": 20,
                "mate_in": 0,
                "depth_score_diff": 0,
                "error_label": "mistake",
            },
        ]
    )
    prepared = prepare_feature_frame(frame)
    assert prepared["export_skill_group"].unique().tolist() == ["Intermediate"]
    assert set(prepared["skill_group"]) == {"Intermediate", "Advanced Amateur"}


def test_validate_dataset_quality_raises_on_bad_label_balance():
    frame = _sample_rows()
    frame["error_label"] = "good"
    prepared = prepare_feature_frame(frame)
    with pytest.raises(DatasetQualityError):
        validate_dataset_quality(prepared, min_rows_for_distribution_checks=10)


def test_validate_dataset_quality_does_not_fail_on_source_or_time_control_drift():
    from dataset.skill_groups import COURSE_SKILL_GROUP_GAME_QUOTAS, COURSE_TARGET_GAME_COUNT

    rows = []
    mini_game_target = 600
    group_elo = {
        "Beginner": "1100",
        "Intermediate": "1300",
        "Advanced Amateur": "1700",
        "Expert": "2100",
        "Master Candidate": "2300",
        "Master+": "2500",
    }
    game_index = 0
    for group, quota in COURSE_SKILL_GROUP_GAME_QUOTAS.items():
        group_games = max(1, round(quota * mini_game_target / COURSE_TARGET_GAME_COUNT))
        for _ in range(group_games):
            rows.append(
                {
                    "game_id": f"g{game_index}",
                    "move_number": 1,
                    "player_color": 1,
                    "white_elo": group_elo[group],
                    "black_elo": group_elo[group],
                    "source": "novice",
                    "skill_group": group,
                    "time_control": "600+0" if game_index % 5 else "180+0",
                    "opening": "C20",
                    "material_total": 32.0,
                    "num_pieces": 32,
                    "king_safety": 1,
                    "center_control": 4,
                    "has_castling_rights": 1,
                    "is_pawn_endgame": 0,
                    "score_cp": 20,
                    "mate_in": 0,
                    "depth_score_diff": 0,
                    "error_label": "good" if game_index % 2 else "blunder",
                }
            )
            game_index += 1

    prepared = prepare_feature_frame(pd.DataFrame(rows))
    report = validate_dataset_quality(prepared, min_rows_for_distribution_checks=100)

    assert report["source_game_distribution"]["novice"] == pytest.approx(1.0)
    assert report["warnings"]
    assert not any("Source" in failure for failure in report["failures"])
    assert not any("Time control" in failure for failure in report["failures"])


def test_validate_dataset_quality_allows_partial_import_with_skewed_shares():
    rows = []
    for game_index in range(2300):
        rows.append(
            {
                "game_id": f"b{game_index}",
                "move_number": 1,
                "player_color": 1,
                "white_elo": "1100",
                "black_elo": "1100",
                "source": "fide",
                "skill_group": "Beginner",
                "time_control": "600+0",
                "opening": "C20",
                "material_total": 32.0,
                "num_pieces": 32,
                "king_safety": 1,
                "center_control": 4,
                "has_castling_rights": 1,
                "is_pawn_endgame": 0,
                "score_cp": 20,
                "mate_in": 0,
                "depth_score_diff": 0,
                "error_label": "good" if game_index % 2 else "blunder",
            }
        )
    for game_index in range(3791):
        rows.append(
            {
                "game_id": f"i{game_index}",
                "move_number": 1,
                "player_color": 1,
                "white_elo": "1300",
                "black_elo": "1300",
                "source": "fide",
                "skill_group": "Intermediate",
                "time_control": "600+0",
                "opening": "C20",
                "material_total": 32.0,
                "num_pieces": 32,
                "king_safety": 1,
                "center_control": 4,
                "has_castling_rights": 1,
                "is_pawn_endgame": 0,
                "score_cp": 20,
                "mate_in": 0,
                "depth_score_diff": 0,
                "error_label": "good" if game_index % 2 else "blunder",
            }
        )

    prepared = prepare_feature_frame(pd.DataFrame(rows))
    report = validate_dataset_quality(prepared, min_rows_for_distribution_checks=100)

    assert report["import_complete"] is False
    assert report["skill_group_game_counts"]["Intermediate"] == 3791
    assert not report["failures"]
    assert any("incomplete" in warning.lower() for warning in report["warnings"])


def test_split_by_game_id_has_no_game_overlap():
    prepared = prepare_feature_frame(_sample_rows())
    train_df, val_df, test_df = split_by_game_id(prepared, test_size=0.34)
    train_games = set(train_df["game_id"])
    val_games = set(val_df["game_id"])
    test_games = set(test_df["game_id"])
    assert not train_games.intersection(val_games)
    assert not train_games.intersection(test_games)
    assert not val_games.intersection(test_games)
