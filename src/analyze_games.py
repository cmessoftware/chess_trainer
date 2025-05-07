import os
import chess.pgn
import pandas as pd
from stockfish_engine import StockfishEngine
from sqlalchemy import create_engine

def analyze_game(pgn_file, player_name):
    engine = StockfishEngine()
    game = chess.pgn.read_game(open(pgn_file))
    board = game.board()
    moves_data = []

    for move in game.mainline_moves():
        board.push(move)
        score = engine.evaluate_position(board)
        best_move = engine.get_best_move(board)
        is_blunder = abs(score) > 300  # Umbral para considerar un error grave
        moves_data.append({
            "move": move.uci(),
            "score": score,
            "best_move": best_move.uci(),
            "is_blunder": is_blunder,
            "player": player_name
        })

    engine.close()
    return pd.DataFrame(moves_data)

def generate_report(df):
    """Genera un informe con métricas."""
    blunder_rate = df["is_blunder"].mean() * 100
    avg_score = df["score"].mean()
    report = {
        "blunder_rate": blunder_rate,
        "avg_score": avg_score,
        "total_moves": len(df)
    }
    return report

def analyze_multiple_games(game_files, platform):
    results = []
    for player_name, pgn_file in game_files:
        if os.path.exists(pgn_file):
            df = analyze_game(pgn_file, player_name)
            report = generate_report(df)
            save_report(report, player_name, pgn_file, platform)
            results.append((player_name, report))
        else:
            print(f"Archivo no encontrado: {pgn_file}")
    return results

def save_report(report, player_name, pgn_file, platform):
    engine = create_engine("sqlite:///data/games.db")
    pd.DataFrame([{
        "player_name": player_name,
        "pgn_file": pgn_file,
        "blunder_rate": report["blunder_rate"],
        "avg_score": report["avg_score"],
        "platform": platform,
        "date_analyzed": pd.Timestamp.now()
    }]).to_sql("games", engine, if_exists="append", index=False)