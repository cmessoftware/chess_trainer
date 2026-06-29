"""Board-based tactical pattern detectors."""

from __future__ import annotations

import chess

from coaching.diagnosis.base import PatternDetector
from coaching.diagnosis.board_utils import (
    PIECE_VALUES,
    attacked_undefended,
    is_pawn_push_san,
    piece_label_es,
)
from coaching.diagnosis.models import DiagnosisContext, PatternMatch


def _newly_vulnerable(
    before: chess.Board,
    after: chess.Board,
    color: chess.Color,
) -> list[tuple[int, chess.Piece]]:
    before_set = {sq for sq, _ in attacked_undefended(before, color)}
    return [item for item in attacked_undefended(after, color) if item[0] not in before_set]


class HangingPieceDetector(PatternDetector):
    pattern_id = "hanging_piece"

    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        vulnerable = _newly_vulnerable(
            context.before_board,
            context.after_player_board,
            context.player_color,
        )
        if not vulnerable:
            return None
        square, piece = max(vulnerable, key=lambda item: PIECE_VALUES.get(item[1].piece_type, 0))
        return PatternMatch(
            pattern_id=self.pattern_id,
            confidence=0.9,
            tactical_motif="piece left en prise",
            affected_piece=piece_label_es(piece.piece_type, square),
            affected_square=chess.square_name(square),
        )


class UndefendedPawnDetector(PatternDetector):
    pattern_id = "undefended_pawn"

    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        if not is_pawn_push_san(context.player_move_san):
            return None
        pawns = [
            (sq, piece)
            for sq, piece in _newly_vulnerable(
                context.before_board,
                context.after_player_board,
                context.player_color,
            )
            if piece.piece_type == chess.PAWN
        ]
        if not pawns:
            pawns = [
                (sq, piece)
                for sq, piece in attacked_undefended(context.after_player_board, context.player_color)
                if piece.piece_type == chess.PAWN
            ]
        if not pawns:
            return None
        square, _ = pawns[0]
        return PatternMatch(
            pattern_id=self.pattern_id,
            confidence=0.88,
            tactical_motif="undefended pawn",
            affected_piece=piece_label_es(chess.PAWN, square),
            affected_square=chess.square_name(square),
        )


class LoosePieceAfterPawnPushDetector(PatternDetector):
    pattern_id = "loose_piece_after_pawn_push"

    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        if not is_pawn_push_san(context.player_move_san):
            return None
        non_pawns = [
            (sq, piece)
            for sq, piece in _newly_vulnerable(
                context.before_board,
                context.after_player_board,
                context.player_color,
            )
            if piece.piece_type != chess.PAWN
        ]
        if not non_pawns:
            return None
        square, piece = max(non_pawns, key=lambda item: PIECE_VALUES.get(item[1].piece_type, 0))
        return PatternMatch(
            pattern_id=self.pattern_id,
            confidence=0.86,
            tactical_motif="piece lost defenders after pawn push",
            affected_piece=piece_label_es(piece.piece_type, square),
            affected_square=chess.square_name(square),
        )


class ForkDetector(PatternDetector):
    pattern_id = "fork"

    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        if context.after_opponent_board is None or context.root_ply + 1 >= len(context.sans):
            return None
        board = context.after_player_board.copy()
        try:
            move = board.parse_san(context.sans[context.root_ply + 1])
        except (chess.InvalidMoveError, chess.AmbiguousMoveError, ValueError):
            return None
        board.push(move)
        opponent = not context.player_color
        attacked: list[tuple[int, chess.Piece]] = []
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == context.player_color and piece.piece_type != chess.KING:
                if board.is_attacked_by(opponent, square):
                    attacked.append((square, piece))
        valuable = [
            item for item in attacked if PIECE_VALUES.get(item[1].piece_type, 0) >= PIECE_VALUES[chess.KNIGHT]
        ]
        if len(valuable) < 2:
            return None
        return PatternMatch(
            pattern_id=self.pattern_id,
            confidence=0.92,
            tactical_motif="double attack",
            affected_piece=f"{piece_label_es(valuable[0][1].piece_type, valuable[0][0])} y {piece_label_es(valuable[1][1].piece_type, valuable[1][0])}",
            details={"targets": [chess.square_name(sq) for sq, _ in valuable[:2]]},
        )


class PinDetector(PatternDetector):
    pattern_id = "pin"

    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        board = context.after_opponent_board or context.after_player_board
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.color != context.player_color:
                continue
            if piece.piece_type in (chess.KING, chess.PAWN):
                continue
            if board.is_pinned(context.player_color, square):
                return PatternMatch(
                    pattern_id=self.pattern_id,
                    confidence=0.84,
                    tactical_motif="pin",
                    affected_piece=piece_label_es(piece.piece_type, square),
                    affected_square=chess.square_name(square),
                )
        return None


class SkewerDetector(PatternDetector):
    pattern_id = "skewer"

    def detect(self, context: DiagnosisContext) -> PatternMatch | None:
        if context.after_opponent_board is None:
            return None
        board = context.after_opponent_board
        opponent = not context.player_color
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.color != context.player_color:
                continue
            if not board.is_attacked_by(opponent, square):
                continue
            if board.is_pinned(context.player_color, square) and piece.piece_type in (
                chess.QUEEN,
                chess.ROOK,
            ):
                return PatternMatch(
                    pattern_id=self.pattern_id,
                    confidence=0.82,
                    tactical_motif="skewer",
                    affected_piece=piece_label_es(piece.piece_type, square),
                    affected_square=chess.square_name(square),
                )
        return None
