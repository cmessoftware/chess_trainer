"""Orchestrate human 1600 rapid decision assessment."""

from __future__ import annotations

from typing import Any

import chess

from analysis.mental_model.anti_blunder import run_anti_blunder_checks
from analysis.mental_model.candidate_taxonomy import sort_candidates_by_priority
from analysis.mental_model.critical_triggers import detect_human_triggers
from analysis.mental_model.mapping_07 import map_triggers_to_07
from analysis.mental_model.models import (
    AntiBlunderCheck,
    CandidateCategory,
    DecisionAssessment,
    DecisionMode,
    ThinkingStep,
)

PAUSE_BY_TIME_CONTROL: dict[str, int] = {
    "bullet": 5,
    "blitz": 5,
    "rapid": 10,
    "classical": 30,
}

FAST_PATH_EVAL_DELTA = 40

THINKING_PLAN_CRITICAL: list[ThinkingStep] = [
    ThinkingStep("F", "Detener automatismo — usar pausa sugerida", "critical"),
    ThinkingStep("G1", "¿Qué amenaza realmente la última jugada?", "update"),
    ThinkingStep("G2", "¿Qué cambió respecto al movimiento anterior?", "update"),
    ThinkingStep("G3", "¿Qué quedó atacado o indefenso?", "update"),
    ThinkingStep("G4", "¿Qué líneas se abrieron o cerraron?", "update"),
    ThinkingStep("D", "Generar candidatas: forzantes → amenazas → activas → profilácticas → posicionales", "candidates"),
    ThinkingStep("E", "Reducir a 2–3 candidatas reales", "candidates"),
    ThinkingStep("G", "Calcular: mi jugada → respuesta rival → mi continuación", "calculate"),
    ThinkingStep("I", "Evaluar: rey, material, actividad, estructura, iniciativa práctica", "evaluate"),
    ThinkingStep("J", "Comparar candidatas", "evaluate"),
    ThinkingStep("S", "Chequeo final anti-blunder (S1–S4)", "check"),
]

THINKING_PLAN_FAST: list[ThinkingStep] = [
    ThinkingStep("C", "Modo rápido — buscar jugada natural", "fast"),
    ThinkingStep("C1", "¿Mi jugada natural es segura y coherente?", "fast"),
]


def suggest_pause_seconds(time_control: str = "rapid", player_elo: int = 1600) -> int:
    base = PAUSE_BY_TIME_CONTROL.get(time_control.lower(), 10)
    if player_elo < 1400:
        return max(5, base - 2)
    if player_elo >= 1800:
        return base + 5
    return base


def assess_decision_point(
    *,
    fen: str | None = None,
    board: chess.Board | None = None,
    last_move_uci: str | None = None,
    time_control: str = "rapid",
    player_elo: int = 1600,
    score_diff_before: float | None = None,
    score_diff_after: float | None = None,
    candidate_count: int | None = None,
    top_moves_uci: list[str] | None = None,
) -> DecisionAssessment:
    """
    Assess whether the player should enter critical mode and return a thinking plan.

    Priority: human mental model first; attach engine candidate_count / top_moves when available.
    """
    position = board.copy() if board is not None else chess.Board(fen or chess.STARTING_FEN)
    if last_move_uci and not board:
        move = chess.Move.from_uci(last_move_uci)
        if move in position.legal_moves:
            position.push(move)

    triggers = detect_human_triggers(
        position,
        score_diff_before=score_diff_before,
        score_diff_after=score_diff_after,
        candidate_count=candidate_count,
    )

    eval_delta = None
    if score_diff_before is not None and score_diff_after is not None:
        eval_delta = abs(float(score_diff_after) - float(score_diff_before))

    if triggers or (eval_delta is not None and eval_delta >= FAST_PATH_EVAL_DELTA):
        mode = DecisionMode.CRITICAL
        plan = list(THINKING_PLAN_CRITICAL)
    else:
        mode = DecisionMode.FAST
        plan = list(THINKING_PLAN_FAST)

    categories = list(CandidateCategory)
    anti_checks = list(AntiBlunderCheck)

    meta: dict[str, Any] = {
        "fen": position.fen(),
        "side_to_move": "white" if position.turn == chess.WHITE else "black",
        "legal_moves": position.legal_moves.count(),
    }

    if top_moves_uci:
        moves = [chess.Move.from_uci(u) for u in top_moves_uci if chess.Move.from_uci(u) in position.legal_moves]
        ordered = sort_candidates_by_priority(position, moves)
        meta["ordered_candidates"] = [
            {"uci": m.uci(), "category": cat.value} for m, cat in ordered
        ]

    return DecisionAssessment(
        mode=mode,
        pause_seconds=suggest_pause_seconds(time_control, player_elo),
        triggers=triggers,
        thinking_plan=plan,
        candidate_categories=categories,
        anti_blunder_checks=anti_checks,
        mapped_07_reasons=map_triggers_to_07([t.code for t in triggers]),
        meta=meta,
    )


def assess_move_before_play(
    board: chess.Board,
    move: chess.Move,
    **kwargs: Any,
) -> DecisionAssessment:
    """Run assessment and attach anti-blunder result for a concrete candidate."""
    assessment = assess_decision_point(board=board, **kwargs)
    failed = run_anti_blunder_checks(board, move)
    assessment.meta["anti_blunder_failed"] = [c.value for c in failed]
    assessment.meta["move_uci"] = move.uci()
    assessment.meta["move_safe"] = not failed
    return assessment
