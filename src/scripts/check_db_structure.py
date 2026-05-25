"""
Script to check database structure for survivorship bias module.
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ.get(
    "CHESS_TRAINER_DB_URL",
    "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db",
)


def check_database_structure():
    engine = create_engine(DB_URL)

    with engine.connect() as conn:
        # Check games table structure
        print("=== GAMES TABLE STRUCTURE ===")
        result = conn.execute(
            text(
                """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'games' 
            ORDER BY ordinal_position
        """
            )
        )
        games_columns = result.fetchall()
        for col_name, data_type in games_columns:
            print(f"  {col_name}: {data_type}")

        # Check features table structure
        print("\n=== FEATURES TABLE STRUCTURE ===")
        result = conn.execute(
            text(
                """
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'features' 
            ORDER BY ordinal_position
        """
            )
        )
        features_columns = result.fetchall()
        for col_name, data_type in features_columns:
            print(f"  {col_name}: {data_type}")

        # Get sample data to understand structure
        print("\n=== SAMPLE GAMES DATA ===")
        result = conn.execute(text("SELECT * FROM games LIMIT 3"))
        rows = result.fetchall()
        if rows:
            # Print column names
            print("Columns:", result.keys())
            for i, row in enumerate(rows[:2]):
                print(f"Row {i+1}: {dict(zip(result.keys(), row))}")
        else:
            print("No data in games table")

        # Check if we have data with specific sources
        print("\n=== DATA BY SOURCE ===")
        result = conn.execute(
            text("SELECT source, COUNT(*) as count FROM games GROUP BY source")
        )
        sources = result.fetchall()
        for source, count in sources:
            print(f"  {source}: {count} games")


if __name__ == "__main__":
    check_database_structure()
