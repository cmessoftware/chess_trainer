from db.postgres_utils import execute_postgres_query
import sys
import os
sys.path.insert(0, '/app/src')


def test_processed_hash_table():
    # Check if any of the core tables exist in PostgreSQL
    query = """
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'games'
    );
    """
    result = execute_postgres_query(query)
    assert result[0]['exists'] is True
