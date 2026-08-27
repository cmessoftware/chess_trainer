"""S1–S4 anti-blunder checks before playing a candidate move."""

from __future__ import annotations

import chess

from coaching.diagnosis.board_utils import PIECE_VALUES, attacked_undefended
from analysis.mental_model.models import AntiBlunderCheck


def run_anti_blunder_checks(board: chess.Board, move: chess.Move) -> list[AntiBlunderCheck]:
    """Simulate `move` for side to move and return failed check codes."""
    if move not in board.legal_moves:
        return [AntiBlunderCheck.S1_MAJOR_HANGING]

    player = board.turn
    trial = board.copy()
    trial.push(move)
    failed: list[AntiBlunderCheck] = []

    if trial.is_check():
        failed.append(AntiBlunderCheck.S2_IN_CHECK)

    major_hanging = [
        (sq, piece)
        for sq, piece in attacked_undefended(trial, player, min_value=5)
    ]
    if major_hanging:
        failed.append(AntiBlunderCheck.S1_MAJOR_HANGING)

    opponent = not player
    for opp_move in trial.legal_moves:
        if trial.is_capture(opp_move):
            captured = trial.piece_at(opp_move.to_square)
            if captured and PIECE_VALUES.get(captured.piece_type, 0) >= 5:
                failed.append(AntiBlunderCheck.S3_OBVIOUS_CAPTURE)
                break

    before_defenders = _defender_count(board, player)
    after_defenders = _defender_count(trial, player)
    if after_defenders < before_defenders - 1:
        failed.append(AntiBlunderCheck.S4_LOST_DEFENDER)

    return list(dict.fromkeys(failed))


def _defender_count(board: chess.Board, color: chess.Color) -> int:
    count = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.color == color and piece.piece_type in (chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT):
            if board.is_attacked_by(color, square):
                count += 1
    return count
