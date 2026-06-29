"""Tests for V5-lite DiagnosisBuilder (no Gemini)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.diagnosis_builder import DiagnosisBuilder
from coaching.diagnosis_builder.feature_interpreter import interpret_features
from coaching.diagnosis_builder.shap_interpreter import interpret_shap
from coaching.diagnosis_builder.tactical_interpreter import interpret_tactical_tags
from coaching.root_cause import analyze_critical_moves


def _row(**kwargs) -> pd.Series:
    defaults = {
        "move_san": "Nf3",
        "score_diff": 400.0,
        "self_mobility": 5.0,
        "opponent_mobility": 16.0,
        "king_safety": 0.0,
        "center_control": -0.8,
        "is_low_mobility": 1,
        "is_center_controlled": 0,
        "phase": "middlegame",
    }
    defaults.update(kwargs)
    return pd.Series(defaults)


def test_tactical_interpreter_fork_with_material():
    result = interpret_tactical_tags(
        ["fork", "piece_lost"],
        move_san="Nf3",
        opponent_reply="Nd4",
    )
    assert result is not None
    assert result.pattern_id == "fork"
    assert result.theme == "Ataque doble"
    assert "ataque doble" in result.issue.lower()
    assert "jaques, capturas y amenazas" not in result.lesson_hint.lower()


def test_feature_interpreter_verbalizes_without_raw_names():
    phrases = interpret_features(_row())
    assert phrases
    assert all("self_mobility" not in phrase for phrase in phrases)
    assert any("movilidad" in phrase or "activ" in phrase for phrase in phrases)


def test_shap_interpreter_never_mentions_shap():
    phrases = interpret_shap(
        {
            "top_positive_features": [{"feature": "king_safety", "impact": 0.12}],
            "top_negative_features": [{"feature": "self_mobility", "impact": -0.08}],
        }
    )
    assert phrases
    assert all("shap" not in phrase.lower() for phrase in phrases)
    assert all("king_safety" not in phrase for phrase in phrases)


def test_diagnosis_builder_prioritizes_tags_over_board():
    builder = DiagnosisBuilder()
    diagnosis = builder.build(
        _row(tags=["pin", "hanging_piece"], move_san="Bg5"),
        {"top_positive_features": [{"feature": "branching_factor", "impact": 0.1}]},
        error_label="blunder",
        sans=None,
        root_ply=0,
        is_white=True,
        opponent_reply="Qxg5",
    )
    assert diagnosis.primary_pattern == "pin"
    assert diagnosis.theme == "Clavada"
    assert diagnosis.supporting_features
    assert "shap" not in " ".join(diagnosis.supporting_features).lower()


def test_analyze_critical_moves_includes_theme_and_supporting_features():
    player_moves = pd.DataFrame(
        [
            {
                "move_number": 12,
                "move_san": "Nf3",
                "error_label": "blunder",
                "score_diff": 500.0,
                "phase": "middlegame",
                "white_player": "Alice",
                "black_player": "Bob",
            }
        ]
    )
    labels = pd.Series(["blunder"])
    explanations = [
        {
            "predicted_label": "blunder",
            "top_positive_features": [{"feature": "branching_factor", "impact": 0.15}],
            "top_negative_features": [],
        }
    ]
    feature_rows = player_moves.copy()
    game_rows = pd.DataFrame(
        [
            {
                "game_id": "g1",
                "move_number": 12,
                "player_color": 1,
                "move_san": "Nf3",
                "error_label": "blunder",
                "score_diff": 500.0,
                "self_mobility": 6,
                "opponent_mobility": 15,
                "king_safety": 0,
                "center_control": 0,
                "branching_factor": 25,
                "tags": ["fork", "piece_lost"],
                "white_player": "Alice",
                "black_player": "Bob",
            }
        ]
    )
    moments = analyze_critical_moves(
        player_moves,
        labels,
        explanations,
        feature_rows,
        game_rows=game_rows,
        player_name="Alice",
        is_white=True,
        max_moments=1,
    )
    moment = moments[0]
    assert moment.get("theme") == "Ataque doble"
    assert moment.get("pattern") == "fork"
    assert moment.get("supporting_features")
