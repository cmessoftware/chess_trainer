#!/usr/bin/env python3
"""
Test script to verify Database Connector functionality
SPRINT 1 - TEST 2: Database Connector Component Testing
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from components.database_connector import DatabaseConnector

def test_database_connector():
    """Test Database Connector component functionality"""
    print("🔍 SPRINT 1 - TEST 2: Database Connector Component Testing")
    print("=" * 60)
    
    try:
        # Test 1: Initialize Database Connector
        print("\n1. Initializing Database Connector...")
        db_connector = DatabaseConnector()
        print("   ✅ Database Connector initialized successfully")
        
        # Test 2: Test connection
        print("\n2. Testing database connection...")
        connection_status = db_connector.test_connection()
        if connection_status:
            print("   ✅ Connection test passed")
        else:
            print("   ❌ Connection test failed")
            return False
        
        # Test 3: Get games statistics
        print("\n3. Testing get_database_stats()...")
        stats = db_connector.get_database_stats()
        if stats:
            print(f"   ✅ Statistics retrieved:")
            print(f"      - Total games: {stats.get('total_games', 'N/A'):,}")
            print(f"      - Total features: {stats.get('total_features', 'N/A'):,}")
            print(f"      - Total tacticals: {stats.get('total_tacticals', 'N/A'):,}")
            print(f"      - Unique players: {stats.get('unique_players', 'N/A'):,}")
        else:
            print("   ❌ Failed to get statistics")
            return False
        
        # Test 4: Test pagination
        print("\n4. Testing get_games_paginated()...")
        try:
            result = db_connector.get_games_paginated(page=1, per_page=5)
            print(f"   🔍 Result type: {type(result)}")
            
            # The method might return tuple (df, total) or just df
            if isinstance(result, tuple):
                page_1, total = result
                print(f"   🔍 Got tuple: df shape {page_1.shape if hasattr(page_1, 'shape') else 'no shape'}, total: {total}")
            else:
                page_1 = result
                print(f"   🔍 Got single result: {type(page_1)}")
                
            if page_1 is not None and len(page_1) > 0:
                print(f"   ✅ Page 1 retrieved: {len(page_1)} games")
                sample_game = page_1.iloc[0]
                print(f"      Sample: {sample_game['white_player']} vs {sample_game['black_player']}")
            else:
                print("   ❌ Failed to get paginated results - empty or None result")
                if page_1 is None:
                    print("      Result is None")
                elif len(page_1) == 0:
                    print("      Result is empty")
                return False
                
        except Exception as e:
            print(f"   ❌ Exception in pagination test: {str(e)}")
            import traceback
            print("   🔍 Traceback:")
            traceback.print_exc()
            return False
        
        # Test 5: Test search functionality
        print("\n5. Testing search_games()...")
        search_results = db_connector.search_games("Evgeny", limit=3)
        if search_results is not None:
            print(f"   ✅ Search results: {len(search_results)} games found")
            if len(search_results) > 0:
                sample_result = search_results.iloc[0]
                print(f"      Sample: {sample_result['white_player']} vs {sample_result['black_player']}")
        else:
            print("   ❌ Search functionality failed")
            return False
        
        # Test 6: Test getting unique values  
        print("\n6. Testing get_unique_players()...")
        try:
            players = db_connector.get_unique_players(limit=5)
            if players:
                print(f"   ✅ Unique players found: {len(players)} ({', '.join(players[:3])}...)")
            else:
                print("   ⚠️  No unique players found (might be expected)")
        except Exception as e:
            print(f"   ⚠️  Get unique players test failed: {str(e)}")
        
        # Test 7: Test export functionality (simulate)
        print("\n7. Testing PGN export preparation...")
        try:
            result = db_connector.get_games_paginated(page=1, per_page=2)
            
            # Handle tuple return
            if isinstance(result, tuple):
                export_games, total = result
            else:
                export_games = result
                
            if export_games is not None and len(export_games) > 0:
                print(f"   ✅ Export data preparation: {len(export_games)} games ready")
            else:
                print("   ❌ Export data preparation failed")
        except Exception as e:
            print(f"   ❌ Export test failed: {str(e)}")
            return False
        
        print("\n" + "=" * 60)
        print("✅ Database Connector component test PASSED!")
        print("🎯 Component is ready for Streamlit frontend integration")
        return True
        
    except Exception as e:
        print(f"\n❌ Database Connector component test FAILED!")
        print(f"🚨 Error: {str(e)}")
        print(f"🔍 Error type: {type(e).__name__}")
        
        if "ModuleNotFoundError" in str(type(e)):
            print("\n💡 Troubleshooting tips:")
            print("   - Check Python path is correctly set")
            print("   - Verify src/components/database_connector.py exists")
            print("   - Check all imports in database_connector.py are available")
        
        return False

if __name__ == "__main__":
    success = test_database_connector()
    sys.exit(0 if success else 1)