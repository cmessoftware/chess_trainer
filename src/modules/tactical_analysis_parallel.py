import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

import chess
from decorators.auto_logger import auto_log_module_functions
from db.repository.game_repository import GameRepository
from modules.pgn_utils import get_game_hash
from db.tactical_db import update_features_tags_and_score_diff
from modules.tactical_analysis import detect_tactics_from_game
from db.db_utils import DBUtils
from config.tactical_analysis_config import TACTICAL_ANALYSIS_SETTINGS

db_utils = DBUtils()


def run_parallel_analysis_from_db(max_workers=4):
    repo = GameRepository()
    all_games = repo.get_all_games()

    if not all_games:
        print("❌ No se encontraron partidas para analizar.")
        return

    if not isinstance(all_games[0], chess.pgn.Game):
        print("❌ Las partidas no están en formato PGN válido.")
        raise ValueError("Las partidas no están en formato PGN válido.")

    analyzed = db_utils.load_analyzed_tacticals_hashes()
    print(
        f"🔍 Cargando partidas ya analizadas... {len(analyzed)} encontradas: {analyzed}")

    pending_games = [
        g for g in all_games if repo.get_game_id_by_game(g) not in analyzed]
    print(
        f"🚀 Ejecutando análisis paralelo sobre {len(pending_games)} partidas...")

    # Para testing
    limit = 1
    # Limitar a 1 partidas para depuración
    pending_games = pending_games[:limit]
    print(
        f"🔍 Análisis limitado a {len(pending_games)} partidas para depuración")

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(analyze_game_parallel, game)
                   for game in pending_games]

        for future in as_completed(futures):
            game_hash, tags_df = future.result()
            print(
                f"🔍 Procesando partida {game_hash}...de longitud {len(game_hash)}")
            if game_hash and tags_df is not None:
                update_features_tags_and_score_diff(game_hash, tags_df)
                save_analyzed_tacticals_hash(game_hash)
                print(f"✅ Partida {game_hash} procesada y guardada")


def analyze_game_parallel(game):
    try:
        depth = TACTICAL_ANALYSIS_SETTINGS.get("depth", 8)
        game_hash = get_game_hash(game)
        tags_df = detect_tactics_from_game(game, depth=depth)
        return (game_hash, tags_df)
    except Exception as e:
        print(
            f"❌ Error en partida {game.headers.get('White')} vs {game.headers.get('Black')}: {e}\n{traceback.format_exc()}")
        return (None, None)


auto_log_module_functions(locals())
