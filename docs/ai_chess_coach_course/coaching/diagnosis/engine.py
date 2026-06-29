"""Diagnosis engine — runs pattern detectors and builds structured output."""

from __future__ import annotations

from typing import Any

import chess
import pandas as pd

from coaching.diagnosis.base import PatternDetector
from coaching.diagnosis.board_utils import build_board_at_ply
from coaching.diagnosis.detectors.positional import KingSafetyDetector, PassiveRookDetector
from coaching.diagnosis.detectors.tactical import (
    ForkDetector,
    HangingPieceDetector,
    LoosePieceAfterPawnPushDetector,
    PinDetector,
    SkewerDetector,
    UndefendedPawnDetector,
)
from coaching.diagnosis.material import material_change_from_boards, material_change_from_cp
from coaching.diagnosis.models import DiagnosisContext, PatternMatch, StructuredDiagnosis
from coaching.diagnosis.text_builder import build_consequence, build_issue, build_lesson_hint
from coaching.instructional_patterns import detect_instructional_pattern

DEFAULT_DETECTORS: tuple[type[PatternDetector], ...] = (
    ForkDetector,
    PinDetector,
    SkewerDetector,
    HangingPieceDetector,
    UndefendedPawnDetector,
    LoosePieceAfterPawnPushDetector,
    KingSafetyDetector,
    PassiveRookDetector,
)

PATTERN_PRIORITY = {
    "fork": 10,
    "pin": 9,
    "skewer": 9,
    "hanging_piece": 8,
    "undefended_pawn": 8,
    "loose_piece_after_pawn_push": 7,
    "king_safety": 6,
    "passive_rook": 5,
    "tactical_oversight": 1,
}


def _cp_loss(row: pd.Series) -> float:
    value = row.get("score_diff")
    if value is None or pd.isna(value):
        return 0.0
    return max(0.0, float(value))


class DiagnosisEngine:
    """Run board-based detectors and produce a StructuredDiagnosis."""

    def __init__(self, detectors: list[PatternDetector] | None = None) -> None:
        if detectors is None:
            self.detectors = [cls() for cls in DEFAULT_DETECTORS]
        else:
            self.detectors = detectors

    def build_context(
        self,
        row: pd.Series,
        *,
        error_label: str,
        sans: list[str],
        root_ply: int,
        is_white: bool,
        tactical_line: str | None = None,
        opponent_reply: str | None = None,
    ) -> DiagnosisContext | None:
        if not sans or root_ply < 0 or root_ply >= len(sans):
            return None

        player_color = chess.WHITE if is_white else chess.BLACK
        before_board = build_board_at_ply(sans, root_ply)
        after_player_board = build_board_at_ply(sans, root_ply + 1)
        after_opponent_board = build_board_at_ply(sans, root_ply + 2)
        if before_board is None or after_player_board is None:
            return None
        player_move_san = sans[root_ply]
        opponent_move_san = sans[root_ply + 1] if root_ply + 1 < len(sans) else None

        return DiagnosisContext(
            row=row,
            error_label=error_label,
            cp_loss=_cp_loss(row),
            player_color=player_color,
            root_ply=root_ply,
            sans=sans,
            player_move_san=player_move_san,
            opponent_move_san=opponent_move_san,
            tactical_line=tactical_line,
            opponent_reply=opponent_reply,
            before_board=before_board,
            after_player_board=after_player_board,
            after_opponent_board=after_opponent_board,
        )

    def detect_matches(self, context: DiagnosisContext) -> list[PatternMatch]:
        matches: list[PatternMatch] = []
        for detector in self.detectors:
            match = detector.detect(context)
            if match is not None:
                matches.append(match)
        return matches

    def select_primary(self, matches: list[PatternMatch]) -> PatternMatch:
        if not matches:
            return PatternMatch(pattern_id="tactical_oversight", confidence=0.4)
        return max(
            matches,
            key=lambda item: (
                PATTERN_PRIORITY.get(item.pattern_id, 0),
                item.confidence,
            ),
        )

    def diagnose(
        self,
        row: pd.Series,
        *,
        error_label: str,
        sans: list[str] | None,
        root_ply: int,
        is_white: bool,
        tactical_line: str | None = None,
        opponent_reply: str | None = None,
    ) -> StructuredDiagnosis:
        if not sans:
            return self._fallback_diagnosis(row, error_label, tactical_line, opponent_reply)

        context = self.build_context(
            row,
            error_label=error_label,
            sans=sans,
            root_ply=root_ply,
            is_white=is_white,
            tactical_line=tactical_line,
            opponent_reply=opponent_reply,
        )
        if context is None:
            return self._fallback_diagnosis(row, error_label, tactical_line, opponent_reply)

        matches = self.detect_matches(context)
        primary = self.select_primary(matches)
        secondary = [
            match.pattern_id
            for match in sorted(matches, key=lambda item: item.confidence, reverse=True)
            if match.pattern_id != primary.pattern_id
        ]

        material = material_change_from_cp(context.cp_loss)
        if context.after_opponent_board is not None:
            board_material = material_change_from_boards(
                context.before_board,
                context.after_opponent_board,
                context.player_color,
            )
            if board_material != "none":
                material = board_material

        return StructuredDiagnosis(
            primary_pattern=primary.pattern_id,
            secondary_patterns=secondary,
            issue=build_issue(primary, context),
            consequence=build_consequence(primary, context, material),
            lesson_hint=build_lesson_hint(primary, context),
            material_change=material,
            tactical_motif=primary.tactical_motif,
            affected_piece=primary.affected_piece,
            strategic_theme=primary.strategic_theme,
            opened_file=primary.opened_file,
            weak_square=primary.weak_square,
            confidence=primary.confidence,
        )

    def _fallback_diagnosis(
        self,
        row: pd.Series,
        error_label: str,
        tactical_line: str | None,
        opponent_reply: str | None,
    ) -> StructuredDiagnosis:
        cp_loss = _cp_loss(row)
        move_san = str(row.get("move_san") or "la jugada").strip()
        material = material_change_from_cp(cp_loss)
        legacy = detect_instructional_pattern(
            row,
            {},
            error_label=error_label,
            tactical_line=tactical_line,
            opponent_reply=opponent_reply,
        )
        issue = legacy.concept if legacy.concept else f"Con {move_san} se pasó por alto una respuesta táctica concreta."
        if issue.endswith(".") and " " in issue:
            pass
        elif move_san not in issue:
            issue = f"Con {move_san}: {issue}"

        return StructuredDiagnosis(
            primary_pattern=legacy.pattern_name,
            secondary_patterns=[],
            issue=issue,
            consequence=legacy.consequence,
            lesson_hint=legacy.lesson,
            material_change=material,
            confidence=legacy.confidence,
        )

    def diagnose_from_legacy(
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
        return self.diagnose(
            row,
            error_label=error_label,
            sans=sans,
            root_ply=root_ply,
            is_white=is_white,
            tactical_line=tactical_line,
            opponent_reply=opponent_reply,
        )
