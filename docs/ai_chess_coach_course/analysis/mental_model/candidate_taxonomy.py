"""Classify candidate moves into D1–D5 human categories."""

from __future__ import annotations

import chess

from analysis.mental_model.models import CandidateCategory


def classify_candidate_move(board: chess.Board, move: chess.Move) -> CandidateCategory:
    """Heuristic D1–D5 for a legal move in `board`."""
    if board.is_capture(move) or board.gives_check(move):
        return CandidateCategory.FORCING

    if _creates_threat(board, move):
        return CandidateCategory.TACTICAL_THREAT

    if _is_pawn_break(board, move) or _improves_worst_piece(board, move):
        return CandidateCategory.ACTIVE

    if _blocks_opponent_plan(board, move):
        return CandidateCategory.PROPHYLACTIC

    return CandidateCategory.POSITIONAL


def sort_candidates_by_priority(
    board: chess.Board,
    moves: list[chess.Move],
) -> list[tuple[chess.Move, CandidateCategory]]:
    """Order per rule F: forcing → active → solid (prophylactic/positional)."""
    priority = {
        CandidateCategory.FORCING: 0,
        CandidateCategory.TACTICAL_THREAT: 1,
        CandidateCategory.ACTIVE: 2,
        CandidateCategory.PROPHYLACTIC: 3,
        CandidateCategory.POSITIONAL: 4,
    }
    tagged = [(move, classify_candidate_move(board, move)) for move in moves]
    return sorted(tagged, key=lambda item: priority[item[1]])


def _creates_threat(board: chess.Board, move: chess.Move) -> bool:
    trial = board.copy()
    trial.push(move)
    opponent = not board.turn
    for sq in chess.SQUARES:
        piece = trial.piece_at(sq)
        if piece and piece.color == opponent and piece.piece_type != chess.KING:
            if trial.is_attacked_by(board.turn, sq):
                return True
    return False


def _is_pawn_break(board: chess.Board, move: chess.Move) -> bool:
    piece = board.piece_at(move.from_square)
    if not piece or piece.piece_type != chess.PAWN:
        return False
    return chess.square_file(move.from_square) in (2, 3, 4, 5)


def _improves_worst_piece(board: chess.Board, move: chess.Move) -> bool:
    piece = board.piece_at(move.from_square)
    return piece is not None and piece.piece_type in (chess.KNIGHT, chess.BISHOP, chess.ROOK)


def _blocks_opponent_plan(board: chess.Board, move: chess.Move) -> bool:
    trial = board.copy()
    trial.push(move)
    return trial.is_check() is False and not board.is_capture(move)
