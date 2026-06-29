"""Assign coaching diagnosis style (V6-lite)."""

from __future__ import annotations

import pandas as pd

from coaching.diagnosis_builder.tags_utils import parse_tags

DiagnosisType = str

TACTICAL_PATTERNS = frozenset(
    {
        "fork",
        "pin",
        "skewer",
        "hanging_piece",
        "undefended_pawn",
        "loose_piece_after_pawn_push",
        "discovered_attack",
        "discovered_check",
        "double_attack",
        "remove_defender",
        "mate",
        "mate_threat",
        "check",
    }
)

TACTICAL_TAGS = frozenset(
    {
        "fork",
        "pin",
        "skewer",
        "hanging_piece",
        "discovered_attack",
        "discovered_check",
        "double_attack",
        "remove_defender",
        "mate",
        "mate_threat",
        "check",
        "piece_lost",
        "queen_lost",
        "exchange_lost",
    }
)

OPENING_MAX_MOVE = 12


def _phase_name(row: pd.Series) -> str:
    return str(row.get("phase") or "").strip().lower()


def _move_number(row: pd.Series) -> int | None:
    value = row.get("move_number")
    if value is None or pd.isna(value):
        return None
    return int(value)


def classify_diagnosis_type(
    row: pd.Series,
    *,
    tags: list[str] | None = None,
    primary_pattern: str,
    tactical_actionable: bool = False,
) -> DiagnosisType:
    """
    Priority: tactical > endgame > opening > positional.

    Python assigns the style; Gemini must not infer it.
    """
    resolved_tags = tags if tags is not None else parse_tags(row.get("tags"))
    tag_set = set(resolved_tags)
    phase = _phase_name(row)
    move_number = _move_number(row)

    if tactical_actionable or primary_pattern in TACTICAL_PATTERNS or tag_set & TACTICAL_TAGS:
        return "tactical"

    if phase in {"endgame", "final"} or int(row.get("is_pawn_endgame") or 0) == 1:
        return "endgame"

    if phase in {"opening", "apertura"} or (move_number is not None and move_number <= OPENING_MAX_MOVE):
        return "opening"

    return "positional"
