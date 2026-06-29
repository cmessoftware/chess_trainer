"""Minimal pattern engine: features + SHAP evidence → chess coaching concepts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

OPENING_PREFIX = "opening_"
ERROR_LABELS = ("good", "inaccuracy", "mistake", "blunder")


@dataclass(frozen=True)
class PatternObservation:
    pattern_name: str
    confidence: float
    severity: str
    evidence_summary: str


def _feature_value(row: pd.Series, name: str, default: float = 0.0) -> float:
    if name not in row.index:
        return default
    value = row[name]
    if pd.isna(value):
        return default
    return float(value)


def _shap_impact_map(explanation: dict[str, Any]) -> dict[str, float]:
    impacts: dict[str, float] = {}
    for bucket in ("top_positive_features", "top_negative_features"):
        for item in explanation.get(bucket, []):
            feature = item["feature"]
            impacts[feature] = impacts.get(feature, 0.0) + abs(float(item["impact"]))
    return impacts


def _opening_name_from_row(row: pd.Series) -> str | None:
    opening_columns = [column for column in row.index if str(column).startswith(OPENING_PREFIX)]
    active = [column for column in opening_columns if _feature_value(row, column) >= 0.5]
    if not active:
        return None
    best = max(active, key=lambda column: _feature_value(row, column))
    return str(best).removeprefix(OPENING_PREFIX)


def _severity(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.45:
        return "medium"
    return "low"


def detect_patterns_for_row(
    row: pd.Series,
    explanation: dict[str, Any],
) -> list[PatternObservation]:
    """Map one position row + local SHAP explanation to named coaching patterns."""
    impacts = _shap_impact_map(explanation)
    predicted = explanation.get("predicted_label", "good")
    observations: list[PatternObservation] = []

    king_safety = _feature_value(row, "king_safety")
    king_shap = impacts.get("king_safety", 0.0)
    if king_safety < 0 or king_shap >= 0.05:
        confidence = min(1.0, 0.4 + abs(min(king_safety, 0)) * 0.1 + king_shap)
        observations.append(
            PatternObservation(
                pattern_name="unsafe_king",
                confidence=confidence,
                severity=_severity(confidence),
                evidence_summary="King safety is weak in this position sample.",
            )
        )

    self_mobility = _feature_value(row, "self_mobility")
    mobility_shap = impacts.get("self_mobility", 0.0)
    if self_mobility < 8 or mobility_shap >= 0.05:
        confidence = min(1.0, 0.35 + max(0.0, (8 - self_mobility) * 0.05) + mobility_shap)
        observations.append(
            PatternObservation(
                pattern_name="low_mobility",
                confidence=confidence,
                severity=_severity(confidence),
                evidence_summary="Piece mobility is limited relative to typical middlegame positions.",
            )
        )

    opening = _opening_name_from_row(row)
    if opening and predicted in {"mistake", "blunder"}:
        confidence = 0.6 if predicted == "mistake" else 0.8
        observations.append(
            PatternObservation(
                pattern_name="opening_unfamiliarity",
                confidence=confidence,
                severity=_severity(confidence),
                evidence_summary=f"Mistakes cluster around the {opening} opening line.",
            )
        )

    branching = _feature_value(row, "branching_factor")
    branching_shap = impacts.get("branching_factor", 0.0)
    if branching >= 25 or branching_shap >= 0.05:
        confidence = min(1.0, 0.3 + branching / 50 + branching_shap)
        observations.append(
            PatternObservation(
                pattern_name="tactical_blind_spot",
                confidence=confidence,
                severity=_severity(confidence),
                evidence_summary="Complex tactical positions show elevated error signal.",
            )
        )

    if _feature_value(row, "is_pawn_endgame") >= 0.5:
        confidence = 0.55 + impacts.get("material_total", 0.0) * 0.5
        observations.append(
            PatternObservation(
                pattern_name="endgame_technique",
                confidence=min(1.0, confidence),
                severity=_severity(min(1.0, confidence)),
                evidence_summary="Pawn endgames appear in the error sample.",
            )
        )

    move_number = _feature_value(row, "move_number")
    if _feature_value(row, "has_castling_rights") < 0.5 and move_number < 15:
        confidence = min(1.0, 0.5 + (15 - move_number) * 0.03)
        observations.append(
            PatternObservation(
                pattern_name="uncastled_king",
                confidence=confidence,
                severity=_severity(confidence),
                evidence_summary="The king remains uncastled early in the game.",
            )
        )

    return observations


def detect_patterns_for_sample(
    rows: pd.DataFrame,
    explanations: list[dict[str, Any]],
) -> list[PatternObservation]:
    if len(rows) != len(explanations):
        raise ValueError("rows and explanations must have the same length")
    observations: list[PatternObservation] = []
    for (_, row), explanation in zip(rows.iterrows(), explanations, strict=True):
        observations.extend(detect_patterns_for_row(row, explanation))
    return observations


def aggregate_pattern_counts(
    observations: list[PatternObservation],
) -> list[dict[str, int | str]]:
    counts: dict[str, int] = {}
    for observation in observations:
        counts[observation.pattern_name] = counts.get(observation.pattern_name, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    return [{"pattern": name, "count": count} for name, count in ranked]
