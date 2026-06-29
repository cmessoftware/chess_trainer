"""Tests for V7-lite insight-based coaching (no Gemini)."""

from __future__ import annotations

import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.deterministic_coaching import render_deterministic_coaching
from coaching.lesson_synthesizer import synthesize_lessons
from coaching.prompt_builder import build_single_game_coaching_prompt, prepare_single_game_brief_for_llm


def _critical_moves() -> list[dict]:
    return [
        {
            "move_number": 6,
            "player_move": "6. Nc3",
            "opponent_reply": "6... Nd4",
            "issue": "Desarrollo lento en apertura.",
            "lesson_hint": "Prioriza desarrollo natural.",
            "context_pgn": "pgn6",
            "phase": "opening",
            "severity": "mistake",
            "diagnosis_type": "opening",
            "root_cause": True,
        },
        {
            "move_number": 21,
            "player_move": "21. c4",
            "opponent_reply": "21... Nxe5",
            "issue": "Peón avanzado sin defensa.",
            "lesson_hint": "Verifica defensas antes de empujar.",
            "context_pgn": "pgn21",
            "phase": "middlegame",
            "severity": "blunder",
            "diagnosis_type": "tactical",
            "pattern": "undefended_pawn",
            "root_cause": True,
        },
        {
            "move_number": 34,
            "player_move": "34. b4",
            "issue": "La jugada activó piezas rivales.",
            "lesson_hint": "Pregunta qué pieza enemiga mejora.",
            "context_pgn": "pgn34",
            "phase": "middlegame",
            "severity": "mistake",
            "diagnosis_type": "positional",
            "theme": "enemy_activity",
            "root_cause": True,
        },
    ]


def test_synthesize_lessons_groups_into_two_or_three():
    insight = synthesize_lessons(_critical_moves(), game={"opening": "French Defense"})
    clusters = insight["lesson_clusters"]
    assert 2 <= len(clusters) <= 3
    assert insight["phase_summary"]


def test_prepare_brief_includes_lesson_clusters():
    prepared = prepare_single_game_brief_for_llm(
        {
            "player": "p1",
            "game": {"opponent": "rival", "opening": "French Defense"},
            "critical_moves": _critical_moves(),
        }
    )
    assert "lesson_clusters" in prepared
    assert "phase_summary" in prepared
    assert len(prepared["lesson_clusters"]) >= 2
    assert "recurring_themes" not in prepared


def test_single_game_prompt_requests_v7_sections():
    prompt = build_single_game_coaching_prompt(
        {
            "player": "p1",
            "game": {"opponent": "rival", "opening": "French Defense"},
            "critical_moves": _critical_moves(),
        }
    )
    assert "### Resumen breve" in prompt
    assert "### Lecciones principales" in prompt
    assert "lesson_clusters" in prompt


def test_deterministic_renderer_uses_v7_structure():
    text = render_deterministic_coaching(
        {"opponent": "rival", "result_description": "0-1", "opening": "French Defense"},
        _critical_moves(),
        player="p1",
    )
    assert "### Resumen breve" in text
    assert "### Lecciones principales" in text
    assert "### Momentos clave" in text
    assert "### Plan de entrenamiento" in text
    assert "#### Lección:" in text
