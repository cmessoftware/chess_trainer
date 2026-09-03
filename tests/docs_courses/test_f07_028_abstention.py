"""Tests for F07-028 — diagnostic abstention."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
from chess.engine import Cp, PovScore

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.abstention import (
    CANDIDATES_TOO_CLOSE,
    CLEAR_EVAL_GAP,
    EVAL_GAP_AMBIGUOUS,
    INSUFFICIENT_CANDIDATES,
    NO_OBJECTIVE_ERROR,
    assess_diagnosis_abstention,
)
from analysis.comparison import compare_played_to_candidates
from analysis.engine_eval import stockfish_available
from analysis.position_extractor import import_game_from_file
import pytest


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


def _opening_engine() -> ScriptedPlayed:
    return ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(40), chess.WHITE), "pv": [chess.Move.from_uci("e2e4")]},
            {"multipv": 2, "score": PovScore(Cp(32), chess.WHITE), "pv": [chess.Move.from_uci("d2d4")]},
            {"multipv": 3, "score": PovScore(Cp(28), chess.WHITE), "pv": [chess.Move.from_uci("g1f3")]},
        ]
    )


def test_opening_best_move_is_unknown():
    vs = compare_played_to_candidates(
        chess.Board().fen(), "e2e4", engine=_opening_engine(), depth=6
    )
    result = assess_diagnosis_abstention(vs)
    assert result.status == "UNKNOWN"
    assert result.may_diagnose is False
    assert NO_OBJECTIVE_ERROR in result.reasons


def test_opening_close_alternatives_need_review():
    vs = compare_played_to_candidates(
        chess.Board().fen(), "d2d4", engine=_opening_engine(), depth=6
    )
    result = assess_diagnosis_abstention(vs)
    assert result.status == "NEEDS_REVIEW"
    assert result.may_diagnose is False
    assert EVAL_GAP_AMBIGUOUS in result.reasons
    assert CANDIDATES_TOO_CLOSE in result.reasons


def test_single_candidate_is_unknown():
    engine = ScriptedPlayed(
        [{"multipv": 1, "score": PovScore(Cp(20), chess.WHITE), "pv": [chess.Move.from_uci("e2e4")]}]
    )
    vs = compare_played_to_candidates(
        chess.Board().fen(), "e2e4", engine=engine, depth=6, multipv=1
    )
    result = assess_diagnosis_abstention(vs)
    assert result.status == "UNKNOWN"
    assert INSUFFICIENT_CANDIDATES in result.reasons
    assert result.may_diagnose is False


def test_scholar_nf6_allows_later_diagnosis():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    board = chess.Board(nf6.fen_before)
    g6 = chess.Move.from_uci("g7g6")
    others = [g6] + [m for m in board.legal_moves if m.uci() not in {nf6.uci, g6.uci()}]
    engine = ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(-20), chess.WHITE), "pv": [others[0]]},
            {"multipv": 2, "score": PovScore(Cp(-200), chess.WHITE), "pv": [others[1]]},
            {"multipv": 3, "score": PovScore(Cp(-220), chess.WHITE), "pv": [others[2]]},
        ],
        {nf6.uci: PovScore(Cp(900), chess.WHITE)},
    )
    vs = compare_played_to_candidates(
        nf6.fen_before, nf6.uci, engine=engine, depth=6, player_color="black"
    )
    result = assess_diagnosis_abstention(vs)
    assert result.status == "NONE"
    assert result.may_diagnose is True
    assert CLEAR_EVAL_GAP in result.reasons


def test_large_gap_still_allows_diagnosis_if_top_two_are_close():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    board = chess.Board(nf6.fen_before)
    others = [m for m in board.legal_moves if m.uci() != nf6.uci][:3]
    engine = ScriptedPlayed(
        [
            {"multipv": 1, "score": PovScore(Cp(-20), chess.WHITE), "pv": [others[0]]},
            {"multipv": 2, "score": PovScore(Cp(-25), chess.WHITE), "pv": [others[1]]},
            {"multipv": 3, "score": PovScore(Cp(-30), chess.WHITE), "pv": [others[2]]},
        ],
        {nf6.uci: PovScore(Cp(900), chess.WHITE)},
    )
    vs = compare_played_to_candidates(
        nf6.fen_before, nf6.uci, engine=engine, depth=6, player_color="black"
    )
    result = assess_diagnosis_abstention(vs)
    assert result.status == "NONE"
    assert result.may_diagnose is True


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_scholar_nf6_does_not_abstain():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    vs = compare_played_to_candidates(
        nf6.fen_before, nf6.uci, depth=8, player_color="black"
    )
    result = assess_diagnosis_abstention(vs)
    assert result.status == "NONE"
    assert result.may_diagnose is True
