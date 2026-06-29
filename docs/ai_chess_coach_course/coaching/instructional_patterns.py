"""Instructional chess motifs for coaching (v2 — pedagogical, not generic)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from coaching.pattern_engine import PatternObservation, detect_patterns_for_row

INSTRUCTIONAL_PATTERN_IDS = (
    "loose_piece",
    "hanging_piece",
    "undefended_pawn",
    "tactical_oversight",
    "passive_piece",
    "king_safety",
)

PATTERN_DESCRIPTIONS = {
    "loose_piece": "una pieza quedó con poca defensa",
    "hanging_piece": "una pieza quedó en prise",
    "undefended_pawn": "un peón importante quedó sin defensa",
    "tactical_oversight": "se pasó por alto una idea táctica concreta",
    "passive_piece": "una pieza quedó pasiva o mal ubicada",
    "king_safety": "el rey quedó expuesto de forma real",
}

PATTERN_CONCEPTS = {
    "loose_piece": "pieza sin suficiente respaldo",
    "hanging_piece": "pieza colgada",
    "undefended_pawn": "peón avanzado indefenso",
    "tactical_oversight": "ceguera táctica",
    "passive_piece": "pieza pasiva / baja actividad",
    "king_safety": "seguridad del rey",
}

PATTERN_LESSONS = {
    "loose_piece": "Antes de mover, revisa qué piezas dejan de estar defendidas.",
    "hanging_piece": "Comprueba si tu jugada deja material capturable sin compensación.",
    "undefended_pawn": "Antes de empujar un peón, confirma que los peones vecinos siguen defendidos.",
    "tactical_oversight": "Antes de jugar, calcula la respuesta más forzada del rival en la variante concreta.",
    "passive_piece": "Mejora tu peor pieza antes de abrir nuevas complicaciones.",
    "king_safety": "Confirma que tu rey está a salvo antes de buscar material o ataque.",
}

MISTAKE_CP_THRESHOLD = 151.0
BLUNDER_CP_THRESHOLD = 501.0


@dataclass(frozen=True)
class InstructionalPattern:
    pattern_name: str
    confidence: float
    concept: str
    consequence: str
    lesson: str


def _feature_value(row: pd.Series, name: str, default: float = 0.0) -> float:
    if name not in row.index:
        return default
    value = row[name]
    if pd.isna(value):
        return default
    return float(value)


def _is_pawn_push(move_san: str | None) -> bool:
    if not move_san:
        return False
    san = str(move_san).strip()
    if not san or san.startswith("O-O"):
        return False
    return san[0].islower()


def _is_capture(san: str | None) -> bool:
    return bool(san) and "x" in str(san)


def _cp_loss(row: pd.Series) -> float:
    value = _feature_value(row, "score_diff", 0.0)
    return max(0.0, value)


def detect_instructional_pattern(
    row: pd.Series,
    explanation: dict[str, Any],
    *,
    error_label: str,
    tactical_line: str | None = None,
    opponent_reply: str | None = None,
    legacy_patterns: list[PatternObservation] | None = None,
) -> InstructionalPattern:
    """
    Diagnose the instructional motif for one critical moment.

    Uses feature rows, optional PGN tactical line, and v1 pattern hints.
    """
    cp_loss = _cp_loss(row)
    move_san = str(row.get("move_san") or "").strip()
    branching = _feature_value(row, "branching_factor")
    mobility = _feature_value(row, "self_mobility")
    king_safety = _feature_value(row, "king_safety")
    phase = str(row.get("phase") or "").lower()

    candidates: list[tuple[str, float]] = []

    if _is_pawn_push(move_san) and _is_capture(opponent_reply) and cp_loss >= MISTAKE_CP_THRESHOLD:
        candidates.append(("undefended_pawn", 0.85))

    if _is_capture(opponent_reply) and cp_loss >= BLUNDER_CP_THRESHOLD:
        candidates.append(("hanging_piece", 0.9))
    elif _is_capture(opponent_reply) and cp_loss >= MISTAKE_CP_THRESHOLD:
        candidates.append(("loose_piece", 0.75))

    if branching >= 25 or error_label == "blunder":
        candidates.append(("tactical_oversight", min(1.0, 0.45 + branching / 60)))

    if mobility < 8 and cp_loss >= MISTAKE_CP_THRESHOLD:
        candidates.append(("passive_piece", min(1.0, 0.5 + (8 - mobility) * 0.05)))

    if king_safety < -1.5 and cp_loss >= BLUNDER_CP_THRESHOLD and phase in {"middlegame", "opening"}:
        candidates.append(("king_safety", min(1.0, 0.55 + abs(min(king_safety, 0)) * 0.1)))

    if legacy_patterns:
        for observation in legacy_patterns:
            if observation.pattern_name == "tactical_blind_spot":
                candidates.append(("tactical_oversight", observation.confidence))
            elif observation.pattern_name == "low_mobility":
                candidates.append(("passive_piece", observation.confidence))
            elif observation.pattern_name == "unsafe_king" and cp_loss >= BLUNDER_CP_THRESHOLD:
                candidates.append(("king_safety", observation.confidence))

    if not candidates:
        fallback = detect_patterns_for_row(row, explanation)
        if fallback:
            top = max(fallback, key=lambda item: item.confidence)
            mapped = {
                "tactical_blind_spot": "tactical_oversight",
                "low_mobility": "passive_piece",
                "unsafe_king": "king_safety",
                "endgame_technique": "passive_piece",
                "opening_unfamiliarity": "tactical_oversight",
                "uncastled_king": "king_safety",
            }.get(top.pattern_name, "tactical_oversight")
            candidates.append((mapped, top.confidence * 0.7))
        else:
            candidates.append(("tactical_oversight", 0.4))

    pattern_name, confidence = max(candidates, key=lambda item: item[1])
    description = PATTERN_DESCRIPTIONS[pattern_name]
    concept = PATTERN_CONCEPTS[pattern_name]
    lesson = PATTERN_LESSONS[pattern_name]

    if tactical_line:
        consequence = f"La secuencia {tactical_line} aprovechó el error."
    elif opponent_reply:
        consequence = f"El rival respondió con {opponent_reply} y la posición empeoró."
    elif cp_loss >= BLUNDER_CP_THRESHOLD:
        consequence = "La posición pasó a una desventaja decisiva."
    elif cp_loss >= MISTAKE_CP_THRESHOLD:
        consequence = "La posición cedió iniciativa o material."
    else:
        consequence = "La jugada debilitó la coordinación de las piezas."

    return InstructionalPattern(
        pattern_name=pattern_name,
        confidence=confidence,
        concept=f"{concept}: {description}.",
        consequence=consequence,
        lesson=lesson,
    )
