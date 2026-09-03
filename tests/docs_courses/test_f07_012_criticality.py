"""Tests for F07-012 — criticality score/level from active triggers."""

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
    CRITICAL_MIN,
    HIGHLY_CRITICAL_MIN,
    RELEVANT_MIN,
    assess_ply_criticality,
    classify_criticality,
    criticality_from_triggers,
    score_player_game,
)
from analysis.engine_eval import analyze_ply_for_player, stockfish_available
from analysis.engine_triggers import EVALUATION_DROP, evaluation_drop_trigger
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


def test_classify_criticality_bands():
    assert classify_criticality(0) == "Routine"
    assert classify_criticality(2.9) == "Routine"
    assert classify_criticality(RELEVANT_MIN) == "Relevant"
    assert classify_criticality(CRITICAL_MIN) == "Critical"
    assert classify_criticality(HIGHLY_CRITICAL_MIN) == "HighlyCritical"


def test_no_triggers_is_routine():
    score, reasons = criticality_from_triggers([])
    assert score == 0.0
    assert reasons == ()
    quiet = evaluation_drop_trigger(20)
    score, reasons = criticality_from_triggers([quiet])
    assert quiet.fired is False
    assert score == 0.0
    assert reasons == ()


def test_evaluation_drop_maps_to_relevant():
    trigger = evaluation_drop_trigger(150)
    score, reasons = criticality_from_triggers([trigger])
    assert score == RELEVANT_MIN
    assert reasons[0].type == EVALUATION_DROP
    assert classify_criticality(score) == "Relevant"


def test_mate_drop_is_highly_critical():
    trigger = evaluation_drop_trigger(50_000)
    score, _reasons = criticality_from_triggers([trigger])
    assert score == 10.0
    assert classify_criticality(score) == "HighlyCritical"


def _scholar_engine(game):
    by_fen: dict[str, PovScore] = {}
    for ply in game.plies:
        by_fen[ply.fen_before] = PovScore(Cp(20), chess.WHITE)
        by_fen[ply.fen_after] = PovScore(Cp(22), chess.WHITE)
    nf6 = next(p for p in game.plies if p.san == "Nf6")
    by_fen[nf6.fen_before] = PovScore(Cp(40), chess.WHITE)
    by_fen[nf6.fen_after] = PovScore(Mate(1), chess.WHITE)
    return ScriptedEngine(by_fen), nf6


def test_scores_all_black_positions_in_scholar():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    engine, nf6 = _scholar_engine(game)
    black = select_analyzed_player(game, color="black")
    rows = score_player_game(black, engine=engine, depth=6)
    assert [row.san for row in rows] == [p.san for p in black.plies]
    assert len(rows) == 3
    by_san = {row.san: row for row in rows}
    assert by_san["e5"].level == "Routine"
    assert by_san["Nc6"].level == "Routine"
    assert by_san["Nf6"].level == "HighlyCritical"
    assert by_san["Nf6"].critical is True
    assert by_san["Nf6"].reasons[0].type == EVALUATION_DROP
    assert by_san["Nf6"].score == max(row.score for row in rows)
    assert by_san["Nf6"].ply == nf6.ply


def test_assess_ply_uses_normalized_eval():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    engine, nf6 = _scholar_engine(game)
    ply_eval = analyze_ply_for_player(
        nf6.fen_before, nf6.uci, "black", engine=engine, depth=6
    )
    result = assess_ply_criticality(nf6, ply_eval)
    assert result.level == "HighlyCritical"
    assert result.san == "Nf6"


@pytest.mark.skipif(not stockfish_available(), reason="Stockfish binary not found")
def test_live_stockfish_scores_all_black_plies():
    game = import_game_from_file(COURSE_ROOT / "data" / "games" / "f07_002_white.pgn")
    black = select_analyzed_player(game, color="black")
    rows = score_player_game(black, depth=8)
    nf6 = next(row for row in rows if row.san == "Nf6")
    assert nf6.score == max(row.score for row in rows)
    assert nf6.critical is True
    assert nf6.level in {"Critical", "HighlyCritical"}
