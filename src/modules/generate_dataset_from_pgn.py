
import chess.pgn
import pandas as pd
import chess

def extract_features_from_position(board, move):
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3.25, chess.ROOK: 5, chess.QUEEN: 9}

    # Material balance
    balance = 0
    total = 0
    num_pieces = 0
    for piece in board.piece_map().values():
        val = values.get(piece.piece_type, 0)
        total += val
        if piece.piece_type != chess.PAWN and piece.piece_type != chess.KING:
            num_pieces += 1
        balance += val if piece.color == chess.WHITE else -val

    # Phase of game
    piece_count = len(board.piece_map())
    if piece_count >= 24:
        phase = "opening"
    elif piece_count >= 12:
        phase = "middlegame"
    else:
        phase = "endgame"

    # Branching factor
    self_mobility = len(board.legal_moves)
    board.push(move)
    opponent_mobility = len(board.legal_moves)
    board.pop()

    return {
        "fen": board.fen(),
        "move_san": board.san(move),
        "move_uci": move.uci(),
        "material_balance": balance,
        "material_total": total,
        "num_pieces": num_pieces,
        "branching_factor": self_mobility + opponent_mobility,
        "self_mobility": self_mobility,
        "opponent_mobility": opponent_mobility,
        "phase": phase,
        "player_color": "white" if board.turn else "black",
        "has_castling_rights": int(board.has_castling_rights()),
        "move_number": board.fullmove_number,
        "is_repetition": int(board.is_repetition())
    }

def generate_dataset_from_pgn(pgn_file, output_csv, limit_games=None):
    data = []
    with open(pgn_file, "r", encoding="utf-8") as f:
        game_count = 0
        while True:
            game = chess.pgn.read_game(f)
            if game is None or (limit_games and game_count >= limit_games):
                break

            board = game.board()
            for move in game.mainline_moves():
                row = extract_features_from_position(board, move)
                data.append(row)
                board.push(move)

            game_count += 1
            if game_count % 50 == 0:
                print(f"{game_count} partidas procesadas...")

    df = pd.DataFrame(data)
    df.to_csv(output_csv, index=False)
    print(f"Dataset generado: {output_csv}")

# Ejemplo de uso:
# generate_dataset_from_pgn("partidas.pgn", "jugadas_dataset.csv", limit_games=100)
