#!/usr/bin/env python3
"""
Integrated Feature Generation + Tactical Analysis Script

This script combines feature generation and tactical analysis in a single process
to optimize performance and reduce database overhead. It processes games from the
PostgreSQL database and generates both features and tactical annotations.

Usage Examples:
    # Generate features + tactics for all games (max 1000)
    python generate_features_with_tactics.py

    # Process specific source with custom limits
    python generate_features_with_tactics.py --source elite --max-games 500

    # Process with custom worker count
    python generate_features_with_tactics.py --source fide --max-games 5000 --workers 6

Environment Variables:
    CHESS_TRAINER_DB_URL: PostgreSQL connection URL
    MAX_WORKERS: Number of parallel workers (default: 4)
    FEATURES_PER_CHUNK: Games per processing chunk (default: 100)

Features:
    - Integrated feature generation and tactical analysis
    - Parallel processing with configurable workers
    - Source-based filtering (lichess, chess.com, fide, elite, etc.)
    - Automatic detection of already processed games
    - Detailed progress reporting and error handling
    - PostgreSQL-based storage with transaction safety
"""

import argparse
import os
import sys
import time
import traceback
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.features_generator import generate_features_from_game
from modules.analyze_games_tactics import detect_tactics_from_game
from modules.pgn_utils import get_game_id, pgn_str_to_game
from db.repository.features_repository import FeaturesRepository
from db.repository.games_repository import GamesRepository
from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository
from db.repository.processed_feature_repository import ProcessedFeaturesRepository

# Load environment variables
import dotenv
dotenv.load_dotenv()

# Configuration
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
FEATURES_PER_CHUNK = int(os.environ.get("FEATURES_PER_CHUNK", 100))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("generate_features_with_tactics.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def process_game_with_tactics(game_data):
    """Process a single game to generate both features and tactical analysis."""
    game_id, pgn_text, source = game_data
    
    try:
        # Parse PGN
        game = pgn_str_to_game(pgn_text)
        if not game:
            return None, f"Failed to parse PGN for game {game_id}"
        
        # Generate features
        features = generate_features_from_game(game, game_id)
        if not features:
            return None, f"Failed to generate features for game {game_id}"
        
        # Generate tactical analysis
        tactics = detect_tactics_from_game(game, game_id)
        
        return {
            'game_id': game_id,
            'features': features,
            'tactics': tactics,
            'source': source
        }, None
        
    except Exception as e:
        error_msg = f"Error processing game {game_id}: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

def process_chunk(games_chunk):
    """Process a chunk of games in parallel."""
    Session = sessionmaker(bind=create_engine(DB_URL))
    session = Session()
    
    processed_count = 0
    error_count = 0
    
    try:
        # Initialize repositories
        features_repo = FeaturesRepository(session_factory=lambda: session)
        tactics_repo = Analyzed_tacticalsRepository(session_factory=lambda: session)
        processed_repo = ProcessedFeaturesRepository(session_factory=lambda: session)
        
        # Process games in chunk
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all games in chunk
            future_to_game = {
                executor.submit(process_game_with_tactics, game_data): game_data[0]
                for game_data in games_chunk
            }
            
            # Process results
            for future in as_completed(future_to_game):
                game_id = future_to_game[future]
                
                try:
                    result, error = future.result()
                    
                    if error:
                        logger.error(f"❌ Game {game_id}: {error}")
                        error_count += 1
                        continue
                    
                    if not result:
                        logger.warning(f"⚠️ No result for game {game_id}")
                        error_count += 1
                        continue
                    
                    # Save features
                    if result.get('features'):
                        features_repo.save_features(result['features'])
                        
                    # Save tactical analysis
                    if result.get('tactics'):
                        tactics_repo.save_tactical_analysis(result['tactics'])
                    
                    # Mark as processed
                    processed_repo.mark_as_processed(game_id)
                    
                    processed_count += 1
                    
                    if processed_count % 10 == 0:
                        logger.info(f"✅ Processed {processed_count} games in chunk")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing game {game_id}: {e}")
                    error_count += 1
        
        # Commit all changes
        session.commit()
        logger.info(f"🎉 Chunk completed: {processed_count} processed, {error_count} errors")
        
    except Exception as e:
        logger.error(f"❌ Chunk processing error: {e}")
        session.rollback()
        
    finally:
        session.close()
    
    return processed_count, error_count

def get_games_to_process(source=None, max_games=1000, offset=0):
    """Get games from database that need processing."""
    Session = sessionmaker(bind=create_engine(DB_URL))
    session = Session()
    
    try:
        games_repo = GamesRepository(session_factory=lambda: session)
        processed_repo = ProcessedFeaturesRepository(session_factory=lambda: session)
        
        # Get processed game IDs to skip
        processed_ids = set(processed_repo.get_all())
        logger.info(f"📊 Found {len(processed_ids)} already processed games")
        
        # Get games from database
        if source:
            games = games_repo.get_games_by_source(source, limit=max_games, offset=offset)
            logger.info(f"🎯 Found {len(games)} games from source '{source}'")
        else:
            games = games_repo.get_all_games(limit=max_games, offset=offset)
            logger.info(f"🎯 Found {len(games)} total games")
        
        # Filter out already processed games
        unprocessed_games = []
        for game in games:
            game_id = game.get('id') or get_game_id(game.get('pgn', ''))
            if game_id not in processed_ids:
                unprocessed_games.append((
                    game_id,
                    game.get('pgn', ''),
                    game.get('source', 'unknown')
                ))
        
        logger.info(f"📋 {len(unprocessed_games)} games need processing")
        return unprocessed_games
        
    except Exception as e:
        logger.error(f"❌ Error getting games: {e}")
        return []
        
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(
        description="Integrated Feature Generation + Tactical Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all games (max 1000)
  python generate_features_with_tactics.py

  # Process specific source
  python generate_features_with_tactics.py --source elite --max-games 500

  # Process with custom workers
  python generate_features_with_tactics.py --source fide --max-games 5000 --workers 6
        """
    )
    
    parser.add_argument('--source', help='Filter by game source (lichess, chess.com, fide, elite, etc.)')
    parser.add_argument('--max-games', type=int, default=1000, help='Maximum number of games to process')
    parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help='Number of parallel workers')
    parser.add_argument('--chunk-size', type=int, default=FEATURES_PER_CHUNK, help='Games per chunk')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update configuration
    global MAX_WORKERS, FEATURES_PER_CHUNK
    MAX_WORKERS = args.workers
    FEATURES_PER_CHUNK = args.chunk_size
    
    logger.info("🚀 Starting integrated feature generation + tactical analysis...")
    logger.info(f"📋 Parameters:")
    logger.info(f"   - Source: {args.source or 'ALL'}")
    logger.info(f"   - Max games: {args.max_games}")
    logger.info(f"   - Workers: {MAX_WORKERS}")
    logger.info(f"   - Chunk size: {FEATURES_PER_CHUNK}")
    
    start_time = time.time()
    
    try:
        # Get games to process
        games_to_process = get_games_to_process(
            source=args.source,
            max_games=args.max_games,
            offset=args.offset
        )
        
        if not games_to_process:
            logger.warning("⚠️ No games found to process")
            return
        
        # Process games in chunks
        total_processed = 0
        total_errors = 0
        
        for i in range(0, len(games_to_process), FEATURES_PER_CHUNK):
            chunk = games_to_process[i:i + FEATURES_PER_CHUNK]
            chunk_num = i // FEATURES_PER_CHUNK + 1
            total_chunks = (len(games_to_process) + FEATURES_PER_CHUNK - 1) // FEATURES_PER_CHUNK
            
            logger.info(f"🔄 Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} games)")
            
            processed, errors = process_chunk(chunk)
            total_processed += processed
            total_errors += errors
            
            logger.info(f"✅ Chunk {chunk_num} completed: {processed} processed, {errors} errors")
        
        # Final summary
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"🎉 Processing completed!")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Total games processed: {total_processed}")
        logger.info(f"   - Total errors: {total_errors}")
        logger.info(f"   - Duration: {duration:.2f} seconds")
        logger.info(f"   - Games per second: {total_processed / duration:.2f}")
        
        if total_errors > 0:
            logger.warning(f"⚠️ {total_errors} games had errors during processing")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
