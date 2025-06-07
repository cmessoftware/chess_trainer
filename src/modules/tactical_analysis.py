import io
import os
import traceback
import chess
import chess.engine
import pandas as pd
from decorators.measure_time import measure_time
from config.tactical_analysis_config import PHASE_DEPTHS, TACTICAL_ANALYSIS_SETTINGS
from db.db_utils import DBUtils
from modules.stockfish_analysis import compare_to_best, get_evaluation
from decorators.auto_logger import auto_log_module_functions, auto_logger_execution_time
import dotenv

from modules.pgn_utils import get_game_hash, load_all_games_from_db
from db.tactical_db import update_features_tags_and_score_diff
env = dotenv.load_dotenv()

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")
db_utils = DBUtils()


@auto_logger_execution_time
def analyze_single_game_tactics(game_id):
    """
    Analiza tácticas de una partida específica por su ID.
    """
    db_utils.init_analyzed_tacticals_table()
    analyzed = db_utils.load_analyzed_tacticals_hashes()

    if game_id in analyzed:
        print(f"✅ Partida {game_id} ya analizada, saltando...")
        return

    game = db_utils.get_game_by_id(game_id)

    print(
        f"🔍 Analizando táctica: {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}")

    try:
        depth = TACTICAL_ANALYSIS_SETTINGS.get("depth", 8)
        tags_df = detect_tactics_from_game(game, depth=depth)
        update_features_tags_and_score_diff(game_id, tags_df)

    except Exception as e:
        print(
            f"❌ Excepcion al analizar partida {game_id} - {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}: {e} - {traceback.print_exc()}")
        if e.__cause__:
            print("🔗 Causa original (inner exception):", e.__cause__)
        return


@auto_logger_execution_time
def analyze_game_tactics():
    db_utils.init_analyzed_tacticals_table()
    analyzed = db_utils.load_analyzed_tacticals_hashes()
    print(
        f"🔍 Cargando partidas ya analizadas... {len(analyzed)} partidas encontradas.")

    games = load_all_games_from_db()

    for game in games:
        game_hash = get_game_hash(game)
        if game_hash in analyzed:
            print(
                f"✅ Partida {game_hash} : {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')} ya analizada, saltando...")
            continue

        print(
            f"🔍 Analizando táctica: {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}")

        try:
            depth = TACTICAL_ANALYSIS_SETTINGS.get("depth", 8)
            tags_df = detect_tactics_from_game(game, depth=depth)
            db_utils.insert_tactical_tags_to_db(game_hash, tags_df)

        except Exception as e:
            print(
                f"❌ Excepcion al analizar partida {game_hash} - {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}: {e} - {traceback.print_exc()}")
            if e.__cause__:
                print("🔗 Causa original (inner exception):", e.__cause__)
            continue  # ⚠️ No marcar como procesada si hay error

        db_utils.save_analyzed_tacticals_hash(game_hash)


# Detecta patrones tácticos en una partida de ajedrez. Bajo depth=15 a 10 para acelerar el análisis
def detect_tactics_from_game(game, depth=10):
    try:
        print("Init detect_tactics_from_game")
        tags = []
        eval_cache = {}

        node = game
        board = chess.Board()

        for i, move in enumerate(game.mainline_moves()):
            if i + 1 <= TACTICAL_ANALYSIS_SETTINGS.get("opening_move_threshold", 6):
                print(f"⏭️ Saltando jugada de apertura #{i+1}")
                board.push(move)
                continue

            # ➤ Clasificación previa rápida
            pre_tag = classify_simple_pattern(board.copy(), move)

            if pre_tag:
                multipv = 1
                depth = 6  # más rápido
            else:
                # ➤ Fase del juego y profundidad dinámica
                branching = len(list(board.legal_moves))
                # ➤ Branching factor para decidir uso de MultiPV
                multipv = 3 if branching > 10 else 1
                phase = get_game_phase(board)
                depth = PHASE_DEPTHS.get(phase, 8)

            fen_before = board.fen()
            print(f"🔢 Move #{i+1}")
            print(f"Evaluando FEN antes del movimiento: {fen_before}")

            min_branching_for_analysis = TACTICAL_ANALYSIS_SETTINGS.get(
                "min_branching_for_analysis", 4)

            if len(list(board.legal_moves)) <= min_branching_for_analysis:
                print(
                    f"⏭️ Jugada #{i+1} omitida por baja complejidad (branching < {min_branching_for_analysis})")
                board.push(move)
                continue

            if fen_before in eval_cache:
                eval_before = eval_cache[fen_before]
            else:
                print(f"Evaluando FEN antes del movimiento: {fen_before}")
                eval_before = get_evaluation(
                    fen_before, depth, multipv=multipv)
                eval_cache[fen_before] = eval_before
            # ➤ Copia antes de aplicar la jugada
            board_before = board.copy()
            # ➤ Aplicar movimiento
            board.push(move)

            print(f"Evaluación antes del movimiento: {eval_before}")
            print(f"Efectuando movimiento {move.uci()}")

            # ➤ Evaluación después del movimiento
            fen_after = board.fen()
            if fen_after in eval_cache:
                eval_after = eval_cache[fen_after]
            else:
                eval_after = get_evaluation(fen_after, depth, multipv=multipv)
                eval_cache[fen_after] = eval_after

           # ➤ Extraer evaluaciones numéricas seguras
            def safe_extract_value(eval_data):
                if isinstance(eval_data, dict):
                    if "best" in eval_data:
                        return eval_data["best"].get("value", 0)
                    return eval_data.get("value", 0)
                return 0

            score_before = safe_extract_value(eval_before)
            score_after = safe_extract_value(eval_after)

            # Ajuste por turno: invertir si juega negras
            if not board.turn:
                score_before = -score_before
                score_after = -score_after

            score_diff = score_after - score_before
            print(f"Diferencia de score: {score_diff}")

           # ➤ Clasificar jugada táctica por patrón
            tag = classify_tactical_pattern(score_diff, board_before, move)
           # ➤ Analizar con MultiPV si hay alternativas mejores
            if "best" in eval_before:
                tag_alt = compare_to_best(eval_before["best"], eval_before.get(
                    "alternatives", []), threshold_cp=100)
            else:
                print("⚠️ eval_before no tiene clave 'best':", eval_before)
                tag_alt = "unknown"

            print(f"Etiqueta táctica: {tag} (alternativa: {tag_alt})")
            if tag:
                tags.append({
                    "fen": fen_before,
                    "move": move.uci(),
                    "tag": pre_tag if pre_tag else tag or tag_alt,
                    "score_diff": score_diff,
                    "player_color": 1 if board.turn == chess.WHITE else 0,
                    "move_number": i + 1
                })

            fen_after = board.fen()
            print(f"Evaluando FEN después del movimiento: {fen_after}")
            eval_after = get_evaluation(fen_after, depth, multipv=multipv)
            print(f"Evaluación después del movimiento: {eval_after}")
            print(
                f"Evaluacion completa para el movimiento {board.turn}:{i+1} : {move.uci()}")
        return tags
    except Exception as e:
        print(f"❌ Error al analizar la partida: {e} - {traceback.print_exc()}")
        if e.__cause__:
            print("❌ Original casue (inner exception):", e.__cause__)


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


def get_game_phase(board):
    pieces_count = len(board.piece_map())
    if pieces_count >= 24:
        return "opening"
    elif pieces_count >= 12:
        return "middlegame"
    return "endgame"


def classify_tactical_pattern(score_diff, board, move):
    # Reutiliza las etiquetas simples
    simple_tag = classify_simple_pattern(board, move)
    if simple_tag:
        return simple_tag

    if abs(score_diff) >= 1.5:
        return "blunder" if score_diff < 0 else "tactical_opportunity"

    return None


def classify_simple_pattern(board, move):
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
    return None


def evaluate_tactical_features(row, engine, depth=18, multipv=1):
    fen = row["fen"]
    move_uci = row["move_uci"]

    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_uci)
        if move not in board.legal_moves:
            return pd.Series([None, None, None])

        # Score antes de mover
        info_before = engine.analyse(
            board, chess.engine.Limit(depth=depth), multipv=multipv)
        score_before = info_before["score"].relative.score(mate_score=10000)

        best_line = info_before.get("pv", [])
        is_forced = len(best_line) == 1

        # Aplicar jugada del jugador
        board.push(move)

        # Score después de mover
        info = engine.analyse(board, chess.engine.Limit(
            depth=depth), multipv=multipv)
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
        results = df.apply(
            lambda row: evaluate_tactical_features(row, engine), axis=1)
        results.columns = ["threatens_mate",
                           "is_forced_move", "depth_score_diff"]
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

    print(
        f"Evaluando fork para el movimiento: {move.uci()} desde {chess.square_name(move.from_square)} a {chess.square_name(move.to_square)}")
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
    print(
        f"Evaluando pin para el movimiento: {move.uci()} desde {chess.square_name(move.from_square)} a {chess.square_name(move.to_square)}")
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
    print(
        f"Evaluando ataque descubierto para el movimiento: {move.uci()} desde {chess.square_name(move.from_square)} a {chess.square_name(move.to_square)}")
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


def extract_score_from_info(info):
    score = info["score"].relative
    if score.is_mate():
        return {"score": 10000 if score.mate() > 0 else -10000, "mate_in": score.mate()}
    else:
        return {"score": score.score(), "mate_in": None}


auto_log_module_functions(locals())


# Uso:
# process_csv("simulated_tactical_dataset.csv", "tactical_enriched.csv")
