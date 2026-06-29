"""Board reconstruction and chess helpers for diagnosis."""

from __future__ import annotations

import chess

PIECE_NAMES_ES: dict[int, str] = {
    chess.PAWN: "peón",
    chess.KNIGHT: "caballo",
    chess.BISHOP: "alfil",
    chess.ROOK: "torre",
    chess.QUEEN: "dama",
    chess.KING: "rey",
}

PIECE_VALUES: dict[int, int] = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 100,
}


def build_board_at_ply(sans: list[str], ply: int) -> chess.Board | None:
    board = chess.Board()
    limit = min(max(ply, 0), len(sans))
    for index in range(limit):
        try:
            board.push(board.parse_san(sans[index]))
        except (chess.InvalidMoveError, chess.AmbiguousMoveError, ValueError):
            return None
    return board


def piece_label_es(piece_type: chess.PieceType, square: int | None = None) -> str:
    name = PIECE_NAMES_ES.get(piece_type, "pieza")
    if square is not None and piece_type == chess.PAWN:
        return f"peón en {chess.square_name(square)}"
    if square is not None:
        return f"{name} en {chess.square_name(square)}"
    return name


def attacked_undefended(
    board: chess.Board,
    color: chess.Color,
    *,
    min_value: int = 1,
) -> list[tuple[int, chess.Piece]]:
    opponent = not color
    found: list[tuple[int, chess.Piece]] = []
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None or piece.color != color:
            continue
        if piece.piece_type == chess.KING:
            continue
        if PIECE_VALUES.get(piece.piece_type, 0) < min_value:
            continue
        if board.is_attacked_by(opponent, square) and not board.is_attacked_by(color, square):
            found.append((square, piece))
    return found


def material_balance(board: chess.Board, color: chess.Color) -> int:
    total = 0
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        value = PIECE_VALUES.get(piece.piece_type, 0)
        total += value if piece.color == color else -value
    return total


def is_pawn_push_san(san: str) -> bool:
    text = str(san).strip()
    if not text or text.startswith("O-O"):
        return False
    return text[0].islower()


def is_rook_move_san(san: str) -> bool:
    text = str(san).strip()
    return text.startswith("R") or text.startswith("r")
