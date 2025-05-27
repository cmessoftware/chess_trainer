import chess
import chess.engine
import pandas as pd

STOCKFISH_PATH = "engines/stockfish"  # Cambiá esto según tu sistema

def evaluate_tactical_features(row, engine, depth=18):
    fen = row["fen"]
    move_uci = row["move_uci"]

    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            return pd.Series([None, None, None])

        # Score antes de mover
        info_before = engine.analyse(board, chess.engine.Limit(depth=depth))
        score_before = info_before["score"].relative.score(mate_score=10000)

        best_line = info_before.get("pv", [])
        is_forced = len(best_line) == 1

        # Aplicar jugada del jugador
        board.push(move)

        # Score después de mover
        info_after = engine.analyse(board, chess.engine.Limit(depth=depth))
        score_after = info_after["score"].relative.score(mate_score=10000)

        # ¿Amenaza mate?
        threatens_mate = info_after["score"].relative.mate() in [1, 2]

        return pd.Series([
            threatens_mate,
            is_forced,
            score_after - score_before
        ])

    except Exception as e:
        print(f"Error: {e}")
        return pd.Series([None, None, None])

def process_csv(input_file, output_file):
    df = pd.read_csv(input_file)
    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        results = df.apply(lambda row: evaluate_tactical_features(row, engine), axis=1)
        results.columns = ["threatens_mate", "is_forced_move", "depth_score_diff"]
        df = df.join(results)
        df.to_csv(output_file, index=False)
        print(f"Dataset enriquecido guardado en: {output_file}")

# Uso:
# process_csv("simulated_tactical_dataset.csv", "tactical_enriched.csv")
