"""Tests for verbal game briefs."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.human_brief import (
    build_verbal_game_brief,
    describe_critical_moves,
    verbalize_patterns,
)
from coaching.pattern_engine import PatternObservation


def test_verbalize_patterns_uses_intensity_words():
    observations = [PatternObservation("unsafe_king", 0.9, "high", "")] * 10
    phrases = verbalize_patterns(observations, total_moves=40)
    assert any("a menudo" in phrase for phrase in phrases)
    assert all("%" not in phrase for phrase in phrases)


def test_verbal_brief_has_no_numeric_breakdown():
    brief = build_verbal_game_brief(
        game_summary={
            "opponent": "rival",
            "result": "0-1",
            "opening": "Sicilian",
            "player_moves_analyzed": 30,
        },
        pattern_observations=[PatternObservation("low_mobility", 0.6, "medium", "")],
        sample_labels=pd.Series(["good", "mistake", "blunder"]),
        player_name="cmess1315",
    )
    text = str(brief)
    assert "error_breakdown" not in text
    assert "sample_classes" not in text
    assert brief["game"]["result_description"] == "perdiste"
    assert brief["language"] == "es"


def test_describe_critical_moves_includes_move_notation():
    player_moves = pd.DataFrame(
        {
            "move_number": [21, 51],
            "phase": ["middlegame", "endgame"],
            "move_san": ["c4", "Rd3"],
        }
    )
    labels = pd.Series(["mistake", "blunder"])
    explanations = [
        {
            "predicted_label": "mistake",
            "top_positive_features": [{"feature": "material_total", "impact": 0.1}],
            "top_negative_features": [],
        },
        {
            "predicted_label": "blunder",
            "top_positive_features": [{"feature": "branching_factor", "impact": 0.2}],
            "top_negative_features": [],
        },
    ]
    feature_rows = pd.DataFrame(
        {
            "king_safety": [-1, -1],
            "self_mobility": [8, 7],
            "branching_factor": [12, 30],
            "move_number": [21, 51],
            "has_castling_rights": [1, 1],
            "is_pawn_endgame": [0, 1],
            "material_total": [38, 30],
        }
    )

    moments = describe_critical_moves(
        player_moves,
        labels,
        explanations,
        feature_rows,
        game_rows=player_moves.assign(player_color=1, score_diff=600, error_label="blunder"),
        player_name="cmess1315",
        is_white=True,
    )
    moves = {moment["move"] for moment in moments}
    assert "21. c4" in moves or any("c4" in moment["move"] for moment in moments)
    assert moments[0]["root_cause"] is True
    assert "pattern" in moments[0]
    assert "lesson" in moments[0]


def test_brief_includes_critical_moves_when_data_provided():
    player_moves = pd.DataFrame(
        {
            "game_id": ["g1"],
            "move_number": [10],
            "phase": ["opening"],
            "move_san": ["Nf3"],
            "white_player": ["cmess1315"],
            "black_player": ["rival"],
            "player_color": [1],
            "error_label": ["blunder"],
            "score_diff": [600.0],
        }
    )
    labels = pd.Series(["blunder"])
    explanations = [
        {
            "predicted_label": "blunder",
            "top_positive_features": [{"feature": "king_safety", "impact": 0.2}],
            "top_negative_features": [],
        }
    ]
    feature_rows = pd.DataFrame(
        {
            "king_safety": [-3],
            "self_mobility": [8],
            "branching_factor": [10],
            "move_number": [10],
            "has_castling_rights": [1],
            "is_pawn_endgame": [0],
        }
    )
    brief = build_verbal_game_brief(
        game_summary={"opponent": "rival", "result": "0-1", "player_moves_analyzed": 1, "game_id": "g1"},
        pattern_observations=[],
        sample_labels=labels,
        player_name="cmess1315",
        player_moves=player_moves,
        explanations=explanations,
        feature_rows=feature_rows,
        repo=None,
        game_id="g1",
    )
    assert len(brief["critical_moves"]) == 1
    assert brief["critical_moves"][0]["move"] == "10. Nf3"
    assert brief["critical_moves"][0]["root_cause"] is True
