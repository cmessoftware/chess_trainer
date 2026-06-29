"""Structured diagnosis models (V4)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import chess
import pandas as pd


@dataclass(frozen=True)
class PatternMatch:
    pattern_id: str
    confidence: float
    tactical_motif: str | None = None
    affected_piece: str | None = None
    affected_square: str | None = None
    material_change: str | None = None
    opened_file: str | None = None
    weak_square: str | None = None
    strategic_theme: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class DiagnosisContext:
    row: pd.Series
    error_label: str
    cp_loss: float
    player_color: chess.Color
    root_ply: int
    sans: list[str]
    player_move_san: str
    opponent_move_san: str | None
    tactical_line: str | None
    opponent_reply: str | None
    before_board: chess.Board
    after_player_board: chess.Board
    after_opponent_board: chess.Board | None


@dataclass
class StructuredDiagnosis:
    primary_pattern: str
    secondary_patterns: list[str]
    issue: str
    consequence: str
    lesson_hint: str
    material_change: str
    tactical_motif: str | None = None
    affected_piece: str | None = None
    strategic_theme: str | None = None
    opened_file: str | None = None
    weak_square: str | None = None
    theme: str | None = None
    supporting_features: list[str] | None = None
    diagnosis_type: str | None = None
    sections: dict[str, Any] | None = None
    include_opponent_reply: bool = True
    confidence: float = 0.0

    def as_moment_fields(self) -> dict[str, Any]:
        fields: dict[str, Any] = {
            "pattern": self.primary_pattern,
            "issue": self.issue,
            "concept": self.issue,
            "consequence": self.consequence,
            "lesson": self.lesson_hint,
            "lesson_hint": self.lesson_hint,
            "material_change": self.material_change,
        }
        if self.theme:
            fields["theme"] = self.theme
        if self.tactical_motif:
            fields["tactical_motif"] = self.tactical_motif
        elif self.theme:
            fields["tactical_motif"] = self.theme
        if self.affected_piece:
            fields["affected_piece"] = self.affected_piece
        if self.strategic_theme:
            fields["strategic_theme"] = self.strategic_theme
        if self.opened_file:
            fields["opened_file"] = self.opened_file
        if self.weak_square:
            fields["weak_square"] = self.weak_square
        if self.secondary_patterns:
            fields["secondary_patterns"] = self.secondary_patterns
        if self.supporting_features:
            fields["supporting_features"] = self.supporting_features
        if self.diagnosis_type:
            fields["diagnosis_type"] = self.diagnosis_type
        if self.sections:
            fields["sections"] = self.sections
        return fields
