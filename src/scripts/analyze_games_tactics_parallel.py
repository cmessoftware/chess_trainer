import os
import time
import traceback
import logging
import pandas as pd
import io
import dotenv
import psutil
import chess.pgn
from concurrent.futures import ProcessPoolExecutor, as_completed
from modules.analyze_games_tactics import detect_tactics_from_game
from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository
from db.repository.features_repository import FeaturesRepository
from db.repository.games_repository import GamesRepository
from config.tactical_analysis_config import TACTICAL_ANALYSIS_SETTINGS
from modules.pandas_utils import get_feature_from_df
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

dotenv.load_dotenv()
LIMIT_FOR_DEBUG = int(os.environ.get("LIMIT_FOR_DEBUG", 0))
ANALYSIS_WORKERS = int(os.environ.get("ANALYSIS_WORKERS", 2))
ANALYZED_PER_CHUNK = int(os.environ.get("ANALYZED_PER_CHUNK", 10))

def run_parallel_analysis_from_db(max_games=1000000):
    logging.info("🔍 Starting parallel analysis of games from database...")
    logging.info(f"🔧 Config: WORKERS={ANALYSIS_WORKERS}, CHUNK={ANALYZED_PER_CHUNK}, LIMIT_DEBUG={LIMIT_FOR_DEBUG}")

    analyzed_tacticals_repo = Analyzed_tacticalsRepository()
    features_repo = FeaturesRepository()
    games_repo_local = GamesRepository()

    analyzed = set(row.game_id for row in analyzed_tacticals_repo.get_all())

    offset = 0
    total_processed = 0

    while total_processed < max_games:
        try:
            chunk = games_repo_local.get_games_by_pagination_not_analyzed(analyzed, offset, ANALYZED_PER_CHUNK)
            if not chunk:
                logging.info("✅ No more games to process.")
                break

            pending_ids = [get_game_id(pgn_str_to_game(pgn)) for pgn in chunk]

            logging.info(f"🚀 Processing chunk: {len(pending_ids)} games")
            process = psutil.Process()
            logging.info(f"🧠 RAM Before: {process.memory_info().rss / 1024**2:.2f} MB")

            with ProcessPoolExecutor(max_workers=ANALYSIS_WORKERS) as executor:
                futures = [executor.submit(analyze_game_parallel, game_id) for game_id in pending_ids]
                for future in as_completed(futures):
                    try:
                        game_id, tags_df = future.result(timeout=300)
                    except Exception as e:
                        logging.error(f"💥 Future failed: {e}\n{traceback.format_exc()}")
                        continue
                    try:
                        if tags_df is None:
                            logging.warning(f"⚠️ Game {game_id} returned no tags.")
                            analyzed_tacticals_repo.save_analyzed_tactical_hash(game_id)
                            continue
                        features_repo.update_features_tags_and_score_diff(game_id, tags_df)
                        analyzed_tacticals_repo.save_analyzed_tactical_hash(game_id)
                        logging.info(f"✅ Game {game_id} analyzed with {len(tags_df)} tags")
                    except Exception as e:
                        logging.error(f"❌ Error saving analysis for game {game_id}: {e}\n{traceback.format_exc()}")
            offset += ANALYZED_PER_CHUNK
            total_processed += len(chunk)

        except Exception as e:
            logging.error(f"⚠️ Error in main loop: {e}\n{traceback.format_exc()}")
            break

def analyze_game_parallel(game_id):
    try:
        games_repo = GamesRepository()
        analyzed_tacticals_repo = Analyzed_tacticalsRepository()

        process = psutil.Process()
        logging.info(f"🔍 Analyzing game {game_id} - RAM: {process.memory_info().rss / 1024**2:.2f} MB")

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
        logging.error(f"❌ Error in game {game_id}: {e}\n{traceback.format_exc()}")
        return game_id, None

if __name__ == "__main__":
    start = time.time()
    run_parallel_analysis_from_db()
    elapsed = time.time() - start
    logging.info(f"🏁 Parallel analysis completed in {elapsed:.2f} seconds.")
