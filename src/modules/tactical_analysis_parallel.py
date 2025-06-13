import os
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

import chess
import pandas as pd

from decorators.auto_logger import auto_log_module_functions
from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository
from db.repository.features_repository import FeaturesRepository
from db.repository.games_repository import GamesRepository
from db.models.games import Games
from modules.tactical_analysis import detect_tactics_from_game
from config.tactical_analysis_config import TACTICAL_ANALYSIS_SETTINGS
from modules.pgn_utils import get_game_id
from modules.pandas_utils import get_move_number_from_df
import io
import dotenv


dotenv.load_dotenv()

LIMIT_FOR_DEBUG = int(os.environ.get("LIMIT_FOR_DEBUG", 1))
LIMIT_FOR_DEBUG = None if LIMIT_FOR_DEBUG == 0 else LIMIT_FOR_DEBUG

games_repo = GamesRepository()


def run_parallel_analysis_from_db(max_workers=4):
    analyzed_tacticals_repo = Analyzed_tacticalsRepository()
    features_repo = FeaturesRepository()

    print("🔍 Starting parallel analysis of games from database...")

    all_games = games_repo.get_all_games()
    print(
        f"🔍 Total games retrieved from database: {len(all_games)} - Type: {type(all_games[0]) if not all_games is None else None}")

    analyzed = analyzed_tacticals_repo.get_all()
    print(f"🔍 Total analyzed games: {len(analyzed)}")
    pending_games_id = [
        g.game_id for g in all_games if g.game_id not in analyzed]
    print(
        f"🚀 Running parallel analysis on {len(pending_games_id)} games...type: {pending_games_id}")
    print(
        f"🔍 Type = {type(pending_games_id)}, length = {len(pending_games_id) if hasattr(pending_games_id, '__len__') else 'N/A'}")

    # 🔄 CAMBIO: limitador activo
    pending_games_id = pending_games_id[:LIMIT_FOR_DEBUG]
    print(f"🔍 Analysis limited to {len(pending_games_id)} games for debugging")

    # Testing with a single game for debugging
    game_id, tags_df = analyze_game_parallel(game_id=pending_games_id[0])

    print(
        f"🔍 Analyzed data from analyze_game_parallel: game {game_id} - Tags found: {len(tags_df) if tags_df is not None else 'None'}")
    # 🔄 CAMBIO: log claro
    features_repo.update_features_tags_and_score_diff(game_id, tags_df)
    analyzed_tacticals_repo.save_analyzed_tactical_hash(game_id)
    return

    # 🔄 CAMBIO: podrías usar ThreadPoolExecutor para debug
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        print("💡 About to submit tasks...")

        # 🔄 CAMBIO: prueba de una sola tarea
        for i, game_id in enumerate(pending_games_id):
            try:
                future = executor.submit(analyze_game_parallel, game_id)
                futures.append(future)
            except Exception as e:
                print(f"❌ Error al crear future #{i}: {e}")

        # 🔄 CAMBIO: log claro
        print(f"🧠 {len(futures)} tasks submitted to executor.")

        print("🕒 Entering as_completed loop...")
        # 🔄 CAMBIO: manejo robusto con timeout y try
        for future in as_completed(futures):
            try:
                print("⏳ Waiting for a future to complete...")
                game_id, tags_df = future.result(
                    timeout=60)  # 🔄 CAMBIO: timeout opcional

                print(
                    f"✅ Future completed for game {game_id} - {len(tags_df) if tags_df is not None else 'No tags'} tags found")

                features_repo.update_features_tags_and_score_diff(
                    game_id, tags_df)
                analyzed_tacticals_repo.save_analyzed_tactical_hash(game_id)

            except Exception as e:
                # 🔄 CAMBIO: log de excepción
                print(f"💥 Future failed: {e}\n{traceback.format_exc()}")
                continue

            if tags_df is None:
                print(
                    f"❌ Game {game_id} could not be processed, no tags found")
                continue

            print(f"🔍 Processing game {game_id}... adding {len(tags_df)} tags")

            move_number = get_move_number_from_df(tags_df)
            player_color = tags_df.iloc[0]["player_color"]
            print(
                f"🔍 Game {game_id} - Move: {move_number}, Color: {player_color}")

            features_repo.update_features_tags_and_score_diff(game_id, tags_df)
            print(f"✅ Tags for game {game_id} saved")
            analyzed_tacticals_repo.save_analyzed_tactical(game_id)
            print(f"✅ Game {game_id} marked as analyzed")


def analyze_game_parallel(game_id):
    print(f"🔍 Analyzing game {game_id} in parallel...")
    game = games_repo.get_game_by_id(game_id)
    try:
        # Convert Games object too chess.pgn.Game if necessary
        pgn_games = chess.pgn.read_game(io.StringIO(game.pgn))

        if pgn_games is None:
            raise ValueError(f"Game {game_id} is not a valid Games object")

        depth = TACTICAL_ANALYSIS_SETTINGS.get("depth", 8)
        # 🔄 CAMBIO: log útil
        print(f"▶ Analyzing game {game_id} in subprocess...")

        # 🔄 CAMBIO: validación robusta del objeto juego
        if not hasattr(pgn_games, "headers") or not hasattr(pgn_games, "mainline_moves"):
            raise ValueError(
                f"Invalid game object: missing headers or moves ({type(pgn_games)})")

        tags = detect_tactics_from_game(pgn_games, depth=depth)

        tags_df = pd.DataFrame(tags)
        if tags_df is None or tags_df.empty:
            print(f"❌ No tactics detected in game {game_id}")
            return (game_id, None)
        print(f"✅ Game {game_id} analyzed with {len(tags_df)} tags found")
        return (game_id, tags_df)

    except Exception as e:
        err_id = game_id if game else "unknown"
        # 🔄 CAMBIO: error más informativo
        print(f"❌ Error in game {err_id}: {e}\n{traceback.format_exc()}")
        return (err_id, None)


auto_log_module_functions(locals())
