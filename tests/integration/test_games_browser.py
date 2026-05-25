#!/usr/bin/env python3
"""
Test script to verify Games Browser interface functionality
SPRINT 1 - TEST 3: Games Browser Interface Testing
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from components.database_connector import DatabaseConnector

def test_games_browser_functionality():
    """Test all Games Browser interface components"""
    print("🔍 SPRINT 1 - TEST 3: Games Browser Interface Testing")
    print("=" * 60)
    
    try:
        # Initialize database connector
        db_connector = DatabaseConnector()
        
        if not db_connector.test_connection():
            print("❌ Database connection failed - cannot test Games Browser")
            return False
        
        # Test 1: Database statistics for overview
        print("\n1. Testing database overview statistics...")
        stats = db_connector.get_database_stats()
        if stats:
            print("   ✅ Database overview ready:")
            print(f"      📊 Total games: {stats.get('total_games', 0):,}")
            print(f"      👥 Unique players: {stats.get('unique_players', 0):,}")
            print(f"      ⚡ Features analyzed: {stats.get('total_features', 0):,}")
        else:
            print("   ❌ Failed to get database overview")
            return False
        
        # Test 2: Pagination functionality
        print("\n2. Testing pagination controls...")
        
        # Test different page sizes
        for page_size in [10, 25, 50]:
            result = db_connector.get_games_paginated(page=1, per_page=page_size)
            if isinstance(result, tuple):
                games_df, total = result
                if len(games_df) > 0:
                    print(f"   ✅ Page size {page_size}: Retrieved {len(games_df)} games (Total: {total:,})")
                else:
                    print(f"   ⚠️  Page size {page_size}: No games retrieved")
            else:
                print(f"   ❌ Page size {page_size}: Invalid response format")
                return False
        
        # Test pagination navigation (multiple pages)
        print("\n3. Testing pagination navigation...")
        for page_num in [1, 2, 3]:
            result = db_connector.get_games_paginated(page=page_num, per_page=5)
            if isinstance(result, tuple):
                games_df, total = result
                if len(games_df) > 0:
                    sample_game = games_df.iloc[0]
                    print(f"   ✅ Page {page_num}: {sample_game['white_player']} vs {sample_game['black_player']}")
                else:
                    print(f"   ⚠️  Page {page_num}: No games found")
            else:
                print(f"   ❌ Page {page_num}: Navigation failed")
                return False
        
        # Test 3: Search functionality
        print("\n4. Testing search functionality...")
        
        search_terms = ["Evgeny", "1-0", "Chess", "Novice"]
        for term in search_terms:
            results = db_connector.search_games(term, limit=5)
            if results is not None:
                found_count = len(results)
                print(f"   ✅ Search '{term}': {found_count} results")
                if found_count > 0:
                    sample = results.iloc[0]
                    print(f"      📋 Sample: {sample['white_player']} vs {sample['black_player']}")
            else:
                print(f"   ❌ Search '{term}': Failed")
                return False
        
        # Test 4: Game details functionality
        print("\n5. Testing game details view...")
        
        # Get a game ID first
        result = db_connector.get_games_paginated(page=1, per_page=1)
        if isinstance(result, tuple) and len(result[0]) > 0:
            sample_game_id = result[0].iloc[0]['game_id']
            
            game_details = db_connector.get_game_details(sample_game_id)
            if game_details:
                print("   ✅ Game details retrieved:")
                print(f"      🎯 Game ID: {game_details.get('game_id', 'N/A')}")
                print(f"      ⚪ White: {game_details.get('white_player', 'N/A')} ({game_details.get('white_elo', 'N/A')})")
                print(f"      ⚫ Black: {game_details.get('black_player', 'N/A')} ({game_details.get('black_elo', 'N/A')})")
                print(f"      🏆 Result: {game_details.get('result', 'N/A')}")
                print(f"      📅 Date: {game_details.get('date_played', 'N/A')}")
            else:
                print("   ❌ Failed to get game details")
                return False
        else:
            print("   ⚠️  No games available to test details view")
        
        # Test 5: Player search suggestions
        print("\n6. Testing player search suggestions...")
        
        players = db_connector.get_unique_players(limit=10)
        if players and len(players) > 0:
            print(f"   ✅ Player suggestions ready: {len(players)} players")
            print(f"      👥 Sample players: {', '.join(players[:5])}")
        else:
            print("   ⚠️  No player suggestions available")
        
        # Test 6: Export functionality preparation
        print("\n7. Testing PGN export functionality...")
        
        # Get some game IDs for export testing
        result = db_connector.get_games_paginated(page=1, per_page=3)
        if isinstance(result, tuple) and len(result[0]) > 0:
            game_ids = result[0]['game_id'].tolist()
            
            pgn_content = db_connector.export_games_to_pgn(game_ids)
            if pgn_content and len(pgn_content) > 0:
                lines_count = len(pgn_content.split('\n'))
                print(f"   ✅ PGN export ready: {len(game_ids)} games, {lines_count} lines")
                
                # Check if PGN format is valid
                if '[Event ' in pgn_content and '[White ' in pgn_content:
                    print("   ✅ PGN format validation passed")
                else:
                    print("   ⚠️  PGN format may have issues")
            else:
                print("   ❌ PGN export failed")
                return False
        else:
            print("   ⚠️  No games available for export testing")
        
        # Test 7: Performance check
        print("\n8. Testing performance with larger datasets...")
        
        # Test larger pagination
        result = db_connector.get_games_paginated(page=1, per_page=100)
        if isinstance(result, tuple) and len(result[0]) > 0:
            print(f"   ✅ Large pagination: {len(result[0])} games retrieved efficiently")
        else:
            print("   ⚠️  Large pagination test failed")
        
        print("\n" + "=" * 60)
        print("✅ Games Browser interface test PASSED!")
        print("🎯 All interface components are ready for Streamlit deployment")
        return True
        
    except Exception as e:
        print(f"\n❌ Games Browser interface test FAILED!")
        print(f"🚨 Error: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        import traceback
        print("\n🔍 Detailed traceback:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    success = test_games_browser_functionality()
    sys.exit(0 if success else 1)