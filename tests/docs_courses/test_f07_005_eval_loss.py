"""Tests for F07-005 — eval_loss / cp_loss from player-normalized scores."""

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
    ply_evaluation_loss,
    stockfish_available,
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


def test_cp_loss_is_non_negative_drop():
    before = PlayerScore(player_color="white", kind="cp", cp=40, mate=None)
    after = PlayerScore(player_color="white", kind="cp", cp=-80, mate=None)
    result = evaluation_loss(before, after)
    assert result.eval_delta == -120
    assert result.eval_loss == 120
    assert result.cp_loss == 120


def test_improvement_has_zero_loss():
    before = PlayerScore(player_color="black", kind="cp", cp=-30, mate=None)
    after = PlayerScore(player_color="black", kind="cp", cp=20, mate=None)
    result = evaluation_loss(before, after)
    assert result.eval_delta == 50
    assert result.eval_loss == 0
    assert result.cp_loss == 0


def test_rejects_mixed_player_colors():
    before = PlayerScore(player_color="white", kind="cp", cp=10, mate=None)
    after = PlayerScore(player_color="black", kind="cp", cp=10, mate=None)
    with pytest.raises(ValueError, match="color mismatch"):
        evaluation_loss(before, after)


def test_nf6_scholar_is_known_error_for_black():
    """3...Nf6 in Scholar's mate hangs f7 — classic known error."""
    path = COURSE_ROOT / "data" / "games" / "f07_002_white.pgn"
    game = import_game_from_file(path)
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    assert nf6.side_to_move == "black"
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
    loss = ply_evaluation_loss(ply_eval)
    assert ply_eval.after.kind == "mate"
    assert ply_eval.after.mate == -1
    assert loss.eval_loss == loss.cp_loss
    assert loss.eval_loss > 10_000


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_stockfish_detects_nf6_error():
    path = COURSE_ROOT / "data" / "games" / "f07_002_white.pgn"
    game = import_game_from_file(path)
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    ply_eval = analyze_ply_for_player(nf6.fen_before, nf6.uci, "black", depth=8)
    loss = ply_evaluation_loss(ply_eval)
    assert loss.eval_loss >= 150
