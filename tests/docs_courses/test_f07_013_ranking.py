"""Tests for F07-013 — top-N ranking of scored plies."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pytest
from chess.engine import Cp, Mate, PovScore

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.criticality import (
    PlyCriticality,
    RELEVANT_MIN,
    rank_critical_positions,
    rank_player_game,
)
from analysis.engine_eval import stockfish_available
from analysis.game_models import select_analyzed_player
from analysis.position_extractor import import_game_from_file


class ScriptedEngine:
    def __init__(self, by_fen: dict[str, PovScore]):
        self.by_fen = by_fen
        self.id = {"name": "Scripted"}

    def analyse(self, board: chess.Board, limit):
        fen = board.fen()
        if fen in self.by_fen:
            return {"score": self.by_fen[fen]}
        key4 = " ".join(fen.split()[:4])
        for stored, score in self.by_fen.items():
            if " ".join(stored.split()[:4]) == key4:
                return {"score": score}
        raise KeyError(fen)


def _scholar_engine(game):
    by_fen: dict[str, PovScore] = {}
    for ply in game.plies:
        by_fen[ply.fen_before] = PovScore(Cp(20), chess.WHITE)
        by_fen[ply.fen_after] = PovScore(Cp(22), chess.WHITE)
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    by_fen[nf6.fen_before] = PovScore(Cp(40), chess.WHITE)
    by_fen[nf6.fen_after] = PovScore(Mate(1), chess.WHITE)
    return ScriptedEngine(by_fen), nf6


def _row(ply: int, san: str, score: float) -> PlyCriticality:
    return PlyCriticality(
        ply=ply,
        move_number=ply // 2 + 1,
        san=san,
        uci="e2e4",
        score=score,
        level="HighlyCritical" if score >= 8.5 else "Relevant" if score >= 3 else "Routine",
        critical=score >= 6,
        reasons=(),
        triggers=(),
    )


def test_rank_orders_by_score_then_ply():
    rows = [_row(4, "a", 3.0), _row(2, "b", 6.0), _row(8, "c", 6.0), _row(0, "d", 0.0)]
    ranked = rank_critical_positions(rows, top_n=5)
    assert [r.item.san for r in ranked] == ["b", "c", "a"]
    assert [r.rank for r in ranked] == [1, 2, 3]
    assert ranked[0].item.ply == 2


def test_top_n_and_min_score():
    rows = [_row(0, "a", 10.0), _row(2, "b", 3.0), _row(4, "c", 2.0)]
    top1 = rank_critical_positions(rows, top_n=1)
    assert [r.item.san for r in top1] == ["a"]
    none = rank_critical_positions(rows, top_n=5, min_score=11.0)
    assert none == []


def test_rejects_invalid_top_n():
    with pytest.raises(ValueError, match="top_n"):
        rank_critical_positions([], top_n=0)


def test_scholar_nf6_is_rank_one_human_review():
    """Known error 3...Nf6 is the only (and thus top) critical ply for Black."""
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    engine, nf6 = _scholar_engine(game)
    black = select_analyzed_player(game, color="black")
    ranked = rank_player_game(black, engine=engine, depth=6, top_n=5)
    assert len(ranked) == 1
    assert ranked[0].rank == 1
    assert ranked[0].item.san == "Nf6"
    assert ranked[0].item.ply == nf6.ply
    assert ranked[0].item.score >= RELEVANT_MIN


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_stockfish_nf6_still_top():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    black = select_analyzed_player(game, color="black")
    ranked = rank_player_game(black, depth=8, top_n=5)
    assert ranked
    assert ranked[0].item.san == "Nf6"
