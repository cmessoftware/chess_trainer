"""Tests for F07-006 — EVALUATION_DROP from eval_loss vs a stable game."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pytest
from chess.engine import Cp, Mate, PovScore

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.engine_eval import (
    PlayerScore,
    analyze_ply_for_player,
    evaluation_loss,
    stockfish_available,
)
from analysis.engine_triggers import (
    DEFAULT_EVALUATION_DROP_CP,
    EVALUATION_DROP,
    evaluation_drop_trigger,
    ply_evaluation_drop,
)
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


def test_threshold_inclusive():
    just_under = evaluation_drop_trigger(DEFAULT_EVALUATION_DROP_CP - 1)
    at_threshold = evaluation_drop_trigger(DEFAULT_EVALUATION_DROP_CP)
    assert just_under.fired is False
    assert at_threshold.fired is True
    assert at_threshold.code == EVALUATION_DROP


def test_loss_object_feeds_trigger():
    before = PlayerScore(player_color="white", kind="cp", cp=40, mate=None)
    after = PlayerScore(player_color="white", kind="cp", cp=-80, mate=None)
    trigger = evaluation_drop_trigger(evaluation_loss(before, after), threshold_cp=100)
    assert trigger.fired is True
    assert trigger.eval_loss == 120


def test_scholar_nf6_fires_evaluation_drop():
    path = COURSE_ROOT / "data" / "games" / "f07_002_white.pgn"
    game = import_game_from_file(path)
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    after = chess.Board(nf6.fen_after)
    engine = ScriptedEngine(
        {
            nf6.fen_before: PovScore(Cp(80), chess.WHITE),
            after.fen(): PovScore(Mate(1), chess.WHITE),
        }
    )
    ply_eval = analyze_ply_for_player(
        nf6.fen_before, nf6.uci, "black", engine=engine, depth=6
    )
    trigger = ply_evaluation_drop(ply_eval)
    assert trigger.fired is True
    assert trigger.code == EVALUATION_DROP
    assert trigger.eval_loss >= DEFAULT_EVALUATION_DROP_CP


def test_ruy_a6_stable_does_not_fire():
    path = COURSE_ROOT / "data" / "games" / "f07_002_black.pgn"
    game = import_game_from_file(path)
    a6 = next(p for p in game.plies if p.san == "a6")
    after = chess.Board(a6.fen_after)
    engine = ScriptedEngine(
        {
            a6.fen_before: PovScore(Cp(18), chess.WHITE),
            after.fen(): PovScore(Cp(25), chess.WHITE),
        }
    )
    ply_eval = analyze_ply_for_player(
        a6.fen_before, a6.uci, "black", engine=engine, depth=6
    )
    trigger = ply_evaluation_drop(ply_eval)
    assert trigger.eval_loss == 7
    assert trigger.fired is False


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_stockfish_blunder_vs_stable():
    scholar = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    nf6 = next(p for p in scholar.plies if p.san == "Nf6")
    blunder = ply_evaluation_drop(
        analyze_ply_for_player(nf6.fen_before, nf6.uci, "black", depth=8)
    )
    ruy = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_black.pgn")
    a6 = next(p for p in ruy.plies if p.san == "a6")
    stable = ply_evaluation_drop(
        analyze_ply_for_player(a6.fen_before, a6.uci, "black", depth=8)
    )
    assert blunder.fired is True
    assert stable.fired is False
    assert blunder.eval_loss > stable.eval_loss
