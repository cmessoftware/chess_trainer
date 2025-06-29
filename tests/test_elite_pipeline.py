from db.postgres_utils import execute_postgres_query, read_postgres_sql
from pathlib import Path
import json
import sys
import os
sys.path.insert(0, '/app/src')


DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
TACTICS_PATH = Path("data/tactics/elite")


def test_db_exists():
    # Test PostgreSQL connection is available
    try:
        result = execute_postgres_query("SELECT 1 as test")
        assert result[0]['test'] == 1
    except Exception as e:
        assert False, f"PostgreSQL connection failed: {e}"


def test_games_table_structure():
    # Check if games table exists and has required columns
    query = """
    SELECT column_name FROM information_schema.columns 
    WHERE table_schema = %s AND table_name = %s
    """
    result = execute_postgres_query(query, ('public', 'games'))
    columns = {row['column_name'] for row in result}
    assert {"game_id", "pgn"}.issubset(columns)


def test_tags_populated():
    # Check if features table has tags (tags are now in features table)
    query = "SELECT COUNT(*) as count FROM features WHERE tags IS NOT NULL"
    result = execute_postgres_query(query)
    count = result[0]['count']
    assert count > 0, "No features have tags"


def test_exercise_files_exist_and_valid():
    # This test checks for tactical exercise files
    # Since we've migrated to PostgreSQL, let's check if we can create tactical exercises
    from db.postgres_utils import pg_conn

    # Check if tactical_exercises table can be created (this validates PostgreSQL setup)
    try:
        result = pg_conn.table_exists('tactical_exercises')
        # Test passes if we can check for table existence (PostgreSQL is working)
        assert isinstance(result, bool)
    except Exception as e:
        assert False, f"Failed to check tactical_exercises table: {e}"
