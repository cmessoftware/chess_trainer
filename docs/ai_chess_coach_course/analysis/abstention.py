"""F07-028 — abstain from chess diagnosis when evidence is thin or ambiguous."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from analysis.comparison import PlayedVsCandidates
from analysis.engine_triggers import DEFAULT_EVALUATION_DROP_CP

AbstentionStatus = Literal["NONE", "UNKNOWN", "NEEDS_REVIEW"]

CLEAR_EVAL_GAP_CP = DEFAULT_EVALUATION_DROP_CP
CLOSE_CANDIDATE_CP = 40

INSUFFICIENT_CANDIDATES = "INSUFFICIENT_CANDIDATES"
NO_OBJECTIVE_ERROR = "NO_OBJECTIVE_ERROR"
CANDIDATES_TOO_CLOSE = "CANDIDATES_TOO_CLOSE"
EVAL_GAP_AMBIGUOUS = "EVAL_GAP_AMBIGUOUS"
CLEAR_EVAL_GAP = "CLEAR_EVAL_GAP"

_MESSAGES = {
    "NONE": "Objective gap is sufficient to allow a later chess diagnosis.",
    "UNKNOWN": "Cannot be determined with sufficient confidence.",
    "NEEDS_REVIEW": "Evidence is ambiguous; human review required.",
}


@dataclass(frozen=True)
class DiagnosisAbstention:
    """Gate for F07-026: do not invent a primary error when this is not NONE."""

    status: AbstentionStatus
    reasons: tuple[str, ...]
    may_diagnose: bool
    message: str
    eval_gap_vs_best_cp: int
    candidate_count: int


def _best_vs_second_cp(comparison: PlayedVsCandidates) -> int | None:
    if len(comparison.diffs) < 2:
        return None
    first = comparison.diffs[0].candidate.player_score.as_cp_units()
    second = comparison.diffs[1].candidate.player_score.as_cp_units()
    return abs(first - second)


def assess_diagnosis_abstention(
    comparison: PlayedVsCandidates,
    *,
    clear_gap_cp: int = CLEAR_EVAL_GAP_CP,
    close_candidate_cp: int = CLOSE_CANDIDATE_CP,
) -> DiagnosisAbstention:
    """Return UNKNOWN / NEEDS_REVIEW, or NONE when a later diagnosis may proceed."""
    count = len(comparison.diffs)
    gap = comparison.eval_gap_vs_best_cp
    reasons: list[str] = []

    if count < 2:
        reasons.append(INSUFFICIENT_CANDIDATES)
        status: AbstentionStatus = "UNKNOWN"
    elif comparison.played_is_best or gap <= 0:
        reasons.append(NO_OBJECTIVE_ERROR)
        status = "UNKNOWN"
    elif gap >= clear_gap_cp:
        reasons.append(CLEAR_EVAL_GAP)
        status = "NONE"
    else:
        spread = _best_vs_second_cp(comparison)
        if spread is not None and spread < close_candidate_cp:
            reasons.append(CANDIDATES_TOO_CLOSE)
        reasons.append(EVAL_GAP_AMBIGUOUS)
        status = "NEEDS_REVIEW"

    return DiagnosisAbstention(
        status=status,
        reasons=tuple(reasons),
        may_diagnose=status == "NONE",
        message=_MESSAGES[status],
        eval_gap_vs_best_cp=gap,
        candidate_count=count,
    )
