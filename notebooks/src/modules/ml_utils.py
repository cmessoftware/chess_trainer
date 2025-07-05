import chess


piece_to_index = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11
}

# Helper functions to convert FEN to tensor


def fen_to_tensor(fen):
    board = chess.Board(fen)
    board_tensor = np.zeros((13, 8, 8), dtype=np.float32)

    # Castling mapping
    castling_map = {'K': (7, 6), 'Q': (7, 2), 'k': (0, 6), 'q': (0, 2)}
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            row, col = 7 - chess.square_rank(square), chess.square_file(square)
            board_tensor[piece_to_index[piece.symbol()], row, col] = 1

    # FEN features
    fen_parts = fen.split()
    active_player = 1 if fen_parts[1] == 'w' else 0
    halfmove_clock = float(fen_parts[4]) / 100.0
    en_passant = fen_parts[3]
    castle_rights = fen_parts[2]

    # Encode en passant
    if en_passant != '-':
        row, col = 7 - (int(en_passant[1]) - 1), ord(en_passant[0]) - ord('a')
        board_tensor[12, row, col] = 1

    # Encode castling rights
    if castle_rights != '-':
        for right in castle_rights:
            row, col = castling_map[right]
            board_tensor[12, row, col] = 1

    return board_tensor, active_player, halfmove_clock
