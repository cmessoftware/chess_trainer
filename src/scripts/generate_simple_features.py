#!/usr/bin/env python3
"""
Script simplificado para generar features básicas sin análisis táctico.
Usado para poblar la tabla features con datos iniciales.
"""

import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Import required modules
from db.repository.games_repository import GamesRepository
from db.repository.features_repository import FeaturesRepository
from db.repository.processed_feature_repository import ProcessedFeaturesRepository
from modules.features_generator import generate_features_from_game
from modules.pgn_utils import load_pgn_from_string

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def generate_simple_features(game_id: str, pgn: str, source: str) -> list:
    """Generate basic chess features without tactical analysis."""
    try:
        # Parse PGN string to game object
        game = load_pgn_from_string(pgn)
        if not game:
            logger.error(f"Could not parse PGN for game {game_id}")
            return []
        
        # Generate features using existing function
        features = generate_features_from_game(game, game_id)
        
        # Convert to list format expected by save_many_features
        feature_list = []
        for feature in features:
            # Add missing fields with defaults
            feature_dict = {
                'game_id': feature.get('game_id'),
                'move_number': feature.get('move_number'),
                'player_color': feature.get('player_color'),
                'fen': feature.get('fen'),
                'move_san': feature.get('move_san'),
                'move_uci': feature.get('move_uci'),
                'material_balance': feature.get('material_balance'),
                'material_total': feature.get('material_total'),
                'num_pieces': feature.get('num_pieces'),
                'branching_factor': feature.get('branching_factor'),
                'self_mobility': feature.get('self_mobility'),
                'opponent_mobility': feature.get('opponent_mobility'),
                'phase': feature.get('phase'),
                'has_castling_rights': feature.get('has_castling_rights'),
                'move_number_global': feature.get('move_number_global'),
                'is_repetition': feature.get('is_repetition'),
                'is_low_mobility': feature.get('is_low_mobility'),
                'is_center_controlled': feature.get('is_center_controlled'),
                'is_pawn_endgame': feature.get('is_pawn_endgame'),
                'tags': None,  # Not in basic features
                'score_diff': feature.get('score_diff'),
                'site': feature.get('site'),
                'event': feature.get('event'),
                'date': feature.get('date'),
                'white_player': feature.get('white_player'),
                'black_player': feature.get('black_player'),
                'result': feature.get('result'),
                'num_moves': feature.get('num_moves'),
                'is_stockfish_test': feature.get('is_stockfish_test', False)
            }
            feature_list.append(feature_dict)
        
        return feature_list
    except Exception as e:
        logger.error(f"Error generating features for game {game_id}: {e}")
        return []

def main():
    """Main function to process games and generate features."""
    logger.info("Starting simple feature generation...")
    
    # Initialize repositories
    games_repo = GamesRepository()
    features_repo = FeaturesRepository()
    processed_repo = ProcessedFeaturesRepository()
    
    # Get processed games to avoid duplicates
    try:
        processed_ids = set(processed_repo.get_all())
        logger.info(f"Found {len(processed_ids)} already processed games")
    except Exception as e:
        logger.warning(f"Could not get processed games: {e}")
        processed_ids = set()
    
    # Get games to process
    MAX_GAMES = 100  # Start with small batch
    games = games_repo.get_games_by_pagination(offset=0, limit=MAX_GAMES)
    logger.info(f"Found {len(games)} games to process")
    
    # Filter unprocessed games
    unprocessed_games = []
    for game in games:
        if game.game_id not in processed_ids:
            unprocessed_games.append((game.game_id, game.pgn, game.source or 'unknown'))
    
    logger.info(f"Processing {len(unprocessed_games)} unprocessed games")
    
    processed_count = 0
    error_count = 0
    
    for game_id, pgn, source in unprocessed_games:
        try:
            logger.info(f"Processing game {game_id} from {source}")
            
            # Generate features
            features = generate_simple_features(game_id, pgn, source)
            
            if features:
                # Save features
                features_repo.save_many_features(features)
                
                # Mark as processed
                processed_repo.save_processed_hash(game_id)
                
                processed_count += 1
                logger.info(f"[SUCCESS] Processed game {game_id} - {len(features)} features")
            else:
                logger.warning(f"[WARNING] No features generated for game {game_id}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"[ERROR] Error processing game {game_id}: {e}")
            error_count += 1
    
    logger.info(f"[COMPLETE] Feature generation completed!")
    logger.info(f"[SUMMARY] Summary:")
    logger.info(f"   - Total games processed: {processed_count}")
    logger.info(f"   - Total errors: {error_count}")

if __name__ == "__main__":
    main()
