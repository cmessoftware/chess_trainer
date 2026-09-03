"""Tests for human 1600 mental model (Module 7.0-human)."""

from __future__ import annotations

import sys
from pathlib import Path

import chess
import pytest

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from analysis.mental_model.flow import assess_decision_point, assess_move_before_play
from analysis.mental_model.models import DecisionMode, HumanTriggerCode
from analysis.mental_model.mapping_07 import map_triggers_to_07


def test_starting_position_fast_mode():
    result = assess_decision_point(fen=chess.STARTING_FEN, time_control="rapid", player_elo=1600)
    assert result.mode == DecisionMode.FAST
    assert result.pause_seconds == 10
    assert any(step.node_id == "C1" for step in result.thinking_plan)


def test_eval_shift_triggers_critical():
    result = assess_decision_point(
        fen=chess.STARTING_FEN,
        score_diff_before=20,
        score_diff_after=150,
        time_control="rapid",
    )
    assert result.mode == DecisionMode.CRITICAL
    codes = {t.code for t in result.triggers}
    assert HumanTriggerCode.EVAL_SHIFT in codes
    assert "EvaluationInstability" in result.mapped_07_reasons


def test_quiet_opening_is_not_critical():
    """Legal captures exist after 1.e4 c5 2.d4 d6; that must not by itself mean E2."""
    board = chess.Board()
    for san in ("e4", "c5", "d4", "d6"):
        board.push_san(san)
    result = assess_decision_point(board=board)
    assert result.mode == DecisionMode.FAST
    assert not any(t.code == HumanTriggerCode.CHECK_CAPTURE_THREAT for t in result.triggers)


def test_scholar_mate_threat_flags_e2_but_is_not_notable():
    """Qh5 is a threat (E2), not a recapture/structure/exchange moment."""
    board = chess.Board()
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Qh5")
    result = assess_decision_point(board=board)
    assert result.mode == DecisionMode.FAST
    assert any(t.code == HumanTriggerCode.CHECK_CAPTURE_THREAT for t in result.triggers)
    assert result.notable_reasons == []


def test_center_recapture_is_notable():
    """1.e4 e5 2.d4 exd4 — retomar con dama, caballo o gambito."""
    board = chess.Board()
    for san in ("e4", "e5", "d4", "exd4"):
        board.push_san(san)
    result = assess_decision_point(board=board)
    kinds = {r.kind.value for r in result.notable_reasons}
    assert result.mode == DecisionMode.CRITICAL
    assert "recapture_choice" in kinds or "center_decision" in kinds
    assert "pawn_structure" in kinds


def test_map_triggers_to_07_deduplicates():
    reasons = map_triggers_to_07(
        [HumanTriggerCode.FREE_MATERIAL, HumanTriggerCode.CHECK_CAPTURE_THREAT]
    )
    assert "TacticalThreat" in reasons
    assert reasons.count("TacticalThreat") == 1


def test_anti_blunder_meta_on_move():
    board = chess.Board("4k3/8/8/8/8/8/8/4Q2K w - - 0 1")
    move = chess.Move.from_uci("e1a5")
    if move in board.legal_moves:
        assessment = assess_move_before_play(board, move)
        assert "anti_blunder_failed" in assessment.meta
        assert "move_uci" in assessment.meta
