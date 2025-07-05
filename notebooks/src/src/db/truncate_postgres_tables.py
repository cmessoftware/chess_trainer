# /app/src/scripts/truncate_postgres_tables.py

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# example: postgresql://user:password@host:port/dbname
DB_URL = os.getenv("CHESS_TRAINER_DB_URL")


def truncate_all_tables():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    cursor = conn.cursor()

    # Get all tables from the 'public' schema
    cursor.execute("""
        SELECT tablename FROM pg_tables
        WHERE schemaname = 'public';
    """)
    tables = cursor.fetchall()

    for (table,) in tables:
        print(f"🧹 Truncating table: {table}")
        cursor.execute(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE;')

    cursor.close()
    conn.close()
    print("✅ All tables have been truncated.")


if __name__ == "__main__":
    truncate_all_tables()
