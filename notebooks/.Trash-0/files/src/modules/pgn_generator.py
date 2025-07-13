import chess.pgn


def generate_pgn_from_moves(moves, starting_fen=None):
    game = chess.pgn.Game()
    if starting_fen:
        game.setup(chess.Board(starting_fen))
    node = game
    board = chess.Board(starting_fen) if starting_fen else chess.Board()
    for move in moves:
        move_obj = board.parse_san(move)
        board.push(move_obj)
        node = node.add_variation(move_obj)
    exporter = chess.pgn.StringExporter(
        headers=True, variations=False, comments=True)
    return game.accept(exporter)
