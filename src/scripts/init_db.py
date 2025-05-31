import sqlite3
import os
from dotenv import load_dotenv

def create_tables(conn):
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS games (
        game_id TEXT PRIMARY KEY,
        white_player TEXT,
        black_player TEXT,
        white_elo INTEGER,
        black_elo INTEGER,
        result TEXT,
        event TEXT,
        site TEXT,
        date TEXT,
        eco TEXT,
        opening TEXT,
        pgn TEXT,
        tags TEXT    
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS features (
        game_id TEXT,
        move_number INTEGER,
        fen TEXT,
        move_san TEXT,
        move_uci TEXT,
        material_balance REAL,
        material_total REAL,
        num_pieces INTEGER,
        branching_factor INTEGER,
        self_mobility INTEGER,
        opponent_mobility INTEGER,
        phase TEXT,
        player_color TEXT,
        has_castling_rights INTEGER,
        move_number_global INTEGER,
        is_repetition INTEGER,
        is_low_mobility INTEGER,
        tags TEXT,
        score_diff REAL,
        PRIMARY KEY (game_id, move_number)
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analyzed_errors (
        game_id TEXT PRIMARY KEY,
        date_analyzed TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS processed_games (
        game_id TEXT PRIMARY KEY
    );
    """)
    conn.commit()

def main():
    load_dotenv()
    db_path = os.environ.get("CHESS_TRAINER_DB")
    conn = sqlite3.connect(db_path)
    create_tables(conn)
    conn.close()
    print(f"✅ Base de datos creada correctamente en {db_path}")

if __name__ == "__main__":
    main()
