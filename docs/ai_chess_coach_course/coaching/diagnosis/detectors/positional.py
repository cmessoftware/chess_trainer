"""Positional / strategic pattern detectors."""

from __future__ import annotations

import chess

from coaching.diagnosis.base import PatternDetector
from coaching.diagnosis.board_utils import is_rook_move_san, piece_label_es
from coaching.diagnosis.models import DiagnosisContext, PatternMatch


class KingSafetyDetector(PatternDetector):
    pattern_id = "king_safety"

    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        if context.cp_loss < 500:
            return None
        king_square = context.after_player_board.king(context.player_color)
        before_king = context.before_board.king(context.player_color)
        opponent = not context.player_color
        before_attacks = sum(
            1
            for sq in chess.SQUARES
            if context.before_board.is_attacked_by(opponent, sq)
            and chess.square_distance(before_king, sq) <= 2
        )
        after_attacks = sum(
            1
            for sq in chess.SQUARES
            if context.after_player_board.is_attacked_by(opponent, sq)
            and chess.square_distance(king_square, sq) <= 2
        )
        if after_attacks <= before_attacks + 1:
            return None
        return PatternMatch(
            pattern_id=self.pattern_id,
            confidence=0.78,
            tactical_motif="king exposure",
            affected_piece=f"rey en {chess.square_name(king_square)}",
            affected_square=chess.square_name(king_square),
            strategic_theme="king_safety",
        )


class PassiveRookDetector(PatternDetector):
    pattern_id = "passive_rook"

    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        if not is_rook_move_san(context.player_move_san):
            return None
        board = context.after_player_board
        move = board.peek()
        piece = board.piece_at(move.to_square)
        if piece is None or piece.piece_type != chess.ROOK:
            return None
        attackers = board.attackers(context.player_color, move.to_square)
        mobility = sum(
            1
            for target in chess.SQUARES
            if board.is_attacked_by(context.player_color, target)
            and board.piece_at(target) is None
        )
        if mobility >= 4:
            return None
        return PatternMatch(
            pattern_id=self.pattern_id,
            confidence=0.72,
            tactical_motif="passive rook",
            affected_piece=piece_label_es(chess.ROOK, move.to_square),
            affected_square=chess.square_name(move.to_square),
            strategic_theme="piece_activity",
        )
