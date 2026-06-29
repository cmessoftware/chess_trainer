"""Tests for deterministic coaching fallback renderer."""

from __future__ import annotations

import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.deterministic_coaching import render_deterministic_coaching


def test_render_deterministic_coaching_uses_v3_fields():
    game = {
        "opponent": "HaseebNurul",
        "result_description": "0-1",
        "overall_impression": "Partida tensa en el medio juego.",
    }
    critical_moves = [
        {
            "player_move": "21. c4",
            "opponent_reply": "21... Nxe5",
            "issue": "peón indefenso",
            "consequence": "pierdes peón central",
            "lesson_hint": "calcula capturas",
            "move_number": 21,
            "context_pgn": "pgn",
            "phase": "middlegame",
            "severity": "blunder",
        }
    ]
    text = render_deterministic_coaching(game, critical_moves, player="cmess1315")
    assert "Hola cmess1315" in text
    assert "21. c4" in text
    assert "### Resumen breve" in text
    assert "### Lecciones principales" in text
    assert "### Momentos clave" in text
    assert "### Plan de entrenamiento" in text
