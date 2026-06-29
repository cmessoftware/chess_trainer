"""Verbal coaching briefs for human-facing LLM prompts (no statistics)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from coaching.game_analysis import attach_move_notation
from coaching.pgn_context import (
    enrich_critical_moves_with_pgn,
    fetch_game_pgn,
    player_is_white,
)
from coaching.root_cause import analyze_critical_moves
from coaching.pattern_engine import PatternObservation, aggregate_pattern_counts

PATTERN_PHRASES = {
    "unsafe_king": "el rey quedó expuesto",
    "low_mobility": "las piezas tuvieron poca movilidad o quedaron pasivas",
    "opening_unfamiliarity": "hubo inseguridad en la apertura",
    "tactical_blind_spot": "se pasó por alto una idea táctica concreta",
    "endgame_technique": "faltó técnica en el final",
    "uncastled_king": "el rey permaneció mucho tiempo en el centro",
}

PATTERN_CONCEPTS = {
    "unsafe_king": "seguridad del rey",
    "low_mobility": "piezas pasivas / baja actividad",
    "opening_unfamiliarity": "plan de apertura",
    "tactical_blind_spot": "ceguera táctica",
    "endgame_technique": "técnica de final",
    "uncastled_king": "rey sin enrocar",
}

PATTERN_LESSONS = {
    "unsafe_king": "Antes de buscar material o ataque, confirma que tu rey está a salvo.",
    "low_mobility": "Mejora tu peor pieza antes de abrir nuevas complicaciones.",
    "opening_unfamiliarity": "Repasa el plan de la apertura para que las jugadas encajen en una idea.",
    "tactical_blind_spot": "En posiciones forzadas, calcula una variante corta antes de jugar.",
    "endgame_technique": "En finales, prioriza la actividad del rey y la estructura de peones.",
    "uncastled_king": "Enrócate a tiempo o ten un motivo claro para mantener el rey en el centro.",
}

SEVERITY_PHRASES = {
    "blunder": "error grave",
    "mistake": "error claro",
}

PHASE_PHRASES = {
    "opening": "apertura",
    "middlegame": "medio juego",
    "endgame": "final",
}

CRITICAL_LABELS = ("mistake", "blunder")

RESULT_PHRASES = {
    "1-0": "ganaste",
    "0-1": "perdiste",
    "1/2-1/2": "empataste",
    "1/2": "empataste",
}


def _intensity_phrase(count: int, total: int) -> str:
    if total <= 0 or count <= 0:
        return ""
    ratio = count / total
    if ratio >= 0.25:
        return "a menudo"
    if ratio >= 0.10:
        return "en varias ocasiones"
    return "algunas veces"


def verbalize_patterns(
    observations: list[PatternObservation],
    *,
    total_moves: int,
) -> list[str]:
    counts = aggregate_pattern_counts(observations)
    phrases: list[str] = []
    for item in counts:
        pattern = str(item["pattern"])
        count = int(item["count"])
        base = PATTERN_PHRASES.get(pattern, pattern.replace("_", " "))
        intensity = _intensity_phrase(count, total_moves)
        if intensity:
            phrases.append(f"{intensity}: {base}")
        else:
            phrases.append(base)
    return phrases


def verbalize_move_quality(labels: pd.Series) -> str:
    if labels.empty:
        return "impresión general no disponible"

    total = len(labels)
    blunders = int((labels == "blunder").sum())
    mistakes = int((labels == "mistake").sum())
    inaccuracies = int((labels == "inaccuracy").sum())
    good = int((labels == "good").sum())

    if blunders >= max(2, total * 0.15):
        tail = "con algunos errores graves que influyeron en el resultado"
    elif mistakes >= max(3, total * 0.20):
        tail = "con errores repetidos que le dieron chances al rival"
    elif inaccuracies >= max(4, total * 0.25):
        tail = "con imprecisiones que fueron minando la posición"
    elif good >= total * 0.6:
        tail = "con juego mayormente sólido y pocos deslizes aislados"
    else:
        tail = "con alternancia de buenas jugadas y momentos débiles"

    if good >= total * 0.5:
        return f"Partida en general estable {tail}."
    return f"Partida irregular {tail}."


def verbalize_result(result: str | None) -> str | None:
    if result is None:
        return None
    normalized = str(result).strip()
    return RESULT_PHRASES.get(normalized, f"el resultado fue {normalized}")


def describe_critical_moves(
    player_moves: pd.DataFrame,
    labels: pd.Series,
    explanations: list[dict[str, Any]],
    feature_rows: pd.DataFrame,
    *,
    game_rows: pd.DataFrame | None = None,
    repo: Any | None = None,
    game_id: str | None = None,
    player_name: str = "",
    pgn_text: str | None = None,
    is_white: bool | None = None,
    max_moments: int = 6,
) -> list[dict[str, Any]]:
    """Root-cause-aware critical moments for coaching briefs."""
    return analyze_critical_moves(
        player_moves,
        labels,
        explanations,
        feature_rows,
        game_rows=game_rows,
        repo=repo,
        game_id=game_id,
        player_name=player_name,
        pgn_text=pgn_text,
        is_white=is_white,
        max_moments=max_moments,
    )


def build_verbal_game_brief(
    *,
    game_summary: dict[str, Any],
    pattern_observations: list[PatternObservation],
    sample_labels: pd.Series,
    player_name: str,
    player_moves: pd.DataFrame | None = None,
    explanations: list[dict[str, Any]] | None = None,
    feature_rows: pd.DataFrame | None = None,
    repo: Any | None = None,
    game_id: str | None = None,
    player_name_for_notation: str | None = None,
    player_color_index: pd.DataFrame | None = None,
    max_critical_moments: int = 6,
) -> dict[str, Any]:
    """Brief verbal en español para una partida — sin porcentajes ni estadísticas."""
    total_moves = int(game_summary.get("player_moves_analyzed") or len(sample_labels) or 1)
    opening = game_summary.get("opening")
    opponent = game_summary.get("opponent")
    result_text = verbalize_result(game_summary.get("result"))
    resolved_game_id = game_id or game_summary.get("game_id")

    moves_frame = player_moves
    if (
        moves_frame is not None
        and not moves_frame.empty
        and repo is not None
        and resolved_game_id
    ):
        moves_frame = attach_move_notation(
            moves_frame,
            repo,
            game_id=str(resolved_game_id),
            player_name=player_name_for_notation or player_name,
            player_color_index=player_color_index,
        )

    game_story: dict[str, Any] = {
        "opponent": opponent,
        "result_description": result_text,
        "opening": opening,
        "overall_impression": verbalize_move_quality(sample_labels),
    }

    themes = verbalize_patterns(pattern_observations, total_moves=total_moves)
    critical_moves: list[dict[str, Any]] = []
    pgn_text: str | None = None
    is_white = player_is_white(moves_frame, player_name_for_notation or player_name) if moves_frame is not None else True
    if repo is not None and resolved_game_id:
        pgn_text = fetch_game_pgn(repo, str(resolved_game_id))

    if (
        moves_frame is not None
        and explanations is not None
        and feature_rows is not None
        and not moves_frame.empty
    ):
        critical_moves = describe_critical_moves(
            moves_frame,
            sample_labels,
            explanations,
            feature_rows,
            repo=repo,
            game_id=str(resolved_game_id) if resolved_game_id else None,
            player_name=player_name_for_notation or player_name,
            pgn_text=pgn_text,
            is_white=is_white,
            max_moments=max_critical_moments,
        )
        if pgn_text:
            critical_moves = enrich_critical_moves_with_pgn(
                critical_moves,
                pgn_text=pgn_text,
                is_white=is_white,
            )

    brief = {
        "focus": "single_game_review",
        "language": "es",
        "player": player_name,
        "game": game_story,
        "recurring_themes": themes,
        "critical_moves": critical_moves,
        "coach_note": (
            "Redacta en español. Prioriza entradas con root_cause=true. "
            "Explica la causa (pattern/concept) y la consecuencia; no repitas síntomas "
            "listados en consequence_moves. Usa context_pgn y tactical_line cuando existan. "
            "No inventes variantes ni rellenes con consejos genéricos de rey o enroque."
        ),
    }
    return brief
