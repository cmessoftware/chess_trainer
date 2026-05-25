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

    # Process games of a specific player (exact name match)
    python generate_features_with_tactics.py --player sergio --max-games 200

    # Combine filters: source + player
    python generate_features_with_tactics.py --source personal --player magnus --max-games 100

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
from datetime import datetime, timedelta
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

# Set Stockfish path if not already set
if not os.environ.get("STOCKFISH_PATH"):
    stockfish_path = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "stockfish.exe")
    if os.path.exists(stockfish_path):
        os.environ["STOCKFISH_PATH"] = stockfish_path
        print(f"Set STOCKFISH_PATH to: {stockfish_path}")
    else:
        print("Warning: Stockfish not found, tactical analysis may fail")

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
        
        # Generate tactical analysis (pass game_id as second parameter)
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
                        logger.error(f"[ERROR] Game {game_id}: {error}")
                        error_count += 1
                        continue
                    
                    if not result:
                        logger.warning(f"[WARNING] No result for game {game_id}")
                        error_count += 1
                        continue
                    
                    # Save features
                    features_saved = False
                    if result.get('features'):
                        try:
                            features_repo.save_many_features(result['features'])
                            features_saved = True
                        except Exception as save_error:
                            logger.error(f"[ERROR] Failed to save features for {game_id}: {save_error}")
                            error_count += 1
                            continue
                        
                    # Update features with tactical analysis if available
                    if result.get('tactics'):
                        try:
                            features_repo.update_tactical_data(result['tactics'])
                        except Exception as tact_error:
                            logger.warning(f"[WARNING] Failed to save tactics for {game_id}: {tact_error}")
                    
                    # Only mark as processed if features were successfully saved
                    if features_saved:
                        try:
                            processed_repo.mark_as_processed(game_id)
                            processed_count += 1
                            
                            if processed_count % 10 == 0:
                                logger.info(f"[SUCCESS] Processed {processed_count} games in chunk")
                        except Exception as mark_error:
                            logger.warning(f"[WARNING] Features saved but failed to mark as processed for {game_id}: {mark_error}")
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"[ERROR] Error processing game {game_id}: {e}")
                    error_count += 1
        
        # Commit all changes
        session.commit()
        logger.info(f"[COMPLETE] Chunk completed: {processed_count} processed, {error_count} errors")
        
    except Exception as e:
        logger.error(f"[ERROR] Chunk processing error: {e}")
        session.rollback()
        
    finally:
        session.close()
    
    return processed_count, error_count

def get_games_to_process(source=None, batch_id=None, since_minutes=None, max_games=1000, offset=0, player_name=None):
    """Get games from database that need processing.
    
    Args:
        source: Filter by source (personal, elite, etc.)
        batch_id: Filter by import batch ID
        since_minutes: Only process games imported in last N minutes
        max_games: Maximum number of games to process
        offset: Offset for pagination
        player_name: Filter by specific player name (white or black)
    """
    Session = sessionmaker(bind=create_engine(DB_URL))
    session = Session()
    
    try:
        games_repo = GamesRepository(session_factory=lambda: session)
        
        # Use direct SQL to get ONLY games without features (more efficient)
        from sqlalchemy import text
        query = """
            SELECT g.game_id, g.pgn, g.source 
            FROM games g
            LEFT JOIN features f ON g.game_id = f.game_id
            WHERE f.game_id IS NULL
        """
        
        # Add filters
        params = {}
        if batch_id:
            query += " AND g.import_batch_id = :batch_id"
            params['batch_id'] = batch_id
        elif since_minutes:
            since_timestamp = datetime.now() - timedelta(minutes=since_minutes)
            query += " AND g.import_date >= :since_timestamp"
            params['since_timestamp'] = since_timestamp
            if source:
                query += " AND g.source = :source"
                params['source'] = source
        elif source:
            query += " AND g.source = :source"
            params['source'] = source
        
        # Add player filter if specified (exact match)
        if player_name:
            query += " AND (g.white_player = :player_name OR g.black_player = :player_name)"
            params['player_name'] = player_name
        
        # Add pagination
        query += " ORDER BY g.game_id LIMIT :limit OFFSET :offset"
        params['limit'] = max_games
        params['offset'] = offset
        
        result = session.execute(text(query), params)
        rows = result.fetchall()
        
        unprocessed_games = [(row[0], row[1], row[2] or 'unknown') for row in rows]
        logger.info(f"[QUERY] Found {len(unprocessed_games)} games WITHOUT features (offset={offset}, limit={max_games})")
        
        return unprocessed_games
        
    except Exception as e:
        logger.error(f"[ERROR] Error getting games: {e}")
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

  # Process games of a specific player (exact name match)
  python generate_features_with_tactics.py --player sergio --max-games 200

  # Combine filters: source + player
  python generate_features_with_tactics.py --source personal --player magnus --max-games 100

  # Process with custom workers
  python generate_features_with_tactics.py --source fide --max-games 5000 --workers 6
        """
    )
    
    # Declare global variables first
    global MAX_WORKERS, FEATURES_PER_CHUNK
    
    parser.add_argument('--batch-id', help='Filter by import batch ID (specific upload)')
    parser.add_argument('--since-minutes', type=int, help='Only process games imported in last N minutes')
    parser.add_argument('--source', help='Filter by game source (lichess, chess.com, fide, elite, etc.)')
    parser.add_argument('--player', help='Filter by player name (exact match, searches white and black)')
    parser.add_argument('--max-games', type=int, default=1000, help='Maximum number of games to process')
    parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help='Number of parallel workers')
    parser.add_argument('--chunk-size', type=int, default=FEATURES_PER_CHUNK, help='Games per chunk')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update configuration
    MAX_WORKERS = args.workers
    FEATURES_PER_CHUNK = args.chunk_size
    
    logger.info("Starting integrated feature generation + tactical analysis...")
    logger.info(f"Parameters:")
    if args.batch_id:
        logger.info(f"   - Batch ID: {args.batch_id}")
    if args.since_minutes:
        logger.info(f"   - Since minutes: {args.since_minutes}")
    if args.player:
        logger.info(f"   - Player: {args.player}")
    logger.info(f"   - Source: {args.source or 'ALL'}")
    logger.info(f"   - Max games: {args.max_games}")
    logger.info(f"   - Workers: {MAX_WORKERS}")
    logger.info(f"   - Chunk size: {FEATURES_PER_CHUNK}")
    
    start_time = time.time()
    
    try:
        # Get games to process
        games_to_process = get_games_to_process(
            source=args.source,
            batch_id=getattr(args, 'batch_id', None),
            since_minutes=getattr(args, 'since_minutes', None),
            max_games=args.max_games,
            offset=args.offset,
            player_name=getattr(args, 'player', None)
        )
        
        if not games_to_process:
            logger.warning("[WARNING] No games found to process")
            return
        
        # Process games in chunks
        total_processed = 0
        total_errors = 0
        
        for i in range(0, len(games_to_process), FEATURES_PER_CHUNK):
            chunk = games_to_process[i:i + FEATURES_PER_CHUNK]
            chunk_num = i // FEATURES_PER_CHUNK + 1
            total_chunks = (len(games_to_process) + FEATURES_PER_CHUNK - 1) // FEATURES_PER_CHUNK
            
            logger.info(f"[PROCESS] Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} games)")
            
            processed, errors = process_chunk(chunk)
            total_processed += processed
            total_errors += errors
            
            logger.info(f"[SUCCESS] Chunk {chunk_num} completed: {processed} processed, {errors} errors")
        
        # Final summary
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"[COMPLETE] Processing completed!")
        logger.info(f"[SUMMARY] Summary:")
        logger.info(f"   - Total games processed: {total_processed}")
        logger.info(f"   - Total errors: {total_errors}")
        logger.info(f"   - Duration: {duration:.2f} seconds")
        logger.info(f"   - Games per second: {total_processed / duration:.2f}")
        
        if total_errors > 0:
            logger.warning(f"[WARNING] {total_errors} games had errors during processing")
        
    except Exception as e:
        logger.error(f"[FATAL] Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
