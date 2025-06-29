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
from db.repository.games_repository import GamesRepository
from db.repository.processed_feature_repository import ProcessedFeaturesRepository
from db.repository.games_repository import GamesRepository

# Load environment variables
import dotenv
dotenv.load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
PGN_PATH = os.environ.get("PGN_PATH", "./data/games")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
FEATURES_PER_CHUNK = int(os.environ.get("FEATURES_PER_CHUNK", 500))

engine = create_engine(DB_URL)
metadata = MetaData()


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


def process_chunk(pgn_list: list[str], max_to_process=None):
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
            return processed_count

        # Load processed hashes at chunk level to reduce database calls
        processed_hashes = load_processed_hashes()

        for i, pgn_text in enumerate(pgn_list):
            # Stop if we've reached the max limit
            if max_to_process and processed_count >= max_to_process:
                print(
                    f"🛑 Reached processing limit of {max_to_process} games in this chunk.")
                break

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

                print(
                    f"🎯 Processing game ID: {game_id} ({processed_count + 1})")
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

                print(f"📊 Game {game_id} generated {len(features)} features")

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
        return processed_count

    except Exception as e:
        session.rollback()
        print(f"❌ Error in chunk processing: {e} {traceback.format_exc()}")
        if e.__cause__:
            print(f"🔍 Error cause: {e.__cause__}")
        return processed_count
    finally:
        session.close()


def chunkify(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def main(max_games, source=None, start_offset=0):
    games_repo = GamesRepository()

    all_games = []

    try:
        offset = start_offset  # Start from the provided offset
        processed_hashes = load_processed_hashes()

        print(f"🔍 Starting feature generation process...")
        if source:
            print(f"📋 Filtering by source: {source}")
        print(f"🎯 Maximum games to process: {max_games}")
        print(f"📊 Starting offset: {start_offset}")
        print(f"📊 Already processed games: {len(processed_hashes)}")

        while len(all_games) < max_games:
            # Calculate how many more games we need
            remaining_games = max_games - len(all_games)
            fetch_limit = min(FEATURES_PER_CHUNK, remaining_games)

            # Use the method that supports source filtering and excludes already processed games
            current_chunk = games_repo.get_games_by_pagination_not_analyzed(
                analyzed_hashes=processed_hashes,
                offset=offset,
                limit=fetch_limit,
                source=source
            )
            if not current_chunk:
                print(
                    f"🔍 No more games available. Retrieved {len(all_games)} games total.")
                break

            # Only add the games we need to reach max_games
            games_to_add = current_chunk[:remaining_games]
            all_games.extend(games_to_add)
            offset += len(games_to_add)

            print(
                f"📥 Retrieved {len(games_to_add)} games (total: {len(all_games)}/{max_games})")

            # Break if we've reached our limit
            if len(all_games) >= max_games:
                break
    except Exception as e:
        print(f"⚠️ Error getting games: {e}")
        return

    if not all_games:
        print("🔍 No games to process.")
        return

    # Ensure we don't process more than max_games
    all_game_pgns = all_games[:max_games]
    print(
        f"📊 Total games to process (limited to max_games): {len(all_game_pgns)}")

    # For precise control with small numbers, always process sequentially
    if max_games <= 50:
        print("🔄 Processing games sequentially for precise control...")
        actual_processed = process_chunk(
            all_game_pgns, max_to_process=max_games)
        print(f"📊 Actually processed: {actual_processed} games")
    else:
        chunks = list(chunkify(all_game_pgns, FEATURES_PER_CHUNK))
        print(f"🧩 Total chunks to process: {len(chunks)}")

        total_processed = 0
        for i, chunk in enumerate(chunks, 1):
            remaining_to_process = max_games - total_processed
            if remaining_to_process <= 0:
                print(f"🛑 Reached max_games limit of {max_games}. Stopping.")
                break

            print(f"⏳ Processing chunk {i}/{len(chunks)}...")
            chunk_processed = process_chunk(
                chunk, max_to_process=remaining_to_process)
            total_processed += chunk_processed
            print(
                f"✅ Completed chunk {i}/{len(chunks)} - Processed: {chunk_processed} (Total: {total_processed})")

    print("✅ Parallel feature generation completed.")


def get_all_sources(games_repo):
    """Get all unique sources from the games table."""
    try:
        return games_repo.get_all_sources()
    except Exception as e:
        print(f"❌ Error fetching sources: {e}")
        return []


def process_all_sources(batch_size=10000):
    games_repo = GamesRepository()
    sources = get_all_sources(games_repo)
    if not sources:
        print("❌ No sources found in the games table.")
        return
    print(f"🔎 Found sources: {sources}")

    for source in sources:
        print(f"\n=== Processing source: {source} ===")
        offset = 0
        total_processed_for_source = 0

        while True:
            print(
                f"\n➡️  Processing batch from offset {offset} (batch size: {batch_size}) for source '{source}'...")

            # Get processed count before this batch
            processed_hashes_before = load_processed_hashes()
            initial_count = len(processed_hashes_before)

            # Process the batch
            main(max_games=batch_size, source=source, start_offset=offset)

            # Get processed count after this batch
            processed_hashes_after = load_processed_hashes()
            final_count = len(processed_hashes_after)

            # Calculate how many were actually processed in this batch
            batch_processed = final_count - initial_count
            total_processed_for_source += batch_processed

            print(
                f"📊 Batch processed {batch_processed} games. Total for source '{source}': {total_processed_for_source}")

            # If no games were processed in this batch, we're done with this source
            if batch_processed == 0:
                print(
                    f"✅ All games processed for source '{source}'. Total: {total_processed_for_source}")
                break

            offset += batch_size

    print("\n✅ All sources processed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import chess games and generate features in parallel.")
    parser.add_argument('--max-games', required=False, default=10, type=int,
                        help='Maximum number of games to process (optional, for testing)')
    parser.add_argument('--source', required=False, default=None, type=str,
                        help='Filter games by source (optional). Examples: "personal", "novice", "elite", "fide", "stockfish"')
    parser.add_argument('--offset', required=False, default=0, type=int,
                        help='Starting offset for game pagination (optional, for batch processing)')
    parser.add_argument('--all-sources', action='store_true',
                        help='Process all sources sequentially in batches of 10,000 games each')
    args = parser.parse_args()

    try:
        if not DB_URL:
            raise ValueError(
                "CHESS_TRAINER_DB_URL environment variable is not set.")

        if args.all_sources:
            process_all_sources(batch_size=10000)
        else:
            print(f"🚀 Starting parallel feature generation...")
            print(f"📋 Parameters:")
            print(f"   - Max games: {args.max_games}")
            print(
                f"   - Source filter: {args.source if args.source else 'All sources'}")
            print(f"   - Starting offset: {args.offset}")
            print(f"   - Max workers: {MAX_WORKERS}")
            print(f"   - Features per chunk: {FEATURES_PER_CHUNK}")

            main(max_games=args.max_games,
                 source=args.source, start_offset=args.offset)
    except Exception as e:
        print(f"❌ Error during import: {e}")
        if e.__cause__:
            print(f"🔍 Cause: {e.__cause__}")
        sys.exit(1)
