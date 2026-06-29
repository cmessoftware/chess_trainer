"""Tests for PGN window extraction."""

from __future__ import annotations

import sys
from pathlib import Path

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from coaching.pgn_context import (
    enrich_critical_moves_with_pgn,
    extract_pgn_window_for_player_move,
    extract_tactical_line,
    format_player_move_label,
    format_san_window,
    parse_pgn_sans,
    player_ply_index,
)

SAMPLE_PGN = """[Event "Test"]
[White "Alice"]
[Black "Bob"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. d4 exd4 7. Nxd4 O-O
8. Nc3 d5 9. exd5 Nxd5 10. Nxd5 Qxd5 11. Re1 *
"""

COACHING_SANS = ["dummy"] * 40 + ["c4", "Rxe5", "Bd4"]


def test_player_ply_index_for_black():
    assert player_ply_index(1, is_white=False) == 1
    assert player_ply_index(10, is_white=False) == 19


def test_extract_pgn_window_for_black_move():
    window = extract_pgn_window_for_player_move(
        SAMPLE_PGN,
        move_number=10,
        is_white=False,
        plies_before=2,
        plies_after=2,
    )
    assert "Qxd5" in window or "10..." in window


def test_extract_tactical_line_returns_opponent_replies():
    line = extract_tactical_line(COACHING_SANS, player_ply_index(21, is_white=True), plies_ahead=1)
    assert line is not None
    assert "Rxe5" in line


def test_format_player_move_label_uses_pgn_not_fallback():
    label = format_player_move_label(
        21,
        sans=COACHING_SANS,
        is_white=True,
        fallback_san="Rxe5",
    )
    assert label == "21. c4"
    sans = parse_pgn_sans(SAMPLE_PGN)
    line = extract_tactical_line(sans, player_ply_index(10, is_white=False), plies_ahead=2)
    assert line is not None
    assert "..." in line or "." in line


def test_enrich_critical_moves_adds_context_pgn():
    moves = [
        {
            "move_number": 5,
            "move": "5. O-O",
            "severity": "error claro",
        }
    ]
    enriched = enrich_critical_moves_with_pgn(
        moves,
        pgn_text=SAMPLE_PGN,
        is_white=True,
        plies_before=2,
        plies_after=2,
    )
    assert "context_pgn" in enriched[0]
    assert "O-O" in enriched[0]["context_pgn"]


def test_format_san_window_handles_start_of_game():
    sans = parse_pgn_sans(SAMPLE_PGN)
    window = format_san_window(sans, center_ply=0, plies_before=2, plies_after=2)
    assert window.startswith("1. e4")
