import os
import chess
import pandas as pd
from tqdm import tqdm
from stockfish_engine import StockfishEngine


class GamesAnalyzer:
    def __init__(self):
        self.engine = StockfishEngine(
            stockfish_path="/usr/local/bin/stockfish",
            depth=10
        )  # Adjust path

    def load_games(self, games_path):
        if isinstance(games_path, str):
            if not os.path.exists(games_path):
                print(f"Error: El archivo {games_path} no existe")
                return []
            with open(games_path, encoding="utf-8") as f:
                games = []
                while game := chess.pgn.read_game(f):
                    games.append(game)
                return games
        elif isinstance(games_path, list):
            result = []
            for path in games_path:
                if not os.path.exists(path):
                    print(f"Error: El archivo {path} no existe")
                    continue
                with open(path, encoding="utf-8") as f:
                    while game := chess.pgn.read_game(f):
                        result.append(game)
            return result
        else:
            raise ValueError("games_path must be a string (single path) or a list of paths")

    def analyze_game(self, game, player_name):
        board = game.board()  # Start from the initial position
        moves = []
        previous_score = None
        for node in game.mainline():
            move = node.move
            if not board.is_pseudo_legal(move):  # Optional: Add validation
                print(f"Invalid move {move.uci()} in position {board.fen()}")
                break
            board.push(move)
            score = self.engine.evaluate_position(board)
            is_blunder = False
            is_critical = False
            is_inaccurate = False
            is_mistake = False
            is_best_move = False
            if previous_score is not None:
                match abs(score - previous_score):
                    case diff if diff > 300:
                        is_blunder = True
                    case diff if diff > 100:
                        is_critical = True
                    case diff if diff > 50:
                        is_inaccurate = True
                    case diff if diff > 20:
                        is_mistake = True
                    case diff if diff < 20:
                        is_best_move = True
                
            moves.append({"fen": board.fen(),
                          "move": move.uci(), 
                          "score": score, 
                          "is_blunder": is_blunder,
                          "is_critical": is_critical,
                          "is_inaccurate": is_inaccurate,
                          "is_mistake": is_mistake,
                          "is_best_move": is_best_move
                        })
            previous_score = score
        df = pd.DataFrame(moves)
        summary = {
            "player": player_name,
            "total_moves": len(moves),
            "blunders": len(df[df["is_blunder"]])
        }
        return df, summary
    
    def generate_report(self, df):
        report = f"Reporte para {df['move'].count()} movimientos:\n"
        report += f"Blunders detectados: {len(df[df['is_blunder']])}\n"
        return report

    def save_report(self, game_path, report, player_name, platform):
        os.makedirs("data/reports", exist_ok=True)
        report_path = f"data/reports/{player_name}_{platform}_report.txt"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Reporte guardado en {report_path}")

    def analyze_multiple_games(self, games, platform="chesscom"):
        player_name = "chess_trainer_user"
        all_dfs = []
        total_blunders = 0
        total_moves = 0
        for game in tqdm(games, desc="Analyzing games"):
            print(f"Analizando partida: {game}")
            df, summary = self.analyze_game(game, player_name)
            total_blunders += summary["blunders"]
            total_moves += summary["total_moves"]
            all_dfs.append(df)
            report = self.generate_report(df)
            self.save_report(game, report, player_name, platform)
            combined_df = pd.concat(all_dfs, ignore_index=True)
            summary = {
                "total_games": len(games),
                "total_blunders": total_blunders,
                "total_moves": total_moves
            }
            return combined_df, summary

    def close(self):
        self.engine.close()

