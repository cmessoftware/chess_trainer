import chess
import chess.pgn
import io
from modules.utils import show_spinner_message

def detect_tags_from_game(pgn):
    tags = []
    game = chess.pgn.read_game(io.StringIO(pgn))
    if not game:
        return tags

    show_spinner_message("🔍 Detecting tags...")

    board = game.board()
    move_count = 0
    sacrifice_detected = False
    king_attacked = False
    trapped_piece_found = False
    blocked_piece_found = False
    overloaded_found = False

    for move in game.mainline_moves():
        move_count += 1

        if board.is_capture(move):
            captured_square = move.to_square
            if board.is_attacked_by(not board.turn, captured_square):
                sacrifice_detected = True

        # Detectar si el rey está siendo atacado
        king_square = board.king(board.turn)
        if king_square and board.is_attacked_by(not board.turn, king_square):
            king_attacked = True

        # Posiciones antes del movimiento
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == board.turn:
                legal_moves = [m for m in board.legal_moves if m.from_square == square]
                # Pieza bloqueada
                if not legal_moves:
                    blocked_piece_found = True
                else:
                    # Pieza encerrada: todos sus movimientos terminan en casillas atacadas
                    all_under_attack = all(board.is_attacked_by(not board.turn, m.to_square) for m in legal_moves)
                    if all_under_attack:
                        trapped_piece_found = True

        # Detectar piezas sobrecargadas (simplificado): defensor de múltiples piezas atacadas
        attacked = [sq for sq in chess.SQUARES if board.is_attacked_by(not board.turn, sq)]
        for sq in attacked:
            defenders = board.attackers(board.turn, sq)
            if defenders:
                for defender in defenders:
                    covers = [t for t in attacked if defender in board.attackers(board.turn, t)]
                    if len(covers) > 1:
                        overloaded_found = True
                        break

        board.push(move)

    if move_count <= 20:
        tags.append("short")
    if move_count > 30 and board.is_game_over():
        tags.append("endgame")
    if sacrifice_detected:
        tags.append("sacrifice")
    if king_attacked:
        tags.append("attack_king")
    if trapped_piece_found:
        tags.append("trapped")
    if blocked_piece_found:
        tags.append("blocked")
    if overloaded_found:
        tags.append("overloaded")

    return list(set(tags))  # eliminar duplicados si hay
