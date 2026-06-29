"""Tests for V3 critical_moves LLM contract."""

from __future__ import annotations

import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.critical_move_contract import (
    extract_opponent_reply,
    normalize_critical_move_for_llm,
    validate_critical_moves,
)


def _sample_internal_moment() -> dict:
    return {
        "move_number": 21,
        "move": "21. c4",
        "phase": "middlegame",
        "severity": "blunder",
        "concept": "peón indefenso",
        "lesson": "defiende antes de empujar",
        "context_pgn": "1. e4 e6 2. d4 d5",
        "tactical_line": "21... Nxe5 g4",
        "root_cause": True,
        "pattern": "undefended_pawn",
        "consequence": "pierdes material",
        "diagnosis_type": "tactical",
    }


def test_normalize_maps_internal_fields_to_v3():
    normalized = normalize_critical_move_for_llm(_sample_internal_moment())
    assert normalized["player_move"] == "21. c4"
    assert normalized["opponent_reply"] == "21... Nxe5"
    assert normalized["issue"] == "peón indefenso"
    assert normalized["lesson_hint"] == "defiende antes de empujar"
    assert "move" not in normalized
    assert "concept" not in normalized
    assert "lesson" not in normalized
    assert "tactical_line" not in normalized


def test_extract_opponent_reply_from_tactical_line():
    assert extract_opponent_reply("21... Qh4+ Kg1 Qf2#") == "21... Qh4+"
    assert extract_opponent_reply("") is None


def test_validate_critical_moves_accepts_normalized_payload():
    normalized = normalize_critical_move_for_llm(_sample_internal_moment())
    result = validate_critical_moves([normalized])
    assert result.ok
    assert not result.errors


def test_validate_critical_moves_rejects_ambiguous_move_field():
    moment = normalize_critical_move_for_llm(_sample_internal_moment())
    moment["move"] = moment.pop("player_move")
    result = validate_critical_moves([moment], strict=True)
    assert not result.ok
    assert any("ambiguous field 'move'" in error for error in result.errors)
