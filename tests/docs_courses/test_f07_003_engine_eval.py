"""Tests for F07-003 — Stockfish eval before/after a move."""

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
    analyze_ply,
    configure_asyncio_for_engine,
    parse_engine_score,
    stockfish_available,
)
from analysis.interactive_board import interactive_board_html, legal_dests
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


def test_parse_cp_and_mate_from_white_pov():
    cp = parse_engine_score(PovScore(Cp(35), chess.WHITE))
    assert cp.kind == "cp" and cp.white_cp == 35
    mate = parse_engine_score(PovScore(Mate(2), chess.WHITE))
    assert mate.kind == "mate" and mate.white_mate == 2


def test_analyze_ply_before_and_after_e4():
    start = chess.Board()
    after_e4 = start.copy()
    after_e4.push_uci("e2e4")
    engine = ScriptedEngine(
        {
            start.fen(): PovScore(Cp(18), chess.WHITE),
            after_e4.fen(): PovScore(Cp(42), chess.WHITE),
        }
    )
    result = analyze_ply(start.fen(), "e2e4", engine=engine, depth=8)
    assert result.move_uci == "e2e4"
    assert result.eval_before.white_cp == 18
    assert result.eval_after.white_cp == 42
    assert result.depth == 8


def test_analyze_ply_rejects_illegal_move():
    with pytest.raises(ValueError, match="Illegal"):
        analyze_ply(chess.Board().fen(), "e2e5", engine=ScriptedEngine({}))


def test_scholars_mate_last_ply_is_legal_for_engine_hook():
    path = COURSE_ROOT / "data" / "games" / "f07_002_white.pgn"
    game = import_game_from_file(path)
    last = game.plies[-1]
    assert last.san == "Qxf7#"
    board = chess.Board(last.fen_before)
    assert chess.Move.from_uci(last.uci) in board.legal_moves


def test_legal_dests_starting_position_includes_e4():
    dests = legal_dests(chess.Board())
    assert "e4" in dests["e2"]
    assert "e5" not in dests["e2"]


def test_interactive_html_embeds_mount_and_fen():
    html = interactive_board_html(chess.Board(), lastmove="e2e4", orientation="white")
    assert "mountChessinsightBoard" in html
    assert "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR" in html
    assert "chess.js" in html
    assert "destsFromChess" in html


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_stockfish_mate_in_one_scholar():
    path = COURSE_ROOT / "data" / "games" / "f07_002_white.pgn"
    game = import_game_from_file(path)
    last = game.plies[-1]
    result = analyze_ply(last.fen_before, last.uci, depth=8)
    assert result.eval_after.kind == "mate"
    assert result.eval_after.white_mate is not None
    assert result.eval_after.white_mate >= 0
