"""SVG board helper for Module 07 notebooks."""

from __future__ import annotations

import sys
from pathlib import Path

import chess

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.board_display import board_svg


def test_board_svg_contains_squares():
    svg = board_svg(chess.Board(), lastmove="e2e4", size=200)
    assert "<svg" in svg
    assert "rect" in svg or "square" in svg.lower()
