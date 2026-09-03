"""Tests for F07-007 — ONLY_MOVE from MultiPV or a single legal defense."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pytest
from chess.engine import Cp, PovScore

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.criticality import RELEVANT_MIN, criticality_from_triggers
from analysis.engine_eval import stockfish_available
from analysis.engine_triggers import ONLY_MOVE, only_move_trigger, ply_only_move
from analysis.multipv import analyze_multipv
from analysis.position_extractor import import_game_from_file

# White to move, check on the back rank: only Rxd1.
ONLY_MOVE_FEN = "6k1/5ppp/8/8/8/8/5PPP/R2r2K1 w - - 0 1"


class ScriptedPlayed:
    def __init__(self, lines: list[dict]):
        self.lines = lines
        self.id = {"name": "ScriptedOnlyMove"}

    def analyse(self, board: chess.Board, limit, multipv=1, root_moves=None):
        count = max(1, int(multipv or 1))
        return self.lines[:count]


def _opening_engine() -> ScriptedPlayed:
    return ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(40), chess.WHITE), "pv": [chess.Move.from_uci("e2e4")]},
            {"multipv": 2, "score": PovScore(Cp(32), chess.WHITE), "pv": [chess.Move.from_uci("d2d4")]},
            {"multipv": 3, "score": PovScore(Cp(28), chess.WHITE), "pv": [chess.Move.from_uci("g1f3")]},
        ]
    )


def test_opening_is_not_only_move():
    mpv = analyze_multipv(chess.Board().fen(), engine=_opening_engine(), depth=6)
    trigger = only_move_trigger(mpv)
    assert trigger.fired is False
    assert trigger.code == ONLY_MOVE


def test_wide_gap_is_only_move():
    engine = ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(200), chess.WHITE), "pv": [chess.Move.from_uci("e2e4")]},
            {"multipv": 2, "score": PovScore(Cp(20), chess.WHITE), "pv": [chess.Move.from_uci("d2d4")]},
        ]
    )
    mpv = analyze_multipv(chess.Board().fen(), engine=engine, depth=6, multipv=2)
    trigger = only_move_trigger(mpv, gap_cp=150)
    assert trigger.fired is True
    assert trigger.eval_loss == 180


def test_sole_legal_defense_fires():
    board = chess.Board(ONLY_MOVE_FEN)
    assert board.legal_moves.count() == 1
    engine = ScriptedPlayed(
        [
            {
                "multipv": 1,
                "score": PovScore(Cp(0), chess.WHITE),
                "pv": [next(iter(board.legal_moves))],
            }
        ]
    )
    trigger = ply_only_move(ONLY_MOVE_FEN, engine=engine, depth=6, multipv=3)
    assert trigger.fired is True
    score, reasons = criticality_from_triggers([trigger])
    assert score == RELEVANT_MIN
    assert reasons[0].type == ONLY_MOVE


def test_scholar_nf6_position_is_not_forced_only_move():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    engine = ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(-20), chess.WHITE), "pv": [chess.Move.from_uci("g7g6")]},
            {"multipv": 2, "score": PovScore(Cp(-40), chess.WHITE), "pv": [chess.Move.from_uci("d8e7")]},
            {"multipv": 3, "score": PovScore(Cp(-80), chess.WHITE), "pv": [chess.Move.from_uci("g8f6")]},
        ]
    )
    trigger = ply_only_move(nf6.fen_before, engine=engine, depth=6, player_color="black")
    assert trigger.fired is False


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_back_rank_only_rxd1():
    trigger = ply_only_move(ONLY_MOVE_FEN, depth=8)
    assert trigger.fired is True
    assert trigger.code == ONLY_MOVE
