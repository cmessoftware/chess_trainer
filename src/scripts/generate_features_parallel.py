#!/usr/bin/env python3
"""
Parallel Feature Generation Script for Chess Games

This script generates features from chess games stored in PostgreSQL database.
It supports filtering by source and parallel processing for better performance.

Usage Examples:
    # Generate features for all games (max 1000)
    python generate_features_parallel.py

    # Generate features for a specific number of games
    python generate_features_parallel.py --max-games 500

    # Generate features only for lichess games
    python generate_features_parallel.py --source lichess --max-games 1000

    # Generate features only for chess.com games
    python generate_features_parallel.py --source chess.com --max-games 2000

    # Generate features only for elite games
    python generate_features_parallel.py --source elite_games --max-games 100

Environment Variables:
    CHESS_TRAINER_DB_URL: PostgreSQL connection URL
    MAX_WORKERS: Number of parallel workers (default: 4)
    FEATURES_PER_CHUNK: Games per processing chunk (default: 500)

Features:
    - Parallel processing with configurable workers
    - Source-based filtering (lichess, chess.com, elite_games, etc.)
    - Automatic detection of already processed games
    - Detailed progress reporting and error handling
    - PostgreSQL-based storage with transaction safety
"""

import argparse
from concurrent.futures import ProcessPoolExecutor
from importlib import metadata
from io import StringIO
import os
import sys
import traceback
import chess
import chess.pgn
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from modules.pgn_utils import get_game_id, is_valid_pgn
from modules.features_generator import generate_features_from_game
from db.repository.features_repository import FeaturesRepository
from db.repository.processed_feature_repository import ProcessedFeaturesRepository
from db.repository.games_repository import GamesRepository
from db.db_utils import DBUtils

# Load environment variables
import dotenv
dotenv.load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
PGN_PATH = os.environ.get("PGN_PATH", "./data/games")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
FEATURES_PER_CHUNK = int(os.environ.get("FEATURES_PER_CHUNK", 500))

engine = create_engine(DB_URL)
metadata = MetaData()
db_utils = DBUtils()


def load_processed_hashes():
    print("🔍 Loading processed game hashes...")
    try:
        processed_repo = ProcessedFeaturesRepository(
            session_factory=lambda: sessionmaker(bind=engine)())
        processed_hashes = processed_repo.get_all()
        return set(processed_hashes)
    except Exception as e:
        print(f"❌ Error loading processed hashes: {e}")
        return set()


def process_chunk(pgn_list: list[str]):
    Session = sessionmaker(bind=engine)
    session = Session()
    processed_count = 0
    skipped_count = 0
    error_count = 0

    try:
        features_repo = FeaturesRepository(
            session_factory=lambda: sessionmaker(bind=engine)())

        processed_features_repo = ProcessedFeaturesRepository(
            session_factory=lambda: sessionmaker(bind=engine)())

        if not pgn_list:
            print("🔍 No games to process in this chunk.")
            return

        # Load processed hashes at chunk level to reduce database calls
        processed_hashes = load_processed_hashes()

        for pgn_text in pgn_list:
            try:
                valid, parsed_game = is_valid_pgn(pgn_text)

                if not valid:
                    print(f"❌ Invalid PGN format: {pgn_text[:100]}...")
                    error_count += 1
                    continue

                game_id = get_game_id(parsed_game)
                if game_id in processed_hashes:
                    print(f"⚠️ Game already processed: {game_id}, skipping.")
                    skipped_count += 1
                    continue

                parsed_game = chess.pgn.read_game(StringIO(pgn_text))

                print(f"🎯 Processing game ID: {game_id}")
                white_player = parsed_game.headers.get('White', 'Unknown')
                black_player = parsed_game.headers.get('Black', 'Unknown')
                print(f"   {white_player} vs {black_player}")

                features = generate_features_from_game(
                    parsed_game, game_id=game_id)

                if not isinstance(features, list) or not all(isinstance(f, dict) for f in features):
                    print(
                        f"❌ ERROR: generate_features_from_game returned invalid format for {game_id}")
                    error_count += 1
                    continue

                if len(features) == 0:
                    print(f"⚠️ No features generated for game {game_id}")
                    skipped_count += 1
                    continue

                print(f"� Game {game_id} generated {len(features)} features")

                features_repo.save_many_features(features)
                processed_features_repo.save_processed_hash(game_id)

                processed_count += 1
                print(f"✅ Game {game_id} processed and features saved.")

            except Exception as e:
                error_count += 1
                print(f"❌ Error processing game:\n{pgn_text[:100]}...")
                print(f"🔍 Error details: {e} - {traceback.format_exc()}")
                continue

        session.commit()
        print(
            f"📈 Chunk completed - Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}")

    except Exception as e:
        session.rollback()
        print(f"❌ Error in chunk processing: {e} {traceback.format_exc()}")
        if e.__cause__:
            print(f"🔍 Error cause: {e.__cause__}")
    finally:
        session.close()


def chunkify(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def main(max_games=1000, source=None):
    games_repo = GamesRepository()

    all_games = []

    try:
        offset = 0
        processed_hashes = load_processed_hashes()

        print(f"🔍 Starting feature generation process...")
        if source:
            print(f"📋 Filtering by source: {source}")
        print(f"🎯 Maximum games to process: {max_games}")
        print(f"📊 Already processed games: {len(processed_hashes)}")

        while len(all_games) < max_games:
            # Use the method that supports source filtering and excludes already processed games
            current_chunk = games_repo.get_games_by_pagination_not_analyzed(
                analyzed_hashes=processed_hashes,
                offset=offset,
                limit=FEATURES_PER_CHUNK,
                source=source
            )
            if not current_chunk:
                print(
                    f"🔍 No more games available. Retrieved {len(all_games)} games total.")
                break
            all_games.extend(current_chunk)
            offset += FEATURES_PER_CHUNK
            print(
                f"📥 Retrieved {len(current_chunk)} games (total: {len(all_games)})")
    except Exception as e:
        print(f"⚠️ Error getting games: {e}")
        return

    if not all_games:
        print("🔍 No games to process.")
        return

    # all_games now contains PGN strings directly since we used get_games_by_pagination_not_analyzed
    all_game_pgns = all_games
    chunks = list(chunkify(all_game_pgns, FEATURES_PER_CHUNK))
    print(f"🧩 Total chunks to process: {len(chunks)}")
    print(f"📊 Total games to process: {len(all_game_pgns)}")

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        for i, future in enumerate(futures, 1):
            print(f"⏳ Processing chunk {i}/{len(futures)}...")
            future.result()
            print(f"✅ Completed chunk {i}/{len(futures)}")

    print("✅ Parallel feature generation completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import chess games and generate features in parallel.")
    parser.add_argument('--max-games', required=False, default=1000, type=int,
                        help='Maximum number of games to process (optional, for testing)')
    parser.add_argument('--source', required=False, default=None, type=str,
                        choices=['stockfish', 'elite',
                                 'personal', 'novice', 'fide'],
                        help='Filter games by source (optional). Examples: "personal", "novice", "elite","fide')
    args = parser.parse_args()

    try:
        if not DB_URL:
            raise ValueError(
                "CHESS_TRAINER_DB_URL environment variable is not set.")

        print(f"🚀 Starting parallel feature generation...")
        print(f"📋 Parameters:")
        print(f"   - Max games: {args.max_games}")
        print(
            f"   - Source filter: {args.source if args.source else 'All sources'}")
        print(f"   - Max workers: {MAX_WORKERS}")
        print(f"   - Features per chunk: {FEATURES_PER_CHUNK}")

        main(max_games=args.max_games, source=args.source)
    except Exception as e:
        print(f"❌ Error during import: {e}")
        if e.__cause__:
            print(f"🔍 Cause: {e.__cause__}")
        sys.exit(1)
