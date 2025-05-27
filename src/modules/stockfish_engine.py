import chess
import chess.engine
import chess.pgn
import io


class StockfishEngine:
    def __init__(self, stockfish_path="/usr/local/bin/stockfish", depth=15):
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.depth = depth

    def evaluate_position(self, board):
        """Evalúa una posición y retorna la puntuación en centipawns."""
        info = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
        score = info["score"].relative.score(mate_score=10000)  # Puntuación en centipawns
        return score

    def get_best_move(self, board):
        """Obtiene el mejor movimiento para una posición."""
        result = self.engine.play(board, chess.engine.Limit(depth=self.depth))
        return result.move

    def close(self):
        """Cierra el motor."""
        self.engine.quit()

    def evaluate_game(self, pgn_text):
        # Parse the PGN file to extract moves and game information
        pgn = io.StringIO(pgn_text)
        game = chess.pgn.read_game(pgn)
        board = game.board()
        time_limit = 0.1  # Time limit for engine analysis in seconds

       
        critical_moments = []
        move_number = 0
       
        for move in game.mainline_moves():
            move_number += 1
            # Evaluate position before the move
            info = self.engine.analyse(board, chess.engine.Limit(time=time_limit))
            curr_eval = info["score"].relative.score(mate_score=10000) / 100.0  # Convert to centipawns

            # Push the move to the board
            board.push(move)

            # Evaluate position after the move
            info_after = self.engine.analyse(board, chess.engine.Limit(time=time_limit))
            best_move = info_after["pv"][0] if "pv" in info_after else None
            eval_after = info_after["score"].relative.score(mate_score=10000) / 100.0

            # Adjust evaluations for side to move (White: positive is good; Black: negative is good)
            if board.turn == chess.BLACK:  # Black's turn before move
                curr_eval = -curr_eval
                eval_after = -eval_after

            # Detect errors based on evaluation difference
            eval_diff = curr_eval - eval_after
            error_type = None
            if eval_diff >= 2.0:
                error_type = "Blunder"
            elif eval_diff >= 1.0:
                error_type = "Mistake"
            elif eval_diff >= 0.5:
                error_type = "Inaccuracy"

            # Flag critical moves (large evaluation swings or errors)
            if error_type or abs(curr_eval - eval_after) > 2.0:
                description = f"{error_type or 'Critical move'}: Evaluation changed from {curr_eval:.2f} to {eval_after:.2f}."
                suggestion = f"Best move: {best_move.uci() if best_move else 'N/A'} (Eval: {curr_eval:.2f})."

                # Check for pawn structure changes (basic heuristic)
                if board.is_capture(move) or board.is_zeroing(move):
                    description += " Move affects pawn structure."
                    suggestion += " Consider pawn structure implications."

                critical_moments.append({
                    "move": move_number // 2 + (1 if move_number % 2 else 0),
                    "description": description,
                    "suggestion": suggestion
                })

        # Close the engine
        self.engine.quit()
        return critical_moments

    