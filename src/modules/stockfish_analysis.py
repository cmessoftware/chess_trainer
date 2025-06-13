

import os
import traceback
import chess
import dotenv
env = dotenv.load_dotenv()

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")

# TODO: Analizar donde usar este analisis, si en el juego o en el ejercicio


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


def get_evaluation(fen, depth=10, multipv=1):
    try:
        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            board = chess.Board(fen)
            info = engine.analyse(board, chess.engine.Limit(
                depth=depth), multipv=multipv)
            turn = board.turn
            if multipv == 1:
                print("Multipv is set to 1, returning single evaluation.")
                return parse_info(info, turn=board.turn)
            else:
                return {
                    "best": parse_info(info[0], turn),
                    "alternatives": [parse_info(i, turn) for i in info[1:]]
                } if multipv > 1 else {"best": parse_info(info, turn), "alternatives": []}
    except Exception as e:
        print(f"❌ Error al obtener evaluación: {e} - {traceback.format_exc()}")
        if e.__cause__:
            print(f"Caused by: {e.__cause__}")
        return {"best": {"type": "error", "value": None, "mate_in": None}, "alternatives": []}


def evaluate(board, engine, depth=10, multipv=1):
    info = engine.analyse(board, chess.engine.Limit(
        depth=depth), multipv=multipv)
    return info["score"].relative.score(mate_score=10000) / 100.0


def best_move(board, engine, depth):
    result = engine.play(board, chess.engine.Limit(depth=depth))
    return result.move


def parse_info(info, turn=chess.WHITE):
    # Si es una lista (multiPV), usamos el primero
    if isinstance(info, list):
        if len(info) == 0:
            return {"type": "none", "value": 0, "mate_in": None}
        info = info[0]

    print(f"Parsing info: {info}")

    if info is None or "score" not in info:
        return {"type": "none", "value": 0, "mate_in": None}

    score_obj = info["score"].pov(turn)  # <- esto es clave

    if score_obj.is_mate():
        return {
            "type": "mate",
            "value": None,
            "mate_in": score_obj.mate()
        }
    else:
        return {
            "type": "cp",
            "value": score_obj.score(),
            "mate_in": None
        }


def compare_to_best(actual_eval: dict, alternatives: list, threshold_cp: int = 100) -> str | None:
    """
    Compara la evaluación de la jugada actual con las mejores jugadas alternativas.

    Devuelve una etiqueta si hay una diferencia significativa.
    """
    actual_score = actual_eval.get("value", 0)

    for alt in alternatives:
        alt_score = alt.get("value", 0)

        # Si alguna alternativa era mucho mejor que la jugada real
        if alt_score - actual_score >= threshold_cp:
            return "missed_tactical_opportunity"

        # Si la jugada fue mucho peor que varias opciones
        if actual_score - alt_score >= threshold_cp:
            return "inaccurate_or_blunder"

    return None


def convert_pov_score(score: chess.engine.PovScore) -> dict:
    """
    Convierte un objeto PovScore a un dict estandarizado.
    """
    try:
        if score.is_mate():
            return {
                "type": "mate",
                "value": None,
                "mate_in": score.mate()
            }
        else:
            return {
                "type": "cp",
                "value": score.score(),
                "mate_in": None
            }
    except Exception as e:
        print(f"❌ Error al convertir PovScore: {e}")
        return {
            "type": "unknown",
            "value": None,
            "mate_in": None
        }
