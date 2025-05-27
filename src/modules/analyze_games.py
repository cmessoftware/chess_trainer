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
        
    def is_threatening_mate(board, played_move):
        board.push(played_move)
        result = None
        try:
            import chess.engine
            with chess.engine.SimpleEngine.popen_uci("engines/stockfish") as engine:
                info = engine.analyse(board, chess.engine.Limit(depth=10))
                score = info["score"].white().mate()
                result = True if score and score <= 2 else False
        except:
            result = False
        board.pop()
        return result

    def eval_material(board):
        values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3.25, chess.ROOK: 5, chess.QUEEN: 9}
        score = 0
        for piece in board.piece_map().values():
            value = values.get(piece.piece_type, 0)
            score += value if piece.color == chess.WHITE else -value
        return score

    def classify_phase(board):
        total_pieces = len(board.piece_map())
        if total_pieces >= 24:
            return "opening"
        elif total_pieces >= 12:
            return "middlegame"
        else:
            return "endgame"


    def analyze_game(self, game, player_name="chess_trainer_user"):
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
            "blunders": len(df[df["is_blunder"]]),
            "mistakes": len(df[df["is_mistake"]]),
            "inaccuracies": len(df[df["is_inaccurate"]]),
            "critical_moves": len(df[df["is_critical"]]),
            "best_moves": len(df[df["is_best_move"]]),
            "average_score": df["score"].mean(),
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
        total_mistakes = 0
        total_inaccuracies = 0
        total_critical_moves = 0
        total_best_moves = 0
        for game in tqdm(games, desc="Analyzing games"):
            print(f"Analizando partida: {game}")
            df, summary = self.analyze_game(game, player_name)
            total_blunders += summary["blunders"]
            total_moves += summary["total_moves"]
            total_best_moves += summary["best_moves"]
            total_mistakes += summary["mistakes"]
            total_inaccuracies += summary["inaccuracies"]
            total_critical_moves += summary["critical_moves"]
            all_dfs.append(df)
            report = self.generate_report(df)
            self.save_report(game, report, player_name, platform)
            combined_df = pd.concat(all_dfs, ignore_index=True)
            summary = {
                "total_games": len(games),
                "total_blunders": total_blunders,
                "total_moves": total_moves,
                "total_mistakes": total_mistakes,
                "total_inaccuracies": total_inaccuracies,
                "total_critical_moves": total_critical_moves,
                "total_best_moves": total_best_moves,
                "average_score": combined_df["score"].mean(),
                "average_blunders": total_blunders / len(games) if len(games) > 0 else 0,
                "average_mistakes": total_mistakes / len(games) if len(games) > 0 else 0,
                "average_inaccuracies": total_inaccuracies / len(games) if len(games) > 0 else 0,
                "average_critical_moves": total_critical_moves / len(games) if len(games) > 0 else 0,
                "average_best_moves": total_best_moves / len(games) if len(games) > 0 else 0,
                
            }
            return combined_df, summary

    def close(self):
        self.engine.close()
        
    def generate_training_plan(critical_moments):
        # Generate a training plan based on identified weaknesses
        plan = []
        for moment in critical_moments:
            if "Blunder" in moment["description"]:
                plan.append("Solve 20 tactical puzzles focusing on checks, captures, and threats.")
            if "Mistake" in moment["description"]:
                plan.append("Practice piece coordination in middlegame positions.")
            if "Inaccuracy" in moment["description"]:
                plan.append("Study best-move evaluations in similar positions.")
            if "pawn structure" in moment["description"].lower():
                plan.append("Study pawn structures in 'Pawn Structure Chess' by Andrew Soltis.")
        return list(set(plan))  # Remove duplicates


