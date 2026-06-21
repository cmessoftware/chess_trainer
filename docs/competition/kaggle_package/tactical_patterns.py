"""Board-pattern tactical tags (no engine) for competition enrichment."""

from __future__ import annotations

import chess


def is_fork(board: chess.Board, move: chess.Move) -> bool:
    piece = board.piece_at(move.from_square)
    if not piece or piece.piece_type != chess.KNIGHT:
        return False

    board.push(move)
    attacked = list(board.attacks(move.to_square))
    valuable_targets = [
        sq
        for sq in attacked
        if board.piece_at(sq)
        and board.piece_at(sq).piece_type in (chess.QUEEN, chess.ROOK)
    ]
    board.pop()
    return len(valuable_targets) >= 2


def is_pin(board: chess.Board, move: chess.Move) -> bool:
    board.push(move)
    result = False
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece and piece.color != board.turn and board.is_pinned(not board.turn, sq):
            result = True
            break
    board.pop()
    return result


def is_discovered_attack(board: chess.Board, move: chess.Move) -> bool:
    attacker_color = board.turn
    board.push(move)
    result = any(
        board.piece_at(sq)
        and board.piece_at(sq).color != attacker_color
        and board.is_attacked_by(attacker_color, sq)
        for sq in chess.SQUARES
    )
    board.pop()
    return result


def classify_move_pattern(board: chess.Board, move: chess.Move) -> str | None:
    if board.is_checkmate():
        return "mate"
    if board.gives_check(move):
        return "check"
    if is_fork(board, move):
        return "fork"
    if is_pin(board, move):
        return "pin"
    if is_discovered_attack(board, move):
        return "discovered_attack"
    return None


def parse_move(board: chess.Board, *, move_uci: str | None, move_san: str | None) -> chess.Move | None:
    if move_uci:
        try:
            move = chess.Move.from_uci(move_uci.strip())
            if move in board.legal_moves:
                return move
        except ValueError:
            pass

    if move_san:
        try:
            return board.parse_san(move_san.strip())
        except ValueError:
            return None

    return None


def detect_pattern_from_row(
    *,
    fen: str | None,
    move_uci: str | None,
    move_san: str | None,
) -> str:
    if not fen:
        return "normal"

    try:
        board = chess.Board(fen)
    except ValueError:
        return "normal"

    move = parse_move(board, move_uci=move_uci, move_san=move_san)
    if move is None:
        return "normal"

    return classify_move_pattern(board, move) or "normal"
