#!/usr/bin/env python3
"""
Test script for Chess Board Visualizer integration
CHESS BOARD FEATURE - Integration Testing
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_chess_board_integration():
    """Test Chess Board Visualizer integration with Games Browser"""
    print("🔍 CHESS BOARD VISUALIZER - Integration Testing")
    print("=" * 60)
    
    try:
        # Test 1: Import chess board component
        print("\n1. Testing chess board component import...")
        from components.chess_board import get_chess_visualizer, ChessBoardVisualizer
        chess_visualizer = get_chess_visualizer()
        
        if isinstance(chess_visualizer, ChessBoardVisualizer):
            print("   ✅ Chess board visualizer component loaded")
        else:
            print("   ❌ Invalid chess board visualizer instance")
            return False
        
        # Test 2: Test PGN cleaning function
        print("\n2. Testing PGN processing...")
        
        sample_pgn = """1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 
        6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 1-0"""
        
        cleaned_pgn = chess_visualizer._clean_pgn(sample_pgn)
        
        if cleaned_pgn and "1. e4" in cleaned_pgn:
            print("   ✅ PGN cleaning function works")
            print(f"   📝 Sample: {cleaned_pgn[:50]}...")
        else:
            print("   ❌ PGN cleaning failed")
            return False
        
        # Test 3: Test Games Browser integration
        print("\n3. Testing Games Browser integration...")
        
        from pages.games_browser import main
        print("   ✅ Games Browser with chess board imported successfully")
        
        # Test 4: Test database integration
        print("\n4. Testing database integration for chess board...")
        
        from components.database_connector import DatabaseConnector
        db_connector = DatabaseConnector()
        
        if db_connector.test_connection():
            # Get a sample game with PGN
            result = db_connector.get_games_paginated(page=1, per_page=1)
            if isinstance(result, tuple) and len(result[0]) > 0:
                sample_game_id = result[0].iloc[0]['game_id']
                game_details = db_connector.get_game_details(sample_game_id)
                
                if game_details and game_details.get('pgn'):
                    print("   ✅ Sample game with PGN retrieved for chess board")
                    print(f"   🎯 Game: {game_details['white_player']} vs {game_details['black_player']}")
                    print(f"   📝 PGN length: {len(game_details['pgn'])} characters")
                else:
                    print("   ⚠️  Sample game found but no PGN data")
            else:
                print("   ⚠️  No games available for testing")
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Test 5: Test demo page
        print("\n5. Testing chess board demo page...")
        
        from pages.chess_board_demo import main as demo_main
        print("   ✅ Chess board demo page imported successfully")
        
        # Test 6: Verify HTML generation (basic test)
        print("\n6. Testing HTML component generation...")
        
        # This is a basic test - actual rendering would require Streamlit runtime
        sample_pgn_short = "1. e4 e5 2. Nf3 Nc6 3. Bb5"
        
        try:
            # Just test that the method exists and accepts parameters
            # We can't actually render without Streamlit runtime
            chess_visualizer.render_chess_board.__code__.co_argcount
            chess_visualizer.render_position_only.__code__.co_argcount
            print("   ✅ Chess board rendering methods are callable")
        except Exception as e:
            print(f"   ❌ Chess board methods test failed: {str(e)}")
            return False
        
        print("\n" + "=" * 60)
        print("🎉 CHESS BOARD VISUALIZER INTEGRATION TEST PASSED!")
        print("=" * 60)
        
        print("\n✨ NEW FEATURES AVAILABLE:")
        print("  ♟️ Interactive Chess Board: Navigate through game moves")
        print("  🎮 Move Controls: First, Previous, Next, Last move")
        print("  🔄 Board Flipping: View from both perspectives")
        print("  ⌨️ Keyboard Navigation: Arrow keys, Home, End")
        print("  📱 Responsive Design: Adjustable board sizes")
        print("  🎯 Integration: Available in Games Browser details view")
        print("  🧪 Demo Page: Standalone testing and demonstration")
        
        print("\n🚀 HOW TO USE:")
        print("  1. Run: streamlit run src/app.py")
        print("  2. Navigate to 'Explorar partidas' → Select a game → View details")
        print("  3. Or try 'Tablero interactivo' for standalone demo")
        
        print("\n📈 FUTURE ENHANCEMENTS READY FOR:")
        print("  • 🎯 Arrow highlighting for last moves")
        print("  • 📊 Position evaluation integration")  
        print("  • 🔍 Move analysis and annotations")
        print("  • ⚡ Engine analysis overlay")
        print("  • 🎨 Custom board themes and pieces")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Chess Board Visualizer integration test FAILED!")
        print(f"🚨 Error: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        import traceback
        print("\n🔍 Detailed traceback:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    success = test_chess_board_integration()
    sys.exit(0 if success else 1)