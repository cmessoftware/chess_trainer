"""Tests for V3 single-game coaching orchestration."""

from __future__ import annotations

import json
import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.coaching_generate import generate_single_game_coaching
from coaching.critical_move_contract import normalize_critical_move_for_llm
from llm.dry_run_provider import DryRunProvider


def _brief() -> dict:
    moment = normalize_critical_move_for_llm(
        {
            "move_number": 21,
            "move": "21. c4",
            "phase": "middlegame",
            "severity": "blunder",
            "concept": "peón indefenso",
            "lesson": "calcula capturas",
            "context_pgn": "1. e4 e6",
            "tactical_line": "21... Nxe5",
            "root_cause": True,
        }
    )
    return {
        "focus": "single_game_review",
        "language": "es",
        "player": "cmess1315",
        "game": {"opponent": "HaseebNurul", "result_description": "0-1"},
        "critical_moves": [moment],
    }


def test_generate_single_game_coaching_deterministic_only(tmp_path):
    text, warning, meta = generate_single_game_coaching(
        _brief(),
        debug_dir=tmp_path,
        invoke_llm=False,
    )
    assert warning is None
    assert meta["used_deterministic_fallback"] is True
    assert "21. c4" in text
    assert (tmp_path / "prompt_final_sent_to_gemini.txt").exists()
    assert (tmp_path / "critical_moves_payload.json").exists()
    payload = json.loads((tmp_path / "full_llm_payload.json").read_text(encoding="utf-8"))
    assert payload["critical_moves"][0]["player_move"] == "21. c4"
    assert "recurring_themes" not in payload


def test_generate_single_game_coaching_falls_back_on_invalid_llm(tmp_path):
    text, warning, meta = generate_single_game_coaching(
        _brief(),
        debug_dir=tmp_path,
        invoke_llm=True,
        provider=DryRunProvider(),
    )
    assert meta["llm_invoked"] is True
    assert meta["used_deterministic_fallback"] is True
    assert "### Momentos clave" in text
