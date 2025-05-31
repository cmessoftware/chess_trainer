

import os
import chess
import dotenv
env = dotenv.load_dotenv()

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")


def analyze_critical_moves(game, depth=15, threshold=0.5):
    engine, d = get_engine(depth)
    board = game.board()
    feedback = []

    prev_eval = evaluate(board, engine, d)
    move_number = 1

    for move in game.mainline_moves():
        board.push(move)
        new_eval = evaluate(board, engine, d)
        diff = abs(new_eval - prev_eval)

        if diff >= threshold:
            error_type = (
                "Blunder" if diff >= 2.0 else
                "Mistake" if diff >= 1.0 else
                "Inaccuracy"
            )
            bm = best_move(board, engine, d)
            feedback.append({
                "move_number": move_number,
                "san": board.san(move),
                "eval_before": prev_eval,
                "eval_after": new_eval,
                "eval_diff": diff,
                "type": error_type,
                "suggestion": bm.uci() if bm else "N/A"
            })

        prev_eval = new_eval
        move_number += 1

    engine.quit()
    return feedback

def get_engine(depth=15):
    return chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH), depth

def get_evaluation(fen, depth=15):
    with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
        board = chess.Board(fen)
        info = engine.analyse(board, chess.engine.Limit(depth=depth))
        score = info["score"].relative

        if score.is_mate():
            return {"score": 10000 if score.mate() > 0 else -10000, "mate_in": score.mate()}
        else:
            return {"score": score.score(), "mate_in": None}

def evaluate(board, engine, depth):
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    return info["score"].relative.score(mate_score=10000) / 100.0

def best_move(board, engine, depth):
    result = engine.play(board, chess.engine.Limit(depth=depth))
    return result.move
