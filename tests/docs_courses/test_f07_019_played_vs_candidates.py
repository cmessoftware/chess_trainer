"""Tests for F07-019 — played move vs MultiPV candidates."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pytest
from chess.engine import Cp, PovScore

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.comparison import compare_played_to_candidates, describe_consequence
from analysis.engine_eval import stockfish_available
from analysis.position_extractor import import_game_from_file


class ScriptedPlayed:
    def __init__(self, lines: list[dict], independent: dict[str, PovScore] | None = None):
        self.lines = lines
        self.independent = independent or {}
        self.id = {"name": "ScriptedPlayed"}

    def analyse(self, board: chess.Board, limit, multipv=1, root_moves=None):
        if root_moves:
            move = root_moves[0]
            return {"score": self.independent[move.uci()], "pv": [move]}
        count = max(1, int(multipv or 1))
        return self.lines[:count]


def _opening_engine(**independent: PovScore) -> ScriptedPlayed:
    e4 = chess.Move.from_uci("e2e4")
    d4 = chess.Move.from_uci("d2d4")
    nf3 = chess.Move.from_uci("g1f3")
    return ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(40), chess.WHITE), "pv": [e4]},
            {"multipv": 2, "score": PovScore(Cp(32), chess.WHITE), "pv": [d4]},
            {"multipv": 3, "score": PovScore(Cp(28), chess.WHITE), "pv": [nf3]},
        ],
        independent,
    )


def test_played_second_best_has_positive_gap_vs_pv1():
    result = compare_played_to_candidates(
        chess.Board().fen(), "d2d4", engine=_opening_engine(), depth=6
    )
    assert result.in_multipv is True
    assert result.played_is_best is False
    assert result.eval_gap_vs_best_cp == 8
    assert result.best is not None and result.best.move_san == "e4"
    d4 = next(d for d in result.diffs if d.same_move)
    assert d4.eval_gap_cp == 0
    assert d4.purpose_differs is False


def test_played_best_has_zero_gap():
    result = compare_played_to_candidates(
        chess.Board().fen(), "e2e4", engine=_opening_engine(), depth=6
    )
    assert result.played_is_best is True
    assert result.eval_gap_vs_best_cp == 0
    assert all(d.eval_gap_cp <= 0 for d in result.diffs)


def test_scholar_nf6_worse_than_top_candidate():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    board = chess.Board(nf6.fen_before)
    g6 = chess.Move.from_uci("g7g6")
    others = [g6] + [m for m in board.legal_moves if m.uci() not in {nf6.uci, g6.uci()}]
    engine = ScriptedPlayed(
        [
            {
                "multipv": 1,
                "score": PovScore(Cp(-20), chess.WHITE),
                "pv": [others[0], chess.Move.from_uci("h5f3")],
            },
            {"multipv": 2, "score": PovScore(Cp(-30), chess.WHITE), "pv": [others[1]]},
            {"multipv": 3, "score": PovScore(Cp(-40), chess.WHITE), "pv": [others[2]]},
        ],
        {nf6.uci: PovScore(Cp(900), chess.WHITE)},
    )
    result = compare_played_to_candidates(
        nf6.fen_before, nf6.uci, engine=engine, depth=6, player_color="black"
    )
    assert result.played.move_san == "Nf6"
    assert result.in_multipv is False
    assert result.played_is_best is False
    assert result.eval_gap_vs_best_cp >= 150
    assert result.best is not None and result.best.move_san == "g6"
    assert result.diffs[0].consequence.opponent_pv_san == "Qf3"
    assert result.played_consequence.is_mate is False


def test_qxf7_consequence_is_mate_capture():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    last = game.plies[-1]
    cons = describe_consequence(last.fen_before, last.uci, "white")
    assert cons.is_mate is True
    assert cons.is_capture is True
    assert cons.gives_check is True
    assert "MATE" in cons.tags
    assert cons.material_delta_cp == 100


def test_sample_game4_white_ply_compares_without_crash():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "sample_game4.pgn")
    ply = next(p for p in game.plies if p.san == "e4")
    result = compare_played_to_candidates(
        ply.fen_before, ply.uci, engine=_opening_engine(), depth=6, player_color="white"
    )
    assert result.played.move_san == "e4"
    assert len(result.diffs) == 3


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_scholar_nf6_worse_than_best():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    result = compare_played_to_candidates(
        nf6.fen_before, nf6.uci, depth=8, player_color="black"
    )
    assert result.eval_gap_vs_best_cp >= 150
    assert result.played_is_best is False
