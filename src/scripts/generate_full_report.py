# Extracción posicional
# Evaluación con Stockfish
# Etiquetado de jugadas
# Guardado acumulativo del dataset

import os
import chess.pgn
import pandas as pd
import chess
import chess.engine

import dotenv
import argparse
dotenv.load_dotenv()  # Carga las variables del archivo .env

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH", "/usr/local/bin/stockfish")

if not STOCKFISH_PATH or not os.path.exists(STOCKFISH_PATH):
    raise FileNotFoundError(f"❌ Stockfish executable not found at: {STOCKFISH_PATH}")

def extract_features_from_position(board, move):
    values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3.25, chess.ROOK: 5, chess.QUEEN: 9}
    balance = 0
    total = 0
    num_pieces = 0
    for piece in board.piece_map().values():
        val = values.get(piece.piece_type, 0)
        total += val
        if piece.piece_type != chess.PAWN and piece.piece_type != chess.KING:
            num_pieces += 1
        balance += val if piece.color == chess.WHITE else -val

    piece_count = len(board.piece_map())
    phase = "opening" if piece_count >= 24 else "middlegame" if piece_count >= 12 else "endgame"
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

def save_dataframe_accumulative(df, path="training_dataset.csv"):
    df.to_csv(
        path,
        mode="a",
        index=False,
        header=not os.path.exists(path)
    )

def generate_full_report(pgn_path, output_csv="training_dataset.csv", limit_games=None, depth=12):
    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    data = []
    with open(pgn_path, "r", encoding="utf-8") as f:
        game_count = 0
        while True:
            game = chess.pgn.read_game(f)
            if game is None or (limit_games and game_count >= limit_games):
                break

            board = game.board()
            for move in game.mainline_moves():
                info_before = engine.analyse(board, chess.engine.Limit(depth=depth))
                score_before = info_before["score"].white().score(mate_score=10000)

                features = extract_features_from_position(board, move)

                board.push(move)

                info_after = engine.analyse(board, chess.engine.Limit(depth=depth))
                score_after = info_after["score"].white().score(mate_score=10000)

                score_diff = (score_before or 0) - (score_after or 0)
                features["score_diff"] = score_diff

                if score_diff >= 200:
                    features["error_label"] = "blunder"
                elif score_diff >= 100:
                    features["error_label"] = "mistake"
                elif score_diff <= -50:
                    features["error_label"] = "best_move"
                else:
                    features["error_label"] = "neutral"

                data.append(features)

            game_count += 1
            if game_count % 10 == 0:
                print(f"Procesadas {game_count} partidas...")

    engine.quit()
    df = pd.DataFrame(data)
    save_dataframe_accumulative(df, output_csv)
    print(f"✅ Dataset generado/acumulado: {output_csv}")


    if __name__ == "__main__":

        parser = argparse.ArgumentParser(description="Generate chess report dataset from PGN.")
        parser.add_argument("pgn_path", help="Path to the PGN file")
        parser.add_argument("--output_csv", default="training_dataset.csv", help="Output CSV file")
        parser.add_argument("--limit_games", type=int, default=None, help="Limit number of games to process")
        parser.add_argument("--depth", type=int, default=12, help="Stockfish analysis depth")

        args = parser.parse_args()

        generate_full_report(
            pgn_path=args.pgn_path,
            output_csv=args.output_csv,
            limit_games=args.limit_games,
            depth=args.depth
        )