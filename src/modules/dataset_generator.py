import chess.pgn
import pandas as pd
from ..modules.report_utils import generate_features_from_game

def generate_training_data_from_pgn(pgn_path, output_csv):
    rows = []
    with open(pgn_path, encoding="utf-8") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            game_rows = generate_features_from_game(game)
            rows.extend(game_rows)

    df = pd.DataFrame(rows)
    df.to_csv(output_csv, index=False)
    print(f"✅ Dataset generado: {output_csv}")