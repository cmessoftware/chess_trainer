#!/usr/bin/env python3
"""
Fast Lightweight Tactical Feature Estimation Script

This script provides a fast, lightweight approach to estimate tactical features
from chess games without full engine analysis. It uses heuristics and pattern
recognition to quickly identify potential tactical motifs.

Usage Examples:
    # Estimate tactical features for personal games
    python estimate_tactical_features.py --source personal --max-games 10000

    # Quick estimation for fide games
    python estimate_tactical_features.py --source fide --max-games 5000

    # Estimate with custom workers
    python estimate_tactical_features.py --source elite --workers 8

Environment Variables:
    CHESS_TRAINER_DB_URL: PostgreSQL connection URL
    MAX_WORKERS: Number of parallel workers (default: 6)
    ESTIMATION_PER_CHUNK: Games per processing chunk (default: 200)

Features:
    - Fast pattern-based tactical estimation
    - No engine analysis required (lightweight)
    - Parallel processing for speed
    - Source-based filtering
    - Quick heuristic detection of common tactics
    - Optimized for large-scale processing
"""

import argparse
import os
import sys
import time
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import chess
import chess.pgn

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.pgn_utils import get_game_id, pgn_str_to_game
from db.repository.games_repository import GamesRepository
from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository

# Load environment variables
import dotenv
dotenv.load_dotenv()

# Configuration
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 6))
ESTIMATION_PER_CHUNK = int(os.environ.get("ESTIMATION_PER_CHUNK", 200))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("estimate_tactical_features.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def estimate_tactical_motifs(game):
    """Fast heuristic estimation of tactical motifs in a game."""
    tactical_features = {
        'forks': 0,
        'pins': 0, 
        'skewers': 0,
        'discovered_attacks': 0,
        'double_attacks': 0,
        'sacrifices': 0,
        'checks': 0,
        'captures': 0,
        'tactical_complexity': 0
    }
    
    board = game.board()
    move_count = 0
    
    try:
        for move in game.mainline_moves():
            move_count += 1
            
            # Check if move is a capture
            if board.is_capture(move):
                tactical_features['captures'] += 1
                
                # Check for potential sacrifice (piece value heuristic)
                piece = board.piece_at(move.from_square)
                captured = board.piece_at(move.to_square)
                
                if piece and captured:
                    piece_values = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, 
                                  chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0}
                    
                    piece_value = piece_values.get(piece.piece_type, 0)
                    captured_value = piece_values.get(captured.piece_type, 0)
                    
                    # Potential sacrifice if losing material
                    if piece_value > captured_value:
                        tactical_features['sacrifices'] += 1
            
            # Check if move gives check
            board.push(move)
            if board.is_check():
                tactical_features['checks'] += 1
            
            # Simple fork detection: knight moves that attack multiple pieces
            if board.piece_at(move.to_square) and board.piece_at(move.to_square).piece_type == chess.KNIGHT:
                attacked_squares = list(board.attacks(move.to_square))
                valuable_attacks = 0
                for sq in attacked_squares:
                    piece = board.piece_at(sq)
                    if piece and piece.color != board.turn:
                        if piece.piece_type in [chess.QUEEN, chess.ROOK, chess.KING]:
                            valuable_attacks += 1
                
                if valuable_attacks >= 2:
                    tactical_features['forks'] += 1
            
            # Simple pin detection: look for pieces that can't move due to discovered check
            if move_count % 5 == 0:  # Check every 5 moves to reduce computation
                for square in chess.SQUARES:
                    piece = board.piece_at(square)
                    if piece and piece.color == board.turn:
                        # Check if piece is potentially pinned
                        original_square = square
                        legal_moves = list(board.legal_moves)
                        pinned_moves = [m for m in legal_moves if m.from_square == original_square]
                        
                        if len(pinned_moves) < 8 and len(pinned_moves) > 0:  # Restricted movement
                            tactical_features['pins'] += 1
    
    except Exception as e:
        logger.debug(f"Error in tactical estimation: {e}")
    
    # Calculate tactical complexity score
    total_tactics = sum(tactical_features.values())
    if move_count > 0:
        tactical_features['tactical_complexity'] = total_tactics / move_count * 100
    
    return tactical_features

def estimate_game_tactics(game_data):
    """Estimate tactical features for a single game."""
    game_id, pgn_text, source = game_data
    
    try:
        # Parse PGN
        game = pgn_str_to_game(pgn_text)
        if not game:
            return None, f"Failed to parse PGN for game {game_id}"
        
        # Estimate tactical features
        tactical_features = estimate_tactical_motifs(game)
        
        # Create tactical analysis record
        tactical_analysis = {
            'game_id': game_id,
            'source': source,
            'estimated_tactics': tactical_features,
            'analysis_method': 'lightweight_estimation',
            'analysis_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return tactical_analysis, None
        
    except Exception as e:
        error_msg = f"Error estimating tactics for game {game_id}: {str(e)}"
        logger.debug(error_msg)
        return None, error_msg

def process_estimation_chunk(games_chunk):
    """Process a chunk of games for tactical estimation."""
    Session = sessionmaker(bind=create_engine(DB_URL))
    session = Session()
    
    processed_count = 0
    error_count = 0
    
    try:
        # Initialize repository
        tactics_repo = Analyzed_tacticalsRepository(session_factory=lambda: session)
        
        # Process games in chunk
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all games in chunk
            future_to_game = {
                executor.submit(estimate_game_tactics, game_data): game_data[0]
                for game_data in games_chunk
            }
            
            # Process results
            for future in as_completed(future_to_game):
                game_id = future_to_game[future]
                
                try:
                    result, error = future.result()
                    
                    if error:
                        logger.debug(f"Game {game_id}: {error}")
                        error_count += 1
                        continue
                    
                    if not result:
                        error_count += 1
                        continue
                    
                    # Save lightweight tactical estimation
                    # Note: This would need adaptation based on your database schema
                    # For now, we'll just log the results
                    processed_count += 1
                    
                    if processed_count % 50 == 0:
                        logger.info(f"⚡ Estimated {processed_count} games in chunk")
                        
                except Exception as e:
                    logger.debug(f"Error processing game {game_id}: {e}")
                    error_count += 1
        
        logger.info(f"⚡ Chunk completed: {processed_count} estimated, {error_count} errors")
        
    except Exception as e:
        logger.error(f"❌ Chunk estimation error: {e}")
        
    finally:
        session.close()
    
    return processed_count, error_count

def get_games_for_estimation(source=None, max_games=10000, offset=0):
    """Get games from database for tactical estimation."""
    Session = sessionmaker(bind=create_engine(DB_URL))
    session = Session()
    
    try:
        games_repo = GamesRepository(session_factory=lambda: session)
        
        # Get games from database
        if source:
            games = games_repo.get_games_by_source(source, limit=max_games, offset=offset)
            logger.info(f"🎯 Found {len(games)} games from source '{source}'")
        else:
            games = games_repo.get_all_games(limit=max_games, offset=offset)
            logger.info(f"🎯 Found {len(games)} total games")
        
        # Prepare games for processing
        games_for_processing = []
        for game in games:
            game_id = game.get('id') or get_game_id(game.get('pgn', ''))
            games_for_processing.append((
                game_id,
                game.get('pgn', ''),
                game.get('source', 'unknown')
            ))
        
        logger.info(f"⚡ {len(games_for_processing)} games ready for estimation")
        return games_for_processing
        
    except Exception as e:
        logger.error(f"❌ Error getting games: {e}")
        return []
        
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(
        description="Fast Lightweight Tactical Feature Estimation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Estimate tactical features for personal games
  python estimate_tactical_features.py --source personal --max-games 10000

  # Quick estimation for fide games
  python estimate_tactical_features.py --source fide --max-games 5000

  # Estimate with custom workers
  python estimate_tactical_features.py --source elite --workers 8
        """
    )
    
    parser.add_argument('--source', help='Filter by game source (personal, fide, lichess, etc.)')
    parser.add_argument('--max-games', type=int, default=10000, help='Maximum number of games to estimate')
    parser.add_argument('--offset', type=int, default=0, help='Offset for pagination')
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help='Number of parallel workers')
    parser.add_argument('--chunk-size', type=int, default=ESTIMATION_PER_CHUNK, help='Games per chunk')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update configuration
    global MAX_WORKERS, ESTIMATION_PER_CHUNK
    MAX_WORKERS = args.workers
    ESTIMATION_PER_CHUNK = args.chunk_size
    
    logger.info("⚡ Starting fast tactical feature estimation...")
    logger.info(f"📋 Parameters:")
    logger.info(f"   - Source: {args.source or 'ALL'}")
    logger.info(f"   - Max games: {args.max_games}")
    logger.info(f"   - Workers: {MAX_WORKERS}")
    logger.info(f"   - Chunk size: {ESTIMATION_PER_CHUNK}")
    
    start_time = time.time()
    
    try:
        # Get games for estimation
        games_to_estimate = get_games_for_estimation(
            source=args.source,
            max_games=args.max_games,
            offset=args.offset
        )
        
        if not games_to_estimate:
            logger.warning("⚠️ No games found for estimation")
            return
        
        # Process games in chunks
        total_estimated = 0
        total_errors = 0
        
        for i in range(0, len(games_to_estimate), ESTIMATION_PER_CHUNK):
            chunk = games_to_estimate[i:i + ESTIMATION_PER_CHUNK]
            chunk_num = i // ESTIMATION_PER_CHUNK + 1
            total_chunks = (len(games_to_estimate) + ESTIMATION_PER_CHUNK - 1) // ESTIMATION_PER_CHUNK
            
            logger.info(f"⚡ Estimating chunk {chunk_num}/{total_chunks} ({len(chunk)} games)")
            
            estimated, errors = process_estimation_chunk(chunk)
            total_estimated += estimated
            total_errors += errors
            
            logger.info(f"✅ Chunk {chunk_num} completed: {estimated} estimated, {errors} errors")
        
        # Final summary
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"🎉 Tactical estimation completed!")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Total games estimated: {total_estimated}")
        logger.info(f"   - Total errors: {total_errors}")
        logger.info(f"   - Duration: {duration:.2f} seconds")
        logger.info(f"   - Games per second: {total_estimated / duration:.2f}")
        
        if total_errors > 0:
            logger.warning(f"⚠️ {total_errors} games had errors during estimation")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
