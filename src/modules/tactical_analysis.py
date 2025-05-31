import os
import traceback
import chess
import chess.engine
import pandas as pd
from modules.stockfish_analysis import get_evaluation
from modules.auto_logger import auto_log_module_functions
import dotenv
env = dotenv.load_dotenv()

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")

def detect_tactics_from_game(game, depth=15):
    try:
        print("Init detect_tactics_from_game")
        tags = []

        node = game
        board = chess.Board()

        for i, move in enumerate(game.mainline_moves()):
            fen_before = board.fen()
            print(f"🔢 Move #{i+1}")
            print(f"Evaluando FEN antes del movimiento: {fen_before}")

            eval_before = get_evaluation(fen_before, depth)
            
            print(f"Evaluación antes del movimiento: {eval_before}")
            print(f"Efectuando movimiento {move.uci()}")
            #board.push(move)

            # if move not in board.pseudo_legal_moves:
            #     print(f"❌ Movimiento no pseudo-legal: {move} en {board.fen()} - Saltando partida completa")
            #     return []  # evitamos guardar datos corruptos

            # print(f"Aplicando movimiento: {move.uci()}")
            # board.push(move)

            fen_after = board.fen()
            print(f"Evaluando FEN después del movimiento: {fen_after}")
            eval_after = get_evaluation(fen_after, depth)
            print(f"Evaluación después del movimiento: {eval_after}")

            eval_before_score = extract_score(eval_before)
            print(f"Score antes del movimiento: {eval_before_score}")
            eval_after_score = extract_score(eval_after)
            print(f"Score después del movimiento: {eval_after_score}")
            score_diff = eval_after_score - eval_before_score
            print(f"Diferencia de score: {score_diff}")

            tag = classify_tactical_pattern(score_diff, board.copy(), move)
            
            #Muevo despues de clasificar para evitar problemas con el tablero
            board.push(move)

            if tag:
                tags.append({
                    "fen": fen_before,
                    "move": move.uci(),
                    "tag": tag,
                    "score_diff": score_diff,
                    "move_number": i + 1
                })

        return tags
    except Exception as e:
        print(f"Error al analizar la partida: {e} - {traceback.print_exc()}")
        if e.__cause__:
            print("Original casue (inner exception):", e.__cause__)
    

def extract_score(evaluation):
    """Convierte un dict de evaluación de Stockfish a un número comparable"""
    if evaluation.get("type") == "cp":
        return evaluation.get("value", 0)
    elif evaluation.get("type") == "mate":
        mate_value = evaluation.get("value", 0)
        return 1000 * (1 if mate_value > 0 else -1)
    elif evaluation.get("type") == "score":
        return evaluation.get("score", 0)
    elif evaluation.get("type") == "mate_in":
        mate_in = evaluation.get("mate_in", 0)
        return 1000 * (1 if mate_in > 0 else -1)
    return 0

def classify_tactical_pattern(score_diff, board, move):
    if board.is_checkmate():
        return "mate"
    if board.gives_check(move):
        return "check"
    if is_fork(board, move):
        return "fork"
    if is_pin(board, move):
        return "pin"
    if is_discovered_attack(board, move):
        return "discovered_attack"
    if abs(score_diff) >= 1.5:
        return "blunder" if score_diff < 0 else "tactical_opportunity"
    return None

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

def is_fork(board, move):
    """
    Detecta si una pieza (usualmente un caballo) ataca múltiples piezas valiosas.
    """
    piece = board.piece_at(move.from_square)
    if not piece or piece.piece_type != chess.KNIGHT:
        return False

    print(f"Evaluando fork para el movimiento: {move.uci()} desde {move.from_square} a {move.to_square}")
    board.push(move)
    attacked = list(board.attacks(move.to_square))
    valuable_targets = [
        sq for sq in attacked
        if board.piece_at(sq) and board.piece_at(sq).piece_type in [chess.QUEEN, chess.ROOK]
    ]
    board.pop()
    return len(valuable_targets) >= 2

def is_pin(board, move):
    """
    Detecta si la jugada genera una clavada (pin).
    """
    print(f"Evaluando pin para el movimiento: {move.uci()} desde {move.from_square} a {move.to_square}")
    board.push(move)
    result = False
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece and piece.color != board.turn:
            if board.is_pinned(not board.turn, sq):
                result = True
                break
    board.pop()
    return result

def is_discovered_attack(board, move):
    """
    Detecta si la jugada expone una pieza atacante (ataque descubierto).
    """
    attacker_color = board.turn
    print(f"Evaluando ataque descubierto para el movimiento: {move.uci()} desde {chess.square_name(move.from_square)} a {chess.square_name(move.to_square)}")
    board.push(move)

    # Verificar si hay alguna pieza enemiga ahora bajo ataque
    result = False
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece and piece.color != attacker_color:
            if board.is_attacked_by(attacker_color, sq):
                result = True
                break

    board.pop()
    return result

auto_log_module_functions(locals())

# Uso:
# process_csv("simulated_tactical_dataset.csv", "tactical_enriched.csv")
