"""Tests for instructional pattern detection."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.instructional_patterns import detect_instructional_pattern


def test_detects_undefended_pawn_on_pawn_push_and_capture_reply():
    row = pd.Series(
        {
            "move_san": "c4",
            "score_diff": 200.0,
            "branching_factor": 18,
            "self_mobility": 9,
            "king_safety": 0.0,
            "phase": "middlegame",
        }
    )
    pattern = detect_instructional_pattern(
        row,
        {"predicted_label": "mistake"},
        error_label="mistake",
        opponent_reply="Rxe5",
    )
    assert pattern.pattern_name == "undefended_pawn"


def test_king_safety_only_on_strong_evidence():
    row = pd.Series(
        {
            "move_san": "Kh1",
            "score_diff": 600.0,
            "branching_factor": 10,
            "self_mobility": 12,
            "king_safety": -2.0,
            "phase": "middlegame",
        }
    )
    pattern = detect_instructional_pattern(
        row,
        {"predicted_label": "blunder"},
        error_label="blunder",
    )
    assert pattern.pattern_name == "king_safety"
