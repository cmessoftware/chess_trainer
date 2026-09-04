"""F07-012 — criticality score and level from active engine triggers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Sequence

from analysis.engine_eval import NormalizedPlyEval, analyze_ply_for_player, open_stockfish
from analysis.engine_triggers import (
    DEFAULT_EVALUATION_DROP_CP,
    EVALUATION_DROP,
    POSITION_TRANSFORMATION,
    ONLY_MOVE,
    EngineTrigger,
    ply_evaluation_drop,
)
from analysis.game_models import PlayerSelection, PlyRecord

CriticalityLevel = Literal["Routine", "Relevant", "Critical", "HighlyCritical"]

# 07-base §7.4 (score 0–10)
ROUTINE_MAX = 2.9
RELEVANT_MIN = 3.0
CRITICAL_MIN = 6.0
HIGHLY_CRITICAL_MIN = 8.5
SCORE_CAP = 10.0


@dataclass(frozen=True)
class CriticalityReason:
    type: str
    weight: float
    description: str


@dataclass(frozen=True)
class PlyCriticality:
    """Criticality for one ply (F07-012)."""

    ply: int
    move_number: int
    san: str
    uci: str
    score: float
    level: CriticalityLevel
    critical: bool
    reasons: tuple[CriticalityReason, ...]
    triggers: tuple[EngineTrigger, ...]


def classify_criticality(score: float) -> CriticalityLevel:
    if score >= HIGHLY_CRITICAL_MIN:
        return "HighlyCritical"
    if score >= CRITICAL_MIN:
        return "Critical"
    if score >= RELEVANT_MIN:
        return "Relevant"
    return "Routine"


def _evaluation_drop_weight(trigger: EngineTrigger) -> float:
    if not trigger.fired:
        return 0.0
    threshold = trigger.threshold_cp or DEFAULT_EVALUATION_DROP_CP
    return min(SCORE_CAP, round(RELEVANT_MIN * trigger.eval_loss / threshold, 1))


def _trigger_weight(trigger: EngineTrigger) -> float:
    if not trigger.fired:
        return 0.0
    if trigger.code == EVALUATION_DROP:
        return _evaluation_drop_weight(trigger)
    if trigger.code == ONLY_MOVE:
        return RELEVANT_MIN
    if trigger.code == POSITION_TRANSFORMATION:
        return RELEVANT_MIN
    return 0.0


def _reason_for(trigger: EngineTrigger, weight: float) -> CriticalityReason | None:
    if not trigger.fired or weight <= 0:
        return None
    if trigger.code == EVALUATION_DROP:
        return CriticalityReason(
            type=EVALUATION_DROP,
            weight=weight,
            description=f"eval_loss {trigger.eval_loss} cp ≥ {trigger.threshold_cp} cp",
        )
    if trigger.code == ONLY_MOVE:
        return CriticalityReason(
            type=ONLY_MOVE,
            weight=weight,
            description=f"only-move gap {trigger.eval_loss} cp ≥ {trigger.threshold_cp} cp",
        )
    if trigger.code == POSITION_TRANSFORMATION:
        return CriticalityReason(
            type=POSITION_TRANSFORMATION,
            weight=weight,
            description=trigger.detail or POSITION_TRANSFORMATION,
        )
    return CriticalityReason(type=trigger.code, weight=weight, description=trigger.code)


def criticality_from_triggers(triggers: Sequence[EngineTrigger]) -> tuple[float, tuple[CriticalityReason, ...]]:
    """Sum weights of fired engine triggers, capped at 10 (minimal 07-base §7.3)."""
    reasons: list[CriticalityReason] = []
    total = 0.0
    for trigger in triggers:
        weight = _trigger_weight(trigger)
        reason = _reason_for(trigger, weight)
        if reason is not None:
            reasons.append(reason)
            total += weight
    return min(SCORE_CAP, round(total, 1)), tuple(reasons)


def assess_ply_criticality(
    record: PlyRecord,
    ply_eval: NormalizedPlyEval,
    *,
    threshold_cp: int = DEFAULT_EVALUATION_DROP_CP,
) -> PlyCriticality:
    triggers = (ply_evaluation_drop(ply_eval, threshold_cp=threshold_cp),)
    score, reasons = criticality_from_triggers(triggers)
    level = classify_criticality(score)
    return PlyCriticality(
        ply=record.ply,
        move_number=record.move_number,
        san=record.san,
        uci=record.uci,
        score=score,
        level=level,
        critical=score >= CRITICAL_MIN,
        reasons=reasons,
        triggers=triggers,
    )


@dataclass(frozen=True)
class RankedCriticality:
    """F07-013 — one row in the top-N ranking."""

    rank: int
    item: PlyCriticality


def rank_critical_positions(
    rows: Sequence[PlyCriticality],
    *,
    top_n: int = 5,
    min_score: float = RELEVANT_MIN,
) -> list[RankedCriticality]:
    """Highest criticality first. Ties break by earlier ply. Routine is excluded by default."""
    if top_n < 1:
        raise ValueError("top_n must be >= 1")
    eligible = [row for row in rows if row.score >= min_score]
    ordered = sorted(eligible, key=lambda row: (-row.score, row.ply))
    return [
        RankedCriticality(rank=index, item=row)
        for index, row in enumerate(ordered[:top_n], start=1)
    ]


def rank_player_game(
    selection: PlayerSelection,
    *,
    engine: Any | None = None,
    depth: int = 12,
    threshold_cp: int = DEFAULT_EVALUATION_DROP_CP,
    top_n: int = 5,
    min_score: float = RELEVANT_MIN,
) -> list[RankedCriticality]:
    """Score all player plies then return top N (F07-012 + F07-013)."""
    rows = score_player_game(
        selection, engine=engine, depth=depth, threshold_cp=threshold_cp
    )
    return rank_critical_positions(rows, top_n=top_n, min_score=min_score)


def score_player_game(
    selection: PlayerSelection,
    *,
    engine: Any | None = None,
    depth: int = 12,
    threshold_cp: int = DEFAULT_EVALUATION_DROP_CP,
) -> list[PlyCriticality]:
    """Score every decision of the analyzed player (F07-012 real-PGN test)."""

    def _run(eng: Any) -> list[PlyCriticality]:
        rows: list[PlyCriticality] = []
        for record in selection.plies:
            ply_eval = analyze_ply_for_player(
                record.fen_before,
                record.uci,
                selection.color,
                engine=eng,
                depth=depth,
            )
            rows.append(
                assess_ply_criticality(record, ply_eval, threshold_cp=threshold_cp)
            )
        return rows

    if engine is not None:
        return _run(engine)
    with open_stockfish() as eng:
        return _run(eng)
