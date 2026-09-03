"""Tests for F07-004 — eval from the analyzed player's perspective."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
from chess.engine import Cp, Mate, PovScore

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.engine_eval import (
    EngineScore,
    analyze_ply_for_player,
    normalize_for_player,
    parse_engine_score,
)


def test_white_keeps_white_pov_cp_and_mate():
    cp = EngineScore(kind="cp", white_cp=80, white_mate=None)
    mate = EngineScore(kind="mate", white_cp=None, white_mate=2)
    assert normalize_for_player(cp, "white").cp == 80
    assert normalize_for_player(mate, "white").mate == 2


def test_black_flips_cp_and_mate():
    cp = EngineScore(kind="cp", white_cp=80, white_mate=None)
    mate = EngineScore(kind="mate", white_cp=None, white_mate=2)
    black_cp = normalize_for_player(cp, "black")
    black_mate = normalize_for_player(mate, "black")
    assert black_cp.cp == -80
    assert black_cp.player_color == "black"
    assert black_mate.mate == -2


def test_turn_change_does_not_change_player_pov():
    """Same White-POV score whether it is White or Black to move."""
    after_e4 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
    board = chess.Board(after_e4)
    assert board.turn == chess.BLACK
    parsed = parse_engine_score(PovScore(Cp(40), chess.WHITE))
    assert parsed.white_cp == 40
    assert normalize_for_player(parsed, "white").cp == 40
    assert normalize_for_player(parsed, "black").cp == -40
    assert normalize_for_player(parsed, 1).cp == 40
    assert normalize_for_player(parsed, 0).cp == -40


def test_mate_for_white_is_loss_for_black():
    parsed = parse_engine_score(PovScore(Mate(1), chess.WHITE))
    assert normalize_for_player(parsed, "white").mate == 1
    assert normalize_for_player(parsed, "black").mate == -1


class ScriptedEngine:
    def __init__(self, by_fen: dict[str, PovScore]):
        self.by_fen = by_fen
        self.id = {"name": "Scripted"}

    def analyse(self, board: chess.Board, limit):
        return {"score": self.by_fen[board.fen()]}


def test_analyze_ply_for_player_black_after_e4():
    start = chess.Board()
    after = start.copy()
    after.push_uci("e2e4")
    engine = ScriptedEngine(
        {
            start.fen(): PovScore(Cp(18), chess.WHITE),
            after.fen(): PovScore(Cp(42), chess.WHITE),
        }
    )
    result = analyze_ply_for_player(start.fen(), "e2e4", "black", engine=engine, depth=6)
    assert result.player_color == "black"
    assert result.before.cp == -18
    assert result.after.cp == -42
    assert result.analysis.eval_before.white_cp == 18
