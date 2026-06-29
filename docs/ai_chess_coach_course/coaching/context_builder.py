"""Structured coaching context for LLM prompts (no raw SHAP or engine features)."""

from __future__ import annotations

import json
from typing import Any

import pandas as pd

from coaching.pattern_engine import OPENING_PREFIX, aggregate_pattern_counts
from coaching.pattern_engine import PatternObservation

FORBIDDEN_CONTEXT_KEYS = frozenset(
    {
        "shap_values",
        "mean_abs_shap",
        "score_cp",
        "mate_in",
        "depth_score_diff",
        "top_positive_features",
        "top_negative_features",
    }
)
FORBIDDEN_SUBSTRINGS = ("shap", "score_cp", "mate_in", "depth_score_diff")


def _label_distribution(labels: pd.Series) -> dict[str, float]:
    if labels.empty:
        return {}
    counts = labels.value_counts(normalize=True)
    return {str(label): round(float(value), 4) for label, value in counts.items()}


def _top_openings_from_rows(rows: pd.DataFrame, *, limit: int = 3) -> list[str]:
    opening_columns = [column for column in rows.columns if str(column).startswith(OPENING_PREFIX)]
    if not opening_columns:
        return []
    active_counts: dict[str, int] = {}
    for column in opening_columns:
        hits = int((rows[column] >= 0.5).sum())
        if hits:
            active_counts[str(column).removeprefix(OPENING_PREFIX)] = hits
    ranked = sorted(active_counts.items(), key=lambda item: item[1], reverse=True)
    return [name for name, _ in ranked[:limit]]


def build_coaching_context(
    *,
    pattern_observations: list[PatternObservation],
    sample_rows: pd.DataFrame,
    sample_labels: pd.Series | None = None,
    player_elo: float | None = None,
    player_name: str | None = None,
    analysis_scope: str = "single_game",
    games_analyzed: list[dict[str, Any]] | None = None,
    trend: str = "stable",
) -> dict[str, Any]:
    if player_elo is None and "player_elo" in sample_rows.columns:
        player_elo = float(sample_rows["player_elo"].median())

    labels = sample_labels
    if labels is None and "error_label" in sample_rows.columns:
        labels = sample_rows["error_label"]

    game_summaries = games_analyzed or []
    context: dict[str, Any] = {
        "analysis_scope": analysis_scope,
        "player_name": player_name,
        "player_elo": round(player_elo, 1) if player_elo is not None else None,
        "games_count": len(game_summaries),
        "games_analyzed": game_summaries,
        "total_moves_analyzed": int(len(sample_rows)),
        "dominant_patterns": aggregate_pattern_counts(pattern_observations),
        "trend": trend,
        "sample_classes": _label_distribution(labels) if labels is not None else {},
        "top_openings": _top_openings_from_rows(sample_rows),
    }
    validate_coaching_context(context)
    return context


def validate_coaching_context(context: dict[str, Any]) -> None:
    """Raise ValueError if forbidden engine/SHAP fields appear in the payload."""

    def walk(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                key_lower = str(key).lower()
                if key in FORBIDDEN_CONTEXT_KEYS or any(
                    token in key_lower for token in FORBIDDEN_SUBSTRINGS
                ):
                    raise ValueError(f"Forbidden context field at {path}.{key}")
                walk(nested, f"{path}.{key}")
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                walk(nested, f"{path}[{index}]")

    walk(context, "context")


def save_coaching_context(context: dict[str, Any], output_path: str) -> None:
    validate_coaching_context(context)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(context, handle, indent=2, ensure_ascii=False)
