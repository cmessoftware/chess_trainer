# commentator.py

import chess


def is_tactical_capture(board, move):
    if board.is_capture(move):
        piece = board.piece_at(move.to_square)
        if piece:
            return piece.piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]
    return False

def comment_move(board, move, move_number):
    comments = []

    if board.is_capture(move):
        if is_tactical_capture(board, move):
            comments.append("Captura táctica importante.")
        else:
            comments.append("Captura de menor valor.")

    if board.is_check():
        comments.append("Jaque, mantiene la presión.")

    if move_number >= 10 and board.fullmove_number <= 10:
        if not board.has_castling_rights(board.turn) and board.king(board.turn):
            comments.append("Rey aún en el centro, puede ser riesgoso.")

    return " ".join(comments).strip()
