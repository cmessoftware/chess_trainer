"""
Single-threaded tactical analysis test script
"""
import os
import sys
import logging
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set up simple logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

from database.database_manager import DatabaseManager
from modules.analyze_games_tactics import detect_tactics_from_game
from repositories.features_repository import FeaturesRepository

def test_single_game():
    """Test tactical analysis on a single game"""
    
    # Set Stockfish path
    stockfish_path = os.path.join(project_root.parent, "bin", "stockfish.exe")
    os.environ['STOCKFISH_PATH'] = stockfish_path
    
    print(f"Using Stockfish: {stockfish_path}")
    print(f"Stockfish exists: {os.path.exists(stockfish_path)}")
    
    # Initialize database
    db_manager = DatabaseManager(db_name="chess_trainer")
    features_repo = FeaturesRepository(db_manager)
    
    # Get a game from database
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, pgn_text 
            FROM games 
            WHERE id = 200  -- Fixed game ID
            LIMIT 1
        """)
        game_data = cursor.fetchone()
    
    if not game_data:
        print("No game found with ID 200")
        return
    
    game_id, pgn_text = game_data
    print(f"Testing game ID: {game_id}")
    
    # Parse game
    import chess.pgn
    import io
    
    pgn_io = io.StringIO(pgn_text)
    game = chess.pgn.read_game(pgn_io)
    
    if not game:
        print("Failed to parse game")
        return
    
    print("Starting tactical analysis...")
    
    # Run tactical analysis
    try:
        tactics = detect_tactics_from_game(game, game_id)
        print(f"Found {len(tactics)} tactical patterns")
        
        for i, tactic in enumerate(tactics[:5]):  # Show first 5
            print(f"Tactic {i+1}: {tactic}")
        
        # Update features with tactical data
        if tactics:
            features_repo.update_tactical_data(game_id, tactics)
            print(f"Updated features for game {game_id} with {len(tactics)} tactical patterns")
        
    except Exception as e:
        print(f"Error in tactical analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_game()
