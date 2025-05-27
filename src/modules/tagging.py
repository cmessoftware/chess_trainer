import chess.pgn
import io

def detect_tags_from_game(pgn):
    tags = []
    game = chess.pgn.read_game(io.StringIO(pgn))
    if not game:
        return tags

    board = game.board()
    move_count = 0
    sacrifice_detected = False
    king_attacked = False

    for move in game.mainline_moves():
        move_count += 1
        if board.is_capture(move):
            captured_square = move.to_square
            if board.is_attacked_by(not board.turn, captured_square):
                sacrifice_detected = True
        if board.king(board.turn) in board.attacks(move.to_square):
            king_attacked = True
        board.push(move)

    if move_count <= 20:
        tags.append("short")
    if sacrifice_detected:
        tags.append("sacrifice")
    if king_attacked:
        tags.append("attack_king")
    if move_count > 30 and board.is_game_over():
        tags.append("endgame")

    return tags
