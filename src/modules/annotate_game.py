# annotate_game.py
import chess
from modules.stockfish_utils import get_engine, evaluate, best_move
from modules.commentator import comment_move  # si usás commentator como complemento

def annotate_game(game, use_stockfish=True, use_commentator=False, stockfish_depth=15):
    board = game.board()
    node = game
    engine = None

    if use_stockfish:
        engine, depth = get_engine(stockfish_depth)

    for move in game.mainline_moves():
        node = node.add_variation(move)
        board.push(move)
        comments = []

        if use_stockfish and engine:
            eval_score = evaluate(board, engine, stockfish_depth)
            best = best_move(board, engine, stockfish_depth)
            comments.append(f"Eval ≈ {eval_score:+.2f}. Best move: {best.uci() if best else 'N/A'}")

        if use_commentator:
            c = comment_move(board.copy(stack=False), move, board.fullmove_number)
            if c:
                comments.append(c)

        if comments:
            node.comment = " ".join(comments)

    if engine:
        engine.quit()

    return game
