#!/usr/bin/env python3
"""
Check database schema for SPRINT 1 testing
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from db.postgres_utils import PostgreSQLConnection

def check_games_schema():
    """Check games table structure"""
    pg = PostgreSQLConnection()
    
    print("📋 Checking games table structure...")
    columns_query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns 
    WHERE table_name = 'games' 
    ORDER BY ordinal_position;
    """
    
    columns = pg.execute_query(columns_query)
    print("\n🔍 Games table columns:")
    for col in columns:
        print(f"   - {col['column_name']}: {col['data_type']} ({'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'})")
    
    # Sample a few games
    print("\n📊 Sample games data:")
    sample_query = """
    SELECT white_player, black_player, result, date_played
    FROM games 
    ORDER BY date_played DESC
    LIMIT 3;
    """
    
    games = pg.execute_query(sample_query)
    for i, game in enumerate(games, 1):
        print(f"   {i}. {game['white_player']} vs {game['black_player']} ({game['result']}) - {game['date_played']}")

if __name__ == "__main__":
    check_games_schema()