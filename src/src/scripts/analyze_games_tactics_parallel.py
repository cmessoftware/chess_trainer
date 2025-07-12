import os
import time
import traceback
import logging
import pandas as pd
import io
import dotenv
import psutil
import chess.pgn
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

import sqlalchemy
from modules.analyze_games_tactics import detect_tactics_from_game
from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository
from db.repository.features_repository import FeaturesRepository
from db.repository.games_repository import GamesRepository
from config.tactical_analysis_config import TACTICAL_ANALYSIS_SETTINGS
from modules.pgn_utils import get_game_id, pgn_str_to_game

# Config Logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("analyze.log"),
        logging.StreamHandler()
    ]
)

# Lower the log level only for modules that clutter the application's log.
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("chess.engine").setLevel(
    logging.WARNING)  # Si usás python-chess
# Si ese es el logger del protocolo UCI
logging.getLogger("UciProtocol").setLevel(logging.WARNING)


dotenv.load_dotenv()
LIMIT_FOR_DEBUG = int(os.environ.get("LIMIT_FOR_DEBUG", 0))
ANALYSIS_WORKERS = int(os.environ.get("ANALYSIS_WORKERS", 2))
ANALYZED_PER_CHUNK = int(os.environ.get("ANALYZED_PER_CHUNK", 10))
GAMES_SOURCE = os.environ.get("GAMES_SOURCE", None)


def run_parallel_analysis_from_db(source=None, max_games=1000000, offset=0):
    logging.info("🔍 Starting parallel analysis of games from database...")
    logging.info(
        f"🔧 Config: WORKERS={ANALYSIS_WORKERS}, CHUNK={ANALYZED_PER_CHUNK}, LIMIT_DEBUG={LIMIT_FOR_DEBUG}")
    logging.info(f"🎯 Max games: {max_games}")

    if offset > 0:
        logging.info(f"⏭️  Starting from offset: {offset}")

    if source:
        logging.info(f"📋 Filtering by source: {source}")
    else:
        logging.info("📋 Processing all sources")

    analyzed_tacticals_repo = Analyzed_tacticalsRepository()
    features_repo = FeaturesRepository()
    games_repo_local = GamesRepository()

    analyzed = set(row.game_id for row in analyzed_tacticals_repo.get_all())

    current_offset = offset
    total_processed = 0

    while total_processed < max_games:
        try:
            remaining_games = max_games - total_processed
            current_chunk_size = min(ANALYZED_PER_CHUNK, remaining_games)

            print(
                f"🔄 Fetching games to analyze by source {source if source is not None else 'All'} (processed: {total_processed}/{max_games})")
            chunk = games_repo_local.get_games_by_pagination_not_analyzed(
                analyzed, current_offset, current_chunk_size, source=source)
            if not chunk:
                logging.info("✅ No more games to process.")
                break

            pending_ids = [get_game_id(pgn_str_to_game(pgn)) for pgn in chunk]

            logging.info(f"🚀 Processing chunk: {len(pending_ids)} games")
            process = psutil.Process()
            logging.info(
                f"🧠 RAM Before: {process.memory_info().rss / 1024**2:.2f} MB")

            with ProcessPoolExecutor(max_workers=ANALYSIS_WORKERS) as executor:
                futures = [executor.submit(
                    analyze_game_parallel, game_id) for game_id in pending_ids]
                for future in as_completed(futures):
                    try:
                        game_id, tags_df = future.result(timeout=300)
                    except Exception as e:
                        logging.error(
                            f"💥 Future failed: {e}\n{traceback.format_exc()}")
                        continue
                    try:
                        if tags_df is None:
                            logging.warning(
                                f"⚠️ Game {game_id} returned no tags.")
                            analyzed_tacticals_repo.save_analyzed_tactical_hash(
                                game_id)
                            continue
                        try:
                            features_repo.update_features_tags_and_score_diff(
                                game_id, tags_df)
                        except sqlalchemy.exc.PendingRollbackError as e:
                            logging.error(
                                f"Sesión rota en juego {game_id}, se hace rollback")
                            features_repo.session.rollback()

                        analyzed_tacticals_repo.save_analyzed_tactical_hash(
                            game_id)
                        logging.info(
                            f"✅ Game {game_id} analyzed with {len(tags_df)} tags")
                    except Exception as e:
                        logging.error(
                            f"❌ Error saving analysis for game {game_id}: {e}\n{traceback.format_exc()}")
            current_offset += current_chunk_size
            total_processed += len(chunk)

            if total_processed >= max_games:
                logging.info(f"✅ Reached max games limit: {max_games}")
                break

        except Exception as e:
            logging.error(
                f"⚠️ Error in main loop: {e}\n{traceback.format_exc()}")
            break


def analyze_game_parallel(game_id):
    try:
        games_repo = GamesRepository()
        analyzed_tacticals_repo = Analyzed_tacticalsRepository()

        process = psutil.Process()
        logging.info(
            f"🔍 Analyzing game {game_id} - RAM: {process.memory_info().rss / 1024**2:.2f} MB")

        pgn_text = games_repo.get_pgn_text_by_id(game_id)
        if not pgn_text or len(pgn_text.strip()) == 0:
            analyzed_tacticals_repo.save_analyzed_tactical_hash(game_id)
            raise ValueError(f"Game {game_id} has empty or invalid PGN")

        pgn_game = chess.pgn.read_game(io.StringIO(pgn_text))
        if not pgn_game:
            analyzed_tacticals_repo.save_analyzed_tactical_hash(game_id)
            raise ValueError(f"Game {game_id} could not be parsed as PGN")

        depth = TACTICAL_ANALYSIS_SETTINGS.get("depth", 8)
        tags = detect_tactics_from_game(pgn_game, depth)

        tags_df = pd.DataFrame(tags)
        if tags_df.empty:
            return game_id, None

        return game_id, tags_df

    except Exception as e:
        logging.error(
            f"❌ Error in game {game_id}: {e}\n{traceback.format_exc()}")
        return game_id, None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Parallel analysis of chess games for tactical patterns")
    parser.add_argument("--source", type=str, default=None,
                        help="Filter games by source (e.g., 'lichess', 'chesscom'). If not specified, processes all sources.")
    parser.add_argument("--max-games", type=int, default=1000000,
                        help="Maximum number of games to process (default: 1000000)")
    parser.add_argument("--offset", type=int, default=0,
                        help="Number of games to skip from the beginning (default: 0)")

    args = parser.parse_args()

    # Use command-line source if provided, otherwise fall back to environment variable
    source_to_use = args.source or GAMES_SOURCE

    start = time.time()
    run_parallel_analysis_from_db(
        source=source_to_use, max_games=args.max_games, offset=args.offset)
    elapsed = time.time() - start
    logging.info(f"🏁 Parallel analysis completed in {elapsed:.2f} seconds.")
