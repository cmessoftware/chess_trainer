"""Cluster critical moves into 2–3 coaching lessons (V7 insight-based coaching)."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

MAX_LESSONS = 3
MIN_LESSONS = 2

LESSON_TITLES: dict[str, str] = {
    "counterplay": "Permitir contrajuego activo del rival",
    "enemy_activity": "Mejorar las piezas enemigas",
    "tactical": "Errores tácticos evitables",
    "opening": "Plan de apertura poco claro",
    "endgame": "Actividad del rey y técnica en el final",
    "positional": "Comprensión posicional",
    "simplification": "Simplificaciones desfavorables",
    "strategic": "Decisiones estratégicas",
}

PHASE_ORDER = ("opening", "middlegame", "endgame")
PHASE_ES = {
    "opening": "apertura",
    "middlegame": "medio juego",
    "endgame": "final",
}


def _cluster_key(moment: dict[str, Any]) -> str:
    theme = str(moment.get("theme") or moment.get("strategic_theme") or "").lower()
    pattern = str(moment.get("pattern") or "").lower()
    dtype = str(moment.get("diagnosis_type") or "positional")

    if any(token in theme for token in ("counterplay", "contrajuego", "counter")):
        return "counterplay"
    if any(token in pattern for token in ("counterplay", "counter_attack")):
        return "counterplay"
    if any(
        token in theme or token in pattern
        for token in ("enemy", "opponent_activity", "passive", "mobility", "coordination")
    ):
        return "enemy_activity"
    if dtype in LESSON_TITLES:
        return dtype
    return "positional"


def _severity_rank(moment: dict[str, Any]) -> int:
    severity = str(moment.get("severity") or "").lower()
    if "grave" in severity or moment.get("severity") == "blunder":
        return 0
    if "claro" in severity or moment.get("severity") == "mistake":
        return 1
    return 2


def _merge_to_target(clusters: dict[str, list[dict[str, Any]]], target: int) -> dict[str, list[dict[str, Any]]]:
    if len(clusters) <= target:
        return clusters

    ordered = sorted(
        clusters.items(),
        key=lambda item: (
            min(_severity_rank(move) for move in item[1]),
            -len(item[1]),
        ),
    )
    merged: dict[str, list[dict[str, Any]]] = {}
    overflow: list[dict[str, Any]] = []
    for index, (key, moves) in enumerate(ordered):
        if index < target:
            merged[key] = moves
        else:
            overflow.extend(moves)

    if overflow:
        fallback_key = next(iter(merged))
        merged[fallback_key].extend(overflow)
    return merged


def _lesson_title(key: str, moves: list[dict[str, Any]]) -> str:
    if key in LESSON_TITLES:
        return LESSON_TITLES[key]
    theme = next((move.get("theme") for move in moves if move.get("theme")), None)
    if theme:
        return str(theme).replace("_", " ").capitalize()
    return "Idea recurrente en la partida"


def _synthesize_why(moves: list[dict[str, Any]]) -> str:
    issues = [str(move.get("issue") or "").strip() for move in moves if move.get("issue")]
    if not issues:
        return "Varias jugadas debilitaron tu posición de forma similar."
    if len(issues) == 1:
        return issues[0]
    return issues[0]


def _synthesize_how_to_avoid(moves: list[dict[str, Any]]) -> str:
    hints = [
        str(move.get("lesson_hint") or move.get("lesson") or "").strip()
        for move in moves
        if move.get("lesson_hint") or move.get("lesson")
    ]
    if not hints:
        return "Antes de repetir el patrón, pregúntate qué pieza rival gana actividad con tu jugada."
    return hints[0]


def _phase_summary(game: dict[str, Any], critical_moves: list[dict[str, Any]]) -> dict[str, str]:
    phases_present = {str(move.get("phase") or "") for move in critical_moves}
    opening = game.get("opening") or "la apertura jugada"
    summary: dict[str, str] = {}

    if "opening" in phases_present or game.get("opening"):
        summary["opening"] = f"En la apertura ({opening}) definiste el carácter inicial de la partida."
    if "middlegame" in phases_present:
        summary["middlegame"] = "En el medio juego la lucha giró en torno a la actividad de las piezas y al plan."
    if "endgame" in phases_present:
        summary["endgame"] = "En el final la precisión técnica y la actividad del rey marcaron la diferencia."
    if not summary:
        summary["middlegame"] = "La partida tuvo fases equilibradas con momentos decisivos en el medio juego."
    return summary


def synthesize_lessons(
    critical_moves: list[dict[str, Any]],
    *,
    game: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build lesson_clusters and phase_summary for the V7 LLM payload."""
    game = game or {}
    if not critical_moves:
        return {"lesson_clusters": [], "phase_summary": _phase_summary(game, [])}

    clusters: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for moment in critical_moves:
        clusters[_cluster_key(moment)].append(moment)

    target = min(MAX_LESSONS, max(MIN_LESSONS, len(clusters)))
    if len(clusters) > MAX_LESSONS:
        clusters = _merge_to_target(clusters, MAX_LESSONS)
    elif len(clusters) < MIN_LESSONS and len(critical_moves) >= MIN_LESSONS:
        # Split largest cluster by phase when we need more distinct lessons
        largest_key = max(clusters, key=lambda key: len(clusters[key]))
        largest = clusters.pop(largest_key)
        by_phase: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for move in largest:
            phase = str(move.get("phase") or "middlegame")
            by_phase[phase].append(move)
        if len(by_phase) >= MIN_LESSONS:
            for phase, moves in by_phase.items():
                clusters[f"{largest_key}:{phase}"] = moves
        else:
            clusters[largest_key] = largest

    lesson_clusters: list[dict[str, Any]] = []
    for key, moves in sorted(
        clusters.items(),
        key=lambda item: (
            min(_severity_rank(move) for move in item[1]),
            -len(item[1]),
        ),
    ):
        root_moves = [move for move in moves if move.get("root_cause")]
        evidence = root_moves or moves
        lesson_clusters.append(
            {
                "title": _lesson_title(key.split(":")[0], moves),
                "idea": _synthesize_why(evidence),
                "evidence_moves": [str(move.get("player_move") or move.get("move")) for move in evidence],
                "move_numbers": [int(move["move_number"]) for move in evidence if "move_number" in move],
                "diagnosis_types": sorted({str(move.get("diagnosis_type") or "positional") for move in moves}),
                "why": _synthesize_why(moves),
                "how_to_avoid": _synthesize_how_to_avoid(moves),
            }
        )

    return {
        "lesson_clusters": lesson_clusters[:MAX_LESSONS],
        "phase_summary": _phase_summary(game, critical_moves),
    }
