#!/usr/bin/env python3
"""
Script ultra-simple para generar features básicas sin dependencias que puedan tener emojis.
"""

import os
import sys
import time
import logging
import chess
import chess.pgn
import io
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
src_path = Path(__file__).parent.parent
sys.path.insert(0, str(src_path))

# Import required modules
from db.repository.games_repository import GamesRepository
from db.repository.features_repository import FeaturesRepository
from db.repository.processed_feature_repository import ProcessedFeaturesRepository

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def parse_pgn_string(pgn_str):
    """Parse PGN string to game object."""
    try:
        return chess.pgn.read_game(io.StringIO(pgn_str))
    except Exception as e:
        logger.error(f"Error parsing PGN: {e}")
        return None

def extract_basic_features(game, game_id):
    """Extract basic features from a chess game."""
    if not game:
        return []
    
    features = []
    board = chess.Board()
    
    # Basic piece values
    values = {
        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
        chess.ROOK: 5, chess.QUEEN: 9
    }
    
    for move_number, move in enumerate(game.mainline_moves(), 1):
        if not board.is_legal(move):
            logger.warning(f"Illegal move in game {game_id}: {move}")
            break
        
        try:
            # Basic position info
            fen = board.fen()
            move_san = board.san(move)
            move_uci = move.uci()
            player_color = int(chess.WHITE) if board.turn else int(chess.BLACK)
            
            # Material calculation
            material_balance = sum(
                values.get(piece.piece_type, 0) * (1 if piece.color else -1)
                for piece in board.piece_map().values()
            )
            material_total = sum(
                values.get(p.piece_type, 0) for p in board.piece_map().values()
            )
            
            # Mobility
            legal_moves = list(board.legal_moves)
            self_mobility = len(legal_moves)
            
            # Make the move and calculate opponent mobility
            board.push(move)
            opponent_mobility = len(list(board.legal_moves))
            
            # Count pieces (excluding pawns and kings for simplicity)
            num_pieces = sum(1 for p in board.piece_map().values()
                           if p.piece_type not in [chess.KING, chess.PAWN])
            
            # Simple phase detection
            piece_count = len(board.piece_map())
            if piece_count >= 24:
                phase = "opening"
            elif piece_count >= 12:
                phase = "middlegame" 
            else:
                phase = "endgame"
            
            # Create feature dictionary
            feature = {
                'game_id': game_id,
                'move_number': move_number,
                'player_color': player_color,
                'fen': fen,
                'move_san': move_san,
                'move_uci': move_uci,
                'material_balance': material_balance,
                'material_total': material_total,
                'num_pieces': num_pieces,
                'branching_factor': self_mobility + opponent_mobility,
                'self_mobility': self_mobility,
                'opponent_mobility': opponent_mobility,
                'phase': phase,
                'has_castling_rights': int(board.has_castling_rights(chess.WHITE if board.turn else chess.BLACK)),
                'move_number_global': move_number,
                'is_repetition': int(board.is_repetition()),
                'is_low_mobility': int(self_mobility <= 5),
                'is_center_controlled': 0,  # Simplified
                'is_pawn_endgame': 0,  # Simplified
                'tags': None,
                'score_diff': None,
                'site': game.headers.get('Site', ''),
                'event': game.headers.get('Event', ''),
                'date': game.headers.get('Date', ''),
                'white_player': game.headers.get('White', ''),
                'black_player': game.headers.get('Black', ''),
                'result': game.headers.get('Result', ''),
                'num_moves': len(list(game.mainline_moves())),
                'is_stockfish_test': False
            }
            
            features.append(feature)
            
            # We already pushed the move above
            
        except Exception as e:
            logger.error(f"Error processing move {move} in game {game_id}: {e}")
            break
    
    return features

def main():
    """Main function to process games and generate features."""
    logger.info("Starting ultra-simple feature generation...")
    
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
    MAX_GAMES = 200  # Process more games
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
            logger.info(f"Processing game {game_id[:8]}... from {source}")
            
            # Parse game
            game = parse_pgn_string(pgn)
            if not game:
                logger.warning(f"Could not parse game {game_id[:8]}")
                error_count += 1
                continue
            
            # Generate features
            features = extract_basic_features(game, game_id)
            
            if features:
                # Save features
                features_repo.save_many_features(features)
                
                # Mark as processed
                processed_repo.save_processed_hash(game_id)
                
                processed_count += 1
                logger.info(f"[SUCCESS] Processed game {game_id[:8]} - {len(features)} features")
            else:
                logger.warning(f"[WARNING] No features generated for game {game_id[:8]}")
                error_count += 1
                
        except Exception as e:
            logger.error(f"[ERROR] Error processing game {game_id[:8]}: {e}")
            error_count += 1
    
    logger.info(f"[COMPLETE] Feature generation completed!")
    logger.info(f"[SUMMARY] Summary:")
    logger.info(f"   - Total games processed: {processed_count}")
    logger.info(f"   - Total errors: {error_count}")

if __name__ == "__main__":
    main()
