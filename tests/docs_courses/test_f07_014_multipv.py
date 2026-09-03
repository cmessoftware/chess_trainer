"""Tests for F07-014 — MultiPV candidates with PV and evaluation."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pytest
from chess.engine import Cp, PovScore

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.engine_eval import stockfish_available
from analysis.multipv import analyze_multipv
from analysis.position_extractor import import_game_from_file


class ScriptedMultiPV:
    def __init__(self, lines: list[dict]):
        self.lines = lines
        self.id = {"name": "ScriptedMultiPV"}

    def analyse(self, board: chess.Board, limit, multipv=1):
        count = max(1, int(multipv or 1))
        return self.lines[:count]


def test_scripted_three_opening_candidates():
    start = chess.Board()
    e4 = chess.Move.from_uci("e2e4")
    d4 = chess.Move.from_uci("d2d4")
    nf3 = chess.Move.from_uci("g1f3")
    engine = ScriptedMultiPV(
        [
            {"multipv": 1, "score": PovScore(Cp(40), chess.WHITE), "pv": [e4]},
            {"multipv": 2, "score": PovScore(Cp(32), chess.WHITE), "pv": [d4]},
            {"multipv": 3, "score": PovScore(Cp(28), chess.WHITE), "pv": [nf3]},
        ]
    )
    result = analyze_multipv(start.fen(), engine=engine, depth=6, multipv=3)
    assert len(result.lines) == 3
    assert [line.move_san for line in result.lines] == ["e4", "d4", "Nf3"]
    assert [line.move_uci for line in result.lines] == ["e2e4", "d2d4", "g1f3"]
    assert result.lines[0].player_score.cp == 40
    assert result.player_color == "white"
    for line in result.lines:
        assert chess.Move.from_uci(line.move_uci) in start.legal_moves


def test_black_pov_flips_score():
    board = chess.Board()
    board.push_san("e4")
    engine = ScriptedMultiPV(
        [
            {
                "multipv": 1,
                "score": PovScore(Cp(30), chess.WHITE),
                "pv": [chess.Move.from_uci("e7e5")],
            }
        ]
    )
    result = analyze_multipv(board.fen(), engine=engine, depth=6, player_color="black")
    assert result.player_color == "black"
    assert result.lines[0].move_san == "e5"
    assert result.lines[0].player_score.cp == -30


def test_drops_illegal_pv_first_move():
    start = chess.Board()
    engine = ScriptedMultiPV(
        [
            {
                "multipv": 1,
                "score": PovScore(Cp(0), chess.WHITE),
                "pv": [chess.Move.from_uci("e2e5")],
            }
        ]
    )
    result = analyze_multipv(start.fen(), engine=engine, depth=4)
    assert result.lines == ()


def test_scholar_critical_fen_has_legal_candidates():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    board = chess.Board(nf6.fen_before)
    legal = list(board.legal_moves)
    engine = ScriptedMultiPV(
        [
            {"multipv": 1, "score": PovScore(Cp(-80), chess.WHITE), "pv": [legal[0]]},
            {"multipv": 2, "score": PovScore(Cp(-90), chess.WHITE), "pv": [legal[1]]},
            {"multipv": 3, "score": PovScore(Cp(-100), chess.WHITE), "pv": [legal[2]]},
        ]
    )
    result = analyze_multipv(nf6.fen_before, engine=engine, depth=6, player_color="black")
    assert len(result.lines) == 3
    for line in result.lines:
        assert chess.Move.from_uci(line.move_uci) in board.legal_moves
        assert line.pv_san[0] == line.move_san


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_stockfish_three_legal_from_start():
    result = analyze_multipv(chess.Board().fen(), depth=8, multipv=3)
    assert 1 <= len(result.lines) <= 3
    board = chess.Board()
    first_moves = [line.move_uci for line in result.lines]
    assert len(set(first_moves)) == len(first_moves)
    for line in result.lines:
        assert chess.Move.from_uci(line.move_uci) in board.legal_moves


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_scholar_mate_includes_qxf7():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    last = game.plies[-1]
    assert last.san == "Qxf7#"
    result = analyze_multipv(last.fen_before, depth=8, multipv=3)
    assert result.lines
    ucis = {line.move_uci for line in result.lines}
    sans = {line.move_san.replace("+", "").replace("#", "") for line in result.lines}
    assert last.uci in ucis or "Qxf7" in sans
