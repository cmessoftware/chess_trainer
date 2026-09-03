"""Tests for F07-015 — played move rank or independent eval."""

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
from analysis.multipv import evaluate_played_move
from analysis.position_extractor import import_game_from_file


class ScriptedPlayed:
    def __init__(self, lines: list[dict], independent: dict[str, PovScore]):
        self.lines = lines
        self.independent = independent
        self.id = {"name": "ScriptedPlayed"}

    def analyse(self, board: chess.Board, limit, multipv=1, root_moves=None):
        if root_moves:
            move = root_moves[0]
            return {"score": self.independent[move.uci()], "pv": [move]}
        count = max(1, int(multipv or 1))
        return self.lines[:count]


def _opening_engine(**independent: PovScore) -> ScriptedPlayed:
    return ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(40), chess.WHITE), "pv": [chess.Move.from_uci("e2e4")]},
            {"multipv": 2, "score": PovScore(Cp(32), chess.WHITE), "pv": [chess.Move.from_uci("d2d4")]},
            {"multipv": 3, "score": PovScore(Cp(28), chess.WHITE), "pv": [chess.Move.from_uci("g1f3")]},
        ],
        independent,
    )


def test_played_move_in_multipv_keeps_rank():
    engine = _opening_engine()
    result = evaluate_played_move(
        chess.Board().fen(), "d2d4", engine=engine, depth=6, multipv=3
    )
    assert result.in_multipv is True
    assert result.multipv_rank == 2
    assert result.source == "multipv"
    assert result.move_san == "d4"
    assert result.player_score.cp == 32


def test_played_move_missing_from_multipv_is_independent():
    engine = _opening_engine(a2a3=PovScore(Cp(4), chess.WHITE))
    result = evaluate_played_move(
        chess.Board().fen(), "a2a3", engine=engine, depth=6, multipv=3
    )
    assert result.in_multipv is False
    assert result.multipv_rank is None
    assert result.source == "independent"
    assert result.move_san == "a3"
    assert result.score.white_cp == 4


def test_rejects_illegal_played_move():
    with pytest.raises(ValueError, match="Illegal"):
        evaluate_played_move(
            chess.Board().fen(), "e2e5", engine=_opening_engine(), depth=4
        )


def test_scholar_nf6_not_in_top3_still_scored():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    board = chess.Board(nf6.fen_before)
    others = [m for m in board.legal_moves if m.uci() != nf6.uci][:3]
    engine = ScriptedPlayed(
        [
            {"multipv": i + 1, "score": PovScore(Cp(-40 - i), chess.WHITE), "pv": [move]}
            for i, move in enumerate(others)
        ],
        {nf6.uci: PovScore(Cp(900), chess.WHITE)},
    )
    result = evaluate_played_move(
        nf6.fen_before, nf6.uci, engine=engine, depth=6, player_color="black"
    )
    assert result.in_multipv is False
    assert result.source == "independent"
    assert result.move_san == "Nf6"
    assert result.player_score.cp == -900


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_qxf7_is_in_or_scored():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    last = game.plies[-1]
    result = evaluate_played_move(last.fen_before, last.uci, depth=8, multipv=3)
    assert result.move_uci == last.uci
    assert result.player_score is not None
    if result.in_multipv:
        assert result.multipv_rank >= 1


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_nf6_scored_even_if_not_top3():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    result = evaluate_played_move(
        nf6.fen_before, nf6.uci, depth=8, multipv=3, player_color="black"
    )
    assert result.move_san == "Nf6"
    assert result.source in {"multipv", "independent"}
    assert result.player_score.kind in {"cp", "mate"}
