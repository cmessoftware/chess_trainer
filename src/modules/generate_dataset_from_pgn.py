
import chess.pgn
import pandas as pd
import chess

from modules.report_utils import extract_features_from_position


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
