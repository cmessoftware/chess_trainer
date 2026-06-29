"""Tests for V6-lite diagnosis styles (no Gemini)."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.critical_move_contract import normalize_critical_move_for_llm
from coaching.diagnosis_builder import DiagnosisBuilder
from coaching.diagnosis_builder.classifier import classify_diagnosis_type
from coaching.deterministic_coaching import render_deterministic_coaching


def _row(**kwargs) -> pd.Series:
    defaults = {
        "move_number": 6,
        "move_san": "Nc3",
        "score_diff": 200.0,
        "phase": "opening",
        "self_mobility": 10.0,
        "opponent_mobility": 12.0,
        "king_safety": 0.0,
        "center_control": 0.0,
        "is_pawn_endgame": 0,
    }
    defaults.update(kwargs)
    return pd.Series(defaults)


def test_classify_opening_without_tactical_tags():
    assert (
        classify_diagnosis_type(
            _row(move_number=6, phase="opening"),
            tags=[],
            primary_pattern="passive_piece",
        )
        == "opening"
    )


def test_classify_endgame_by_phase():
    assert (
        classify_diagnosis_type(
            _row(move_number=40, phase="endgame", move_san="Kb8"),
            tags=[],
            primary_pattern="passive_rook",
        )
        == "endgame"
    )


def test_classify_tactical_when_fork_tag_present():
    assert (
        classify_diagnosis_type(
            _row(move_number=6, phase="opening"),
            tags=["fork"],
            primary_pattern="fork",
            tactical_actionable=True,
        )
        == "tactical"
    )


def test_opening_style_omits_opponent_reply_from_llm_payload():
    builder = DiagnosisBuilder()
    diagnosis = builder.build(
        _row(move_number=6, move_san="Nc3", phase="opening", self_mobility=7, opponent_mobility=14),
        {},
        error_label="mistake",
        sans=None,
        root_ply=0,
        is_white=True,
        opponent_reply="Nd4",
    )
    assert diagnosis.diagnosis_type == "opening"
    assert diagnosis.sections is not None
    assert "desarrollo" in diagnosis.issue.lower() or "apertura" in diagnosis.lesson_hint.lower()
    moment = {
        "move_number": 6,
        "move": "6. Nc3",
        **diagnosis.as_moment_fields(),
        "context_pgn": "pgn",
        "severity": "error claro",
        "phase": "apertura",
    }
    normalized = normalize_critical_move_for_llm(moment)
    assert "opponent_reply" not in normalized
    assert normalized["diagnosis_type"] == "opening"


def test_endgame_style_focuses_on_king():
    builder = DiagnosisBuilder()
    diagnosis = builder.build(
        _row(move_number=57, move_san="Kb8", phase="endgame"),
        {},
        error_label="mistake",
        sans=None,
        root_ply=0,
        is_white=True,
    )
    assert diagnosis.diagnosis_type == "endgame"
    assert "rey" in diagnosis.issue.lower() or "final" in diagnosis.lesson_hint.lower()


def test_deterministic_renderer_uses_v7_lessons_for_opening():
    text = render_deterministic_coaching(
        {"opponent": "rival", "result_description": "0-1", "opening": "French Defense"},
        [
            {
                "player_move": "6. Nc3",
                "move_number": 6,
                "diagnosis_type": "opening",
                "issue": "Desarrollo desequilibrado.",
                "consequence": "El rival igualizó.",
                "lesson_hint": "Prioriza desarrollo.",
                "context_pgn": "pgn",
                "phase": "opening",
                "severity": "mistake",
            },
            {
                "player_move": "21. c4",
                "move_number": 21,
                "diagnosis_type": "tactical",
                "issue": "Peón colgado.",
                "lesson_hint": "Calcula capturas.",
                "context_pgn": "pgn2",
                "phase": "middlegame",
                "severity": "blunder",
            },
        ],
        player="p1",
    )
    assert "### Lecciones principales" in text
    assert "Castigo del rival" not in text
