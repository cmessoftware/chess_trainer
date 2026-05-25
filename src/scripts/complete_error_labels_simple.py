#!/usr/bin/env python3
"""
Complete Error Labels Script (Windows Compatible)

This script processes existing features in the database that lack error_label
by running tactical analysis on their corresponding games.

Usage:
    python complete_error_labels_simple.py --limit 50
    python complete_error_labels_simple.py --limit 500 --workers 2
"""

import argparse
import os
import sys
import time
import traceback
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.analyze_games_tactics import detect_tactics_from_game
from modules.pgn_utils import pgn_str_to_game
from db.repository.features_repository import FeaturesRepository
from db.repository.games_repository import GamesRepository

# Load environment variables
import dotenv
dotenv.load_dotenv()

# Configuration
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")

# Set Stockfish path if not already set
if not os.environ.get("STOCKFISH_PATH"):
    stockfish_path = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "stockfish.exe")
    if os.path.exists(stockfish_path):
        os.environ["STOCKFISH_PATH"] = stockfish_path
        print(f"[OK] Set STOCKFISH_PATH to: {stockfish_path}")
    else:
        print("[WARNING] Stockfish not found, tactical analysis may fail")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("complete_error_labels.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def process_game_for_error_labels(game_data):
    """Process a single game to complete missing error_labels."""
    game_id, pgn_text = game_data
    
    try:
        # Parse PGN
        game = pgn_str_to_game(pgn_text)
        if not game:
            return None, f"Failed to parse PGN for game {game_id}"
        
        # Generate tactical analysis
        logger.info(f"[ANALYZING] Processing game {game_id}...")
        tactics = detect_tactics_from_game(game, game_id, depth=8)
        
        if not tactics:
            return None, f"No tactical analysis generated for game {game_id}"
        
        return {
            'game_id': game_id,
            'tactics': tactics
        }, None
        
    except Exception as e:
        error_msg = f"Error processing game {game_id}: {str(e)}"
        logger.error(error_msg)
        return None, error_msg

def update_features_with_error_labels(features_repo, tactics, game_id):
    """Update existing features with error_label from tactical analysis."""
    updated_count = 0
    
    try:
        for tactic in tactics:
            move_number = tactic.get('move_number')
            player_color = tactic.get('player_color')
            
            if not move_number or not player_color:
                continue
                
            # Find the corresponding feature record
            feature = features_repo.get_by_game_and_move(game_id, move_number)
            
            if feature:
                # Update with error_label from tactical analysis
                tactical_data = {
                    'error_label': tactic.get('error_label'),
                    'tag': tactic.get('tag', ''),
                    'score_diff': tactic.get('score_diff', 0)
                }
                
                # Update directly using the composite key
                success = features_repo.update_feature_by_composite_key(
                    game_id, move_number, player_color, tactical_data
                )
                
                if success:
                    updated_count += 1
                    logger.debug(f"[OK] Updated feature for game {game_id}, move {move_number}: {tactic.get('error_label')}")
                else:
                    logger.warning(f"[ERROR] Failed to update feature for game {game_id}, move {move_number}")
            else:
                logger.warning(f"[WARNING] No feature found for game {game_id}, move {move_number}")
                
    except Exception as e:
        logger.error(f"Error updating features for game {game_id}: {e}")
        
    return updated_count

def main():
    parser = argparse.ArgumentParser(description='Complete missing error_label values in features')
    parser.add_argument('--limit', type=int, default=50, help='Maximum number of games to process')
    parser.add_argument('--workers', type=int, default=1, help='Number of parallel workers')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"[START] Starting error_label completion process...")
    logger.info(f"[PARAMS] Parameters:")
    logger.info(f"   - Limit: {args.limit} games")
    logger.info(f"   - Workers: {args.workers}")
    
    start_time = time.time()
    
    # Create database session
    Session = sessionmaker(bind=create_engine(DB_URL))
    session = Session()
    
    try:
        # Initialize repositories
        games_repo = GamesRepository(session_factory=lambda: session)
        features_repo = FeaturesRepository(session_factory=lambda: session)
        
        # Get games that have features without error_label
        logger.info("[QUERY] Finding games with unlabeled features...")
        
        # Query for distinct games that have features without error_label
        query = text("""
        SELECT DISTINCT g.game_id, g.pgn
        FROM games g
        JOIN features f ON g.game_id = f.game_id
        WHERE f.error_label IS NULL OR f.error_label = ''
        LIMIT :limit
        """)
        
        result = session.execute(query, {"limit": args.limit})
        games_data = [(row[0], row[1]) for row in result.fetchall()]
        
        logger.info(f"[FOUND] Found {len(games_data)} games with unlabeled features")
        
        if not games_data:
            logger.info("[COMPLETE] No games found that need error_label completion")
            return
        
        total_processed = 0
        total_errors = 0
        total_updated_features = 0
        
        # Process games sequentially (safer for Windows)
        for i, game_data in enumerate(games_data, 1):
            logger.info(f"[PROCESS] Processing game {i}/{len(games_data)}: {game_data[0]}")
            
            result, error = process_game_for_error_labels(game_data)
            
            if error:
                logger.error(f"[ERROR] Game {game_data[0]}: {error}")
                total_errors += 1
                continue
            
            if not result:
                logger.warning(f"[WARNING] No result for game {game_data[0]}")
                total_errors += 1
                continue
            
            # Update features with error_labels
            updated_count = update_features_with_error_labels(
                features_repo, result['tactics'], result['game_id']
            )
            
            total_updated_features += updated_count
            total_processed += 1
            
            # Commit after each game
            session.commit()
            
            logger.info(f"[OK] Completed game {result['game_id']}: {updated_count} features updated")
        
        # Final summary
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"\\n[SUMMARY] === COMPLETION SUMMARY ===")
        logger.info(f"[STATS] Total games processed: {total_processed}")
        logger.info(f"[STATS] Total features updated: {total_updated_features}")
        logger.info(f"[STATS] Total errors: {total_errors}")
        logger.info(f"[STATS] Duration: {duration:.2f} seconds")
        if total_processed > 0:
            logger.info(f"[STATS] Average time per game: {duration/total_processed:.2f} seconds")
            logger.info(f"[STATS] Average features per game: {total_updated_features/total_processed:.1f}")
        
        if total_errors > 0:
            logger.warning(f"[WARNING] {total_errors} games had errors during processing")
        
    except Exception as e:
        logger.error(f"[FATAL] Fatal error: {e}")
        traceback.print_exc()
        session.rollback()
        sys.exit(1)
        
    finally:
        session.close()

if __name__ == "__main__":
    main()