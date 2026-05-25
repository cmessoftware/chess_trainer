#!/usr/bin/env python3
"""
Test script to verify PostgreSQL connection
SPRINT 1 - TEST 1: PostgreSQL Connection Verification
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
from db.postgres_utils import PostgreSQLConnection

# Load environment variables
load_dotenv()

def test_postgresql_connection():
    """Test PostgreSQL connection and basic functionality"""
    print("🔍 SPRINT 1 - TEST 1: PostgreSQL Connection Verification")
    print("=" * 60)
    
    try:
        # Test 1: Environment variable check
        print("\n1. Checking environment variables...")
        db_url = os.environ.get("CHESS_TRAINER_DB_URL")
        if db_url:
            print(f"   ✅ CHESS_TRAINER_DB_URL found")
            # Don't print the full URL for security
            parsed_url = db_url.split('@')[-1] if '@' in db_url else 'localhost:5432'
            print(f"   📍 Connection target: {parsed_url}")
        else:
            print("   ❌ CHESS_TRAINER_DB_URL not found")
            return False
        
        # Test 2: PostgreSQL connection
        print("\n2. Testing PostgreSQL connection...")
        pg_conn = PostgreSQLConnection()
        
        # Test basic connection
        with pg_conn.get_connection() as conn:
            print("   ✅ Connection established successfully")
            
            # Test 3: Database version
            print("\n3. Checking PostgreSQL version...")
            version_result = pg_conn.execute_query("SELECT version();")
            if version_result:
                version = version_result[0]['version']
                print(f"   ✅ PostgreSQL Version: {version.split(',')[0]}")
            
            # Test 4: Check tables exist
            print("\n4. Checking required tables...")
            tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('games', 'features', 'analyzed_tacticals')
            ORDER BY table_name;
            """
            tables = pg_conn.execute_query(tables_query)
            
            expected_tables = {'games', 'features', 'analyzed_tacticals'}
            found_tables = {table['table_name'] for table in tables}
            
            for table in expected_tables:
                if table in found_tables:
                    print(f"   ✅ Table '{table}' exists")
                else:
                    print(f"   ⚠️  Table '{table}' missing")
            
            # Test 5: Check games count
            print("\n5. Checking games data...")
            games_count = pg_conn.execute_query("SELECT COUNT(*) as count FROM games;")
            if games_count:
                count = games_count[0]['count']
                print(f"   ✅ Games in database: {count:,}")
                
                if count > 0:
                    # Sample game data
                    sample_game = pg_conn.execute_query("""
                    SELECT game_id, white_player, black_player, result, date_played
                    FROM games 
                    ORDER BY game_id 
                    LIMIT 1;
                    """)
                    
                    if sample_game:
                        game = sample_game[0]
                        print(f"   📋 Sample game: {game['white_player']} vs {game['black_player']} ({game['result']})")
            
        print("\n" + "=" * 60)
        print("✅ PostgreSQL connection test PASSED!")
        print("🎯 Database is ready for SPRINT 1 frontend components")
        return True
        
    except Exception as e:
        print(f"\n❌ PostgreSQL connection test FAILED!")
        print(f"🚨 Error: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print("   - Check if PostgreSQL container is running: docker-compose ps")
        print("   - Verify .env file has correct CHESS_TRAINER_DB_URL")
        print("   - Try restarting services: docker-compose down && docker-compose up -d")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    sys.exit(0 if success else 1)