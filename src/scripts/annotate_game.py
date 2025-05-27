# chess_trainer/tools/annotate_game.py

import chess.pgn
import chess.engine
from io import StringIO
from stockfish import Stockfish

def annotate_game(pgn_text: str, stockfish_path: str = "/usr/bin/stockfish", depth: int = 15):
    # Cargar PGN
    pgn_io = StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)

    stockfish = Stockfish(stockfish_path, parameters={"Threads": 2, "Minimum Thinking Time": 30})
    
    board = game.board()
    annotated_game = chess.pgn.Game()
    node = annotated_game

    for move in game.mainline_moves():
        board.push(move)
        stockfish.set_fen_position(board.fen())
        info = stockfish.get_evaluation()

        comment = generate_comment(info, board, move)
        node = node.add_main_variation(move)
        node.comment = comment

    return annotated_game

def generate_comment(info, board, move):
    score = info.get("value", 0)
    if info["type"] == "mate":
        return f"Mate en {info['value']} jugadas."
    elif abs(score) > 100:
        return f"{'Buena' if score > 0 else 'Mala'} jugada. Eval: {score / 100:.2f}"
    else:
        return f"Jugadas parejas. Eval: {score / 100:.2f}"

# Guardar a PGN
def save_annotated_game(game, output_path="annotated_game.pgn"):
    with open(output_path, "w", encoding="utf-8") as f:
        print(game, file=f)

# Uso
if __name__ == "__main__":
    with open("games/cmess1315_vs_lukeharuki.pgn", "r", encoding="utf-8") as file:
        raw_pgn = file.read()

    annotated = annotate_game(raw_pgn, stockfish_path="/path/to/stockfish")
    save_annotated_game(annotated)
