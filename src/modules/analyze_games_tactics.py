import os
import traceback
import chess
import chess.engine
import pandas as pd
from config.tactical_analysis_config import PHASE_DEPTHS, TACTICAL_ANALYSIS_SETTINGS
from db.db_utils import DBUtils
from db.models.games import Games
from modules.stockfish_analysis import compare_to_best, get_evaluation
from decorators.auto_logger import auto_log_module_functions, auto_logger_execution_time
import dotenv
from modules.pgn_utils import get_game_id
from db.repository.features_repository import FeaturesRepository
from db.repository.games_repository import GamesRepository
from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository
env = dotenv.load_dotenv()

STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")
db_utils = DBUtils()
features_repo = FeaturesRepository()
games_repo = GamesRepository()
analyzed_tacticals_repo = Analyzed_tacticalsRepository()


# Detecta patrones tácticos en una partida de ajedrez. Bajo depth=15 a 10 para acelerar el análisis
@auto_logger_execution_time
def detect_tactics_from_game(game, depth=10):
    """
    Analyzes a chess game to detect tactical motifs and errors for each move beyond the opening phase.

    This function iterates through the mainline moves of a given chess game, skipping the opening moves as defined by
    TACTICAL_ANALYSIS_SETTINGS. For each move, it evaluates the position before and after the move using a chess engine,
    classifies tactical patterns, and assigns error labels based on the evaluation difference. It also considers alternative
    moves using MultiPV analysis when appropriate.

    Args:
        game: A chess.pgn.Game object representing the chess game to analyze.
        depth (int, optional): The default engine search depth for evaluation. May be dynamically adjusted per move.

    Returns:
        list[dict]: A list of dictionaries, each containing information about detected tactical tags, error labels,
                    score differences, player color, move number, and FEN for each analyzed move.
                    Returns None if no tags are found or if an exception occurs before any tags are processed.

    Raises:
        Any exceptions encountered during analysis are caught and logged; the function returns the tags processed up to
        the point of failure, or None if none were processed.

    Note:
        - Requires global settings and helper functions such as TACTICAL_ANALYSIS_SETTINGS, PHASE_DEPTHS,
          classify_simple_pattern, get_game_phase, get_evaluation, classify_tactical_pattern, classify_error_label,
          and compare_to_best.
        - Uses a cache to avoid redundant evaluations of the same positions.
        - Designed for use in tactical analysis modules for chess applications.
    """
    tags = []

    try:
        print("Init detect_tactics_from_game")
        eval_cache = {}

        node = game
        board = chess.Board()

        for i, move in enumerate(game.mainline_moves()):
            if i + 1 <= TACTICAL_ANALYSIS_SETTINGS.get("opening_move_threshold", 6):
                print(f"⏭️ Skiping opening move #{i+1}")
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

            min_branching_for_analysis = TACTICAL_ANALYSIS_SETTINGS.get(
                "min_branching_for_analysis", 4)

            if len(list(board.legal_moves)) <= min_branching_for_analysis:
                print(
                    f"⏭️ Move #{i+1} skipped due to low complexity (branching < {min_branching_for_analysis})")
                board.push(move)
                continue

            if fen_before in eval_cache:
                print(f"Evaluating FEN before move: {fen_before}")
                eval_before = eval_cache[fen_before]
            else:
                print(f"Evaluating FEN before move: {fen_before}")
                eval_before = get_evaluation(
                    fen_before, depth, multipv=multipv)
                eval_cache[fen_before] = eval_before

                best_move = eval_before.get("best", None)
                if not best_move:
                    print("⚠️ No 'best move' received, skipping comparison.")
            # ➤ Copia antes de aplicar la jugada
            board_before = board.copy()
            # ➤ Aplicar movimiento
            board.push(move)

            print(f"Evaluation before move: {eval_before}")
            print(f"Making move {move.uci()}")

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

            if isinstance(score_before, int) and isinstance(score_after, int):
                score_diff = score_after - score_before
            else:
                print(
                    f"⚠️ Non-numeric evaluation before/after: {score_before}, {score_after}")
                score_diff = 0

            print(f"Score difference {score_diff}")

           # ➤ Clasificar jugada táctica por patrón
            tactical_tag = classify_tactical_pattern(
                score_diff, board_before, move)
            error_label = classify_error_label(score_diff)
           # ➤ Analizar con MultiPV si hay alternativas mejores
            if "best" in eval_before:
                tag_alt = compare_to_best(eval_before["best"], eval_before.get(
                    "alternatives", []), threshold_cp=100)
            else:
                print("⚠️ eval_before does not have key 'best':", eval_before)
                tag_alt = "unknown"

            print(f"Tactical tag: {tactical_tag} (alternative: {tag_alt})")
            if tactical_tag:
                tags.append({
                    "fen": fen_before,
                    "move": move.uci(),
                    "tag": pre_tag if pre_tag else tactical_tag or tag_alt,
                    "error_label": error_label,
                    "score_diff": score_diff,
                    "player_color": 1 if board.turn == chess.WHITE else 0,
                    "move_number": i + 1
                })

            fen_after = board.fen()
            print(f"Evaluating FEN after move: {fen_after}")
            eval_after = get_evaluation(fen_after, depth, multipv=multipv)
            print(f"Evaluation after move: {eval_after}")
            print(
                f"Full evaluation for move {board.turn}:{i+1} : {move.uci()}")
            print(
                f"Score before: {score_before}, Score after: {score_after}, Score diff: {score_diff}")
            print(f"Tags found: {tags[-1] if tags else 'None'}")

        print(f"Tags returned by detect_tactics_from_game: {tags}")
        return tags
    except Exception as e:
        print(f"❌ Error analyzing game: {e} - {traceback.print_exc()}")
        if e.__cause__:
            print("❌ Original cause (inner exception):", e.__cause__)
        # returned already procecess tags
        print(
            f"Returning already processed {len(tags) if tags else None} tags before detect_tactics_from_game crashed.")
        return tags if tags else None


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


def generate_comments_for_game(game: Games) -> list:
    """
    Genera lista de jugadas anotadas usando datos del repositorio de características (Features).
    """
    repo = FeaturesRepository()
    features = repo.get_by_game_id(game.id)

    comments = []

    for feat in sorted(features, key=lambda x: x.move_number):
        san = feat.move_san or ""
        tags = feat.tags or []
        diff = feat.score_diff or 0

        comment_parts = []

        if diff > 100:
            comment_parts.append(
                "Muy buena jugada, mejora claramente la evaluación.")
        elif diff < -300:
            comment_parts.append("Blunder, la evaluación empeora gravemente.")
        elif diff < -100:
            comment_parts.append("Jugada dudosa o error táctico importante.")

        # Etiquetas tácticas desde `tags`
        tag_map = {
            "mate": "Mate threat detected.",
            "sacrifice": "Interesting tactical sacrifice.",
            "pin": "Exploits a pin.",
            "fork": "Creates a double attack.",
            "discovered_attack": "Discovered attack.",
            "attraction": "Attraction tactic to weaken.",
            "deflection": "Defensive deflection of the opponent."
        }

        for tag in tags:
            if tag in tag_map:
                comment_parts.append(tag_map[tag])

        comment = f" {{{' '.join(comment_parts)}}}" if comment_parts else ""
        comments.append(f"{san}{comment}")

    return comments


def get_game_phase(board):
    pieces_count = len(board.piece_map())
    if pieces_count >= 24:
        return "opening"
    elif pieces_count >= 12:
        return "middlegame"
    return "endgame"


def classify_error(score_diff):
    if pd.isnull(score_diff):
        return None
    if score_diff < 100:
        return "good"
    elif score_diff < 300:
        return "inaccuracy"
    elif score_diff < 700:
        return "mistake"
    else:
        return "blunder"


def classify_tactical_pattern(score_diff, board, move):
    # Reutiliza las etiquetas simples
    simple_tag = classify_simple_pattern(board, move)
    if simple_tag:
        return simple_tag

    return None


def classify_error_label(score_diff):
    if score_diff is None:
        return None
    if score_diff <= 50:
        return "good"
    elif score_diff <= 150:
        return "inaccuracy"
    elif score_diff <= 500:
        return "mistake"
    else:
        return "blunder"


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
        f"Evaluating fork for move: {move.uci()} from {chess.square_name(move.from_square)} to {chess.square_name(move.to_square)}")
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
        f"Evaluating pin for move: {move.uci()} from {chess.square_name(move.from_square)} to {chess.square_name(move.to_square)}")
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
        f"Evaluating discovered attack for move: {move.uci()} from {chess.square_name(move.from_square)} to {chess.square_name(move.to_square)}")
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
