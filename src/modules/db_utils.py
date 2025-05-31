# modules/db_utils.py

import hashlib
import sqlite3
from typing import Dict, List
import dotenv
import os
env = dotenv.load_dotenv()


DB_PATH = os.environ.get("CHESS_TRAINER_DB")

FEATURE_EXPECTED_COLUMNS = {
    "game_id": "TEXT",
    "move_number": "INTEGER",
    "fen": "TEXT",
    "move_san": "TEXT",
    "move_uci": "TEXT",
    "material_balance": "REAL",
    "material_total": "REAL",
    "num_pieces": "INTEGER",
    "branching_factor": "INTEGER",
    "self_mobility": "INTEGER",
    "opponent_mobility": "INTEGER",
    "phase": "TEXT",
    "player_color": "TEXT",
    "has_castling_rights": "INTEGER",
    "move_number_global": "INTEGER",
    "is_repetition": "INTEGER",
    "is_low_mobility": "INTEGER"
}

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_games (
                game_hash TEXT PRIMARY KEY,
                date_processed TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
 
            
        
def ensure_features_schema():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Obtener columnas actuales
        cursor.execute("PRAGMA table_info(features)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        # Verificar columnas faltantes
        for col, col_type in FEATURE_EXPECTED_COLUMNS.items():
            if col not in existing_cols:
                alter_stmt = f"ALTER TABLE features ADD COLUMN {col} {col_type};"
                print(f"🛠️ Agregando columna faltante: {col} ({col_type})")
                cursor.execute(alter_stmt)

        print("✅ Esquema de 'features' validado o actualizado.")

        
def init_analyzed_errors_table():
    """Crea tabla para partidas ya analizadas por errores."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyzed_errors (
                game_id TEXT PRIMARY KEY,
                date_analyzed TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
def was_game_already_processed(game_hash):
    conn = sqlite3.connect(DB_PATH)
    result = conn.execute("SELECT 1 FROM processed_games WHERE game_id = ?", (game_hash,)).fetchone()
    conn.close()
    return result is not None

def mark_game_as_processed(game_hash):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO processed_games (game_id) VALUES (?)", (game_hash,))
    conn.commit()
    conn.close()

def is_game_in_db(game_id, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM games WHERE game_id = ?", (game_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def compute_game_id(game):
    return hashlib.md5(str(game).encode('utf-8')).hexdigest()

def load_analyzed_errors_hashes():
    """Devuelve los game_hash ya analizados en el módulo de errores."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT game_id FROM analyzed_errors").fetchall()
        return set(row[0] for row in rows)
    
def load_analyzed_tacticals_hashes():
    """Devuelve los game_hash ya analizados en el módulo de errores."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT game_id FROM analyzed_tacticals").fetchall()
        return set(row[0] for row in rows)
    
def save_analyzed_errors_hash(game_hash):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS analyzed_errors (game_id TEXT PRIMARY KEY, date_analyzed TEXT DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT OR IGNORE INTO analyzed_errors (game_id) VALUES (?)", (game_hash,))
        
def save_analyzed_tacticals_hash(game_hash):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS analyzed_tacticals (game_id TEXT PRIMARY KEY, date_analyzed TEXT DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT OR IGNORE INTO analyzed_tacticals (game_id) VALUES (?)", (game_hash,))


def load_processed_hashes():
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute("SELECT game_hash FROM processed_games").fetchall()
        return set(row[0] for row in result)

def save_processed_hash(game_hash):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO processed_games (game_hash) VALUES (?)", (game_hash,))
        
def get_game_hash(game):
   with sqlite3.connect(DB_PATH) as conn:
       game_hash = conn.execute("SELECT game_hash FROM processed_games WHERE game_hash = ?", (game.headers.get('GameHash', ''),)).fetchone()
       return game_hash[0] if game_hash else None
