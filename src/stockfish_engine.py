import chess
import chess.engine

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