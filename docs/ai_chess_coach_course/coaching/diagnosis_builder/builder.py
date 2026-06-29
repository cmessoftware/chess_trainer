"""DiagnosisBuilder — merge tactical tags, features, SHAP, and board fallback (V5-lite)."""

from __future__ import annotations

from typing import Any

import pandas as pd

from coaching.diagnosis import DiagnosisEngine
from coaching.diagnosis.material import material_change_from_cp, material_change_label_es
from coaching.diagnosis.models import StructuredDiagnosis
from coaching.diagnosis_builder.feature_interpreter import interpret_features
from coaching.diagnosis_builder.shap_interpreter import interpret_shap
from coaching.diagnosis_builder.classifier import classify_diagnosis_type
from coaching.diagnosis_builder.style_renderer import apply_diagnosis_style
from coaching.diagnosis_builder.tags_utils import parse_tags_from_row
from coaching.diagnosis_builder.tactical_interpreter import (
    THEME_ES,
    interpret_tactical_tags,
)


def _cp_loss(row: pd.Series) -> float:
    value = row.get("score_diff")
    if value is None or pd.isna(value):
        return 0.0
    return max(0.0, float(value))


def _consequence_from_context(
    *,
    tactical_line: str | None,
    opponent_reply: str | None,
    material_change: str,
) -> str:
    if tactical_line:
        return f"La secuencia {tactical_line} aprovechó el error."
    if opponent_reply:
        material_phrase = material_change_label_es(material_change)
        if material_change != "none":
            return (
                f"El rival respondió {opponent_reply} y la posición sufrió {material_phrase}."
            )
        return f"El rival respondió {opponent_reply} y la iniciativa cambió de mano."
    return "La secuencia posterior empeoró la evaluación de la posición."


class DiagnosisBuilder:
    """
    Priority: tactical tags > board detectors (V4) > legacy heuristics.

    Features and SHAP always enrich supporting_features when available.
    """

    def __init__(self, board_engine: DiagnosisEngine | None = None) -> None:
        self.board_engine = board_engine or DiagnosisEngine()

    def build(
        self,
        row: pd.Series,
        explanation: dict[str, Any],
        *,
        error_label: str,
        sans: list[str] | None,
        root_ply: int,
        is_white: bool,
        tactical_line: str | None = None,
        opponent_reply: str | None = None,
    ) -> StructuredDiagnosis:
        move_san = str(row.get("move_san") or "").strip()
        supporting_features = interpret_features(row)
        supporting_features.extend(interpret_shap(explanation))
        supporting_features = _dedupe_phrases(supporting_features)

        tags = parse_tags_from_row(row)
        tactical = interpret_tactical_tags(
            tags,
            move_san=move_san,
            opponent_reply=opponent_reply,
        )

        if tactical is not None and tactical.is_actionable:
            material = tactical.material_change
            if material == "none":
                material = material_change_from_cp(_cp_loss(row))
            diagnosis = StructuredDiagnosis(
                primary_pattern=tactical.pattern_id,
                secondary_patterns=[tag for tag in tactical.tags if tag != tactical.pattern_id][:3],
                theme=tactical.theme,
                issue=tactical.issue,
                consequence=_consequence_from_context(
                    tactical_line=tactical_line,
                    opponent_reply=opponent_reply,
                    material_change=material,
                ),
                lesson_hint=tactical.lesson_hint,
                material_change=material,
                tactical_motif=tactical.theme,
                supporting_features=supporting_features,
                confidence=tactical.confidence,
            )
            diagnosis_type = classify_diagnosis_type(
                row,
                tags=tactical.tags,
                primary_pattern=tactical.pattern_id,
                tactical_actionable=True,
            )
            return apply_diagnosis_style(
                diagnosis,
                diagnosis_type,
                row,
                opponent_reply=opponent_reply,
                tactical_line=tactical_line,
            )

        board_diagnosis = self.board_engine.diagnose(
            row,
            error_label=error_label,
            sans=sans,
            root_ply=root_ply,
            is_white=is_white,
            tactical_line=tactical_line,
            opponent_reply=opponent_reply,
        )
        theme = board_diagnosis.theme or THEME_ES.get(
            board_diagnosis.primary_pattern,
            board_diagnosis.primary_pattern.replace("_", " ").title(),
        )
        merged_supporting = _dedupe_phrases(
            supporting_features + (board_diagnosis.supporting_features or [])
        )
        diagnosis = StructuredDiagnosis(
            primary_pattern=board_diagnosis.primary_pattern,
            secondary_patterns=board_diagnosis.secondary_patterns,
            theme=theme,
            issue=board_diagnosis.issue,
            consequence=board_diagnosis.consequence,
            lesson_hint=board_diagnosis.lesson_hint,
            material_change=board_diagnosis.material_change,
            tactical_motif=board_diagnosis.tactical_motif or theme,
            affected_piece=board_diagnosis.affected_piece,
            strategic_theme=board_diagnosis.strategic_theme,
            opened_file=board_diagnosis.opened_file,
            weak_square=board_diagnosis.weak_square,
            supporting_features=merged_supporting,
            confidence=board_diagnosis.confidence,
        )
        tags = parse_tags_from_row(row)
        diagnosis_type = classify_diagnosis_type(
            row,
            tags=tags,
            primary_pattern=board_diagnosis.primary_pattern,
            tactical_actionable=False,
        )
        return apply_diagnosis_style(
            diagnosis,
            diagnosis_type,
            row,
            opponent_reply=opponent_reply,
            tactical_line=tactical_line,
        )


def _dedupe_phrases(phrases: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for phrase in phrases:
        normalized = phrase.strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(phrase)
    return result[:4]
