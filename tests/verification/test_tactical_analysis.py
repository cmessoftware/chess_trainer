#!/usr/bin/env python3
"""
Test script for tactical analysis functionality
"""
import os
import sys

# Set up environment
os.environ["STOCKFISH_PATH"] = os.path.join("..", "bin", "stockfish.exe")

# Add src to path
sys.path.append(os.path.dirname(__file__))

try:
    from modules.analyze_games_tactics import detect_tactics_from_game
    print("Successfully imported tactical analysis module")
    
    # Test a simple position
    import chess
    import chess.pgn
    import io
    
    # Simple test game
    pgn_text = """[Event "Test Game"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O *"""
    
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    print("Successfully parsed test game")
    
    # Test with minimal depth to speed up
    print("Starting tactical analysis...")
    tactics = detect_tactics_from_game(game, game_id="test", depth=5)
    print("Tactical analysis completed successfully")
    print(f"Found {len(tactics) if tactics else 0} tactical patterns")
    
    if tactics:
        print("Sample tactical pattern:", tactics[0])
    else:
        print("No tactical patterns found (normal for simple opening moves)")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
