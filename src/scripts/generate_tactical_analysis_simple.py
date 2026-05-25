#!/usr/bin/env python3
"""
Simple Tactical Analysis Script (No Multiprocessing)

This script adds tactical analysis to existing features in the database.
It processes games sequentially to avoid Windows multiprocessing issues.
"""

import os
import sys
import time
import traceback
from sqlalchemy import create_engine
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

# Set Stockfish path
stockfish_path = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "stockfish.exe")
if os.path.exists(stockfish_path):
    os.environ["STOCKFISH_PATH"] = stockfish_path
    print(f"Set STOCKFISH_PATH to: {stockfish_path}")
else:
    print("Warning: Stockfish not found, tactical analysis may fail")

def process_game_for_tactics(game_id, pgn_text):
    """Process a single game to generate tactical analysis."""
    try:
        # Parse PGN
        game = pgn_str_to_game(pgn_text)
        if not game:
            return None, f"Failed to parse PGN for game {game_id}"
        
        # Generate tactical analysis with minimal depth for speed
        print(f"Analyzing game {game_id}...")
        tactics = detect_tactics_from_game(game, game_id, depth=6)
        
        if not tactics:
            return None, f"No tactical patterns found for game {game_id}"
            
        return tactics, None
        
    except Exception as e:
        error_msg = f"Error processing game {game_id}: {str(e)}"
        print(error_msg)
        return None, error_msg

def update_features_with_tactics(features_repo, tactics_list, game_id):
    """Update existing features with tactical data."""
    try:
        for tactic in tactics_list:
            move_number = tactic.get('move_number')
            fen = tactic.get('fen')
            player_color = tactic.get('player_color')
            
            if not move_number or not fen or player_color is None:
                continue
                
            # Find the corresponding feature record
            feature = features_repo.get_by_game_and_move(game_id, move_number)
            
            if feature:
                # Update with tactical data - use composite key since there's no single id
                tactical_data = {
                    'tag': tactic.get('tag'),
                    'error_label': tactic.get('error_label'),
                    'score_diff': tactic.get('score_diff'),
                    'player_color': tactic.get('player_color')
                }
                
                # Update directly using the composite key
                success = features_repo.update_feature_by_composite_key(
                    game_id, move_number, player_color, tactical_data
                )
                
                if success:
                    print(f"Updated feature for game {game_id}, move {move_number} with tactical data: {tactic.get('tag')}")
                else:
                    print(f"Failed to update feature for game {game_id}, move {move_number}")
            else:
                print(f"No feature found for game {game_id}, move {move_number}")
                
    except Exception as e:
        print(f"Error updating features: {e}")

def main():
    print("Starting simple tactical analysis...")
    start_time = time.time()
    
    # Create database session
    Session = sessionmaker(bind=create_engine(DB_URL))
    session = Session()
    
    try:
        # Initialize repositories
        games_repo = GamesRepository(session_factory=lambda: session)
        features_repo = FeaturesRepository(session_factory=lambda: session)
        
        # Get games that have features but no tactical analysis yet
        print("Finding games to analyze...")
        
        # Get a sample of games to process (start with 20 games)
        games = games_repo.get_games_by_pagination(offset=0, limit=20)
        print(f"Found {len(games)} games to analyze")
        
        processed_count = 0
        error_count = 0
        
        for game in games:
            print(f"\n--- Processing game {game.game_id} ({processed_count + 1}/{len(games)}) ---")
            
            # Check if this game already has features
            existing_features = features_repo.get_by_game_id(game.game_id)
            if not existing_features:
                print(f"No features found for game {game.game_id}, skipping...")
                continue
            
            # Check if tactical analysis already exists
            has_tactical = any(f.tags and 'pin' in str(f.tags) or 'fork' in str(f.tags) or 'check' in str(f.tags) 
                             for f in existing_features)
            if has_tactical:
                print(f"Game {game.game_id} already has tactical analysis, skipping...")
                continue
            
            # Process game for tactical analysis
            tactics, error = process_game_for_tactics(game.game_id, game.pgn)
            
            if error:
                print(f"Error: {error}")
                error_count += 1
                continue
            
            if not tactics:
                print(f"No tactics found for game {game.game_id}")
                continue
            
            print(f"Found {len(tactics)} tactical patterns")
            
            # Update features with tactical data
            update_features_with_tactics(features_repo, tactics, game.game_id)
            
            processed_count += 1
            
            # Commit after each game to avoid losing work
            session.commit()
            
            print(f"Completed game {game.game_id}")
        
        # Final summary
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n=== SUMMARY ===")
        print(f"Total games processed: {processed_count}")
        print(f"Total errors: {error_count}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Average time per game: {duration/len(games):.2f} seconds")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
        session.rollback()
        
    finally:
        session.close()

if __name__ == "__main__":
    main()
