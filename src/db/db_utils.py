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


def create_studies_table(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS studies (
                study_id TEXT PRIMARY KEY,
                title TEXT,
                description TEXT,
                tags TEXT,
                source TEXT,
                created_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                study_id TEXT,
                fen TEXT,
                comment TEXT,
                is_critical INTEGER DEFAULT 0,
                FOREIGN KEY(study_id) REFERENCES studies(study_id)
            )
        """)

def create_games_table(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
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

def create_features_table(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
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
            is_center_controlled INTEGER,
            is_pawn_endgame INTEGER,
            tags TEXT,
            score_diff REAL
        );
        """)

def create_analyzed_errors_table(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS analyzed_errors (
            game_id TEXT PRIMARY KEY,
            date_analyzed TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

def create_processed_games_table(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS processed_games (
            game_id TEXT PRIMARY KEY
        );
        """)

def create_analyzed_tacticals_table(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS analyzed_tacticals  (
            game_id TEXT PRIMARY KEY,
            date_analyzed TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)

def create_tactical_exercises_table(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS tactical_exercises  (
            id TEXT PRIMARY KEY,
            fen TEXT NOT NULL,
            move TEXT NOT NULL,
            uci TEXT NOT NULL,
            tags TEXT NOT NULL,
            source_game_id TEXT
        );
        """)

def create_study_positions_table(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS study_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                study_id TEXT,
                fen TEXT,
                comment TEXT,
                FOREIGN KEY(study_id) REFERENCES studies(study_id)
            )
        """)

def init_db(db_path: str = DB_PATH):
    try:
        create_games_table(db_path)
        create_features_table(db_path)
        create_analyzed_errors_table(db_path)
        create_processed_games_table(db_path)
        create_analyzed_tacticals_table(db_path)
        create_tactical_exercises_table(db_path)
        create_studies_table(db_path)
        create_study_positions_table(db_path)
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
        raise
 
            
        
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

def is_feature_in_db(game_id):
    try:
        """Verifica si las características de una partida ya están en la base de datos."""
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM features WHERE game_id = ?", (game_id,))
            return cursor.fetchone() is not None
    except sqlite3.Error as e:
        print(f"Error al verificar si las características están en la tabla feature de la base {DB_PATH}: {e}")
        return False
        
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
        
def init_analyzed_tacticals_table():
    """Crea tabla para partidas ya analizadas por errores."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS analyzed_tacticals (
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

def get_game_by_id(game_id, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM games WHERE game_id = ?", (game_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "game_id": row[0],
            "white_player": row[1],
            "black_player": row[2],
            "white_elo": row[3],
            "black_elo": row[4],
            "result": row[5],
            "event": row[6],
            "site": row[7],
            "date": row[8],
            "eco": row[9],
            "opening": row[10],
            "pgn": row[11],
            "tags": row[12]
        }
    return None

def get_computed_games_ids():
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT game_id FROM games").fetchall()
        return set(row[0] for row in rows)
  
def compute_game_id(game):
    return hashlib.md5(str(game).encode('utf-8')).hexdigest()

def load_analyzed_errors_hashes():
    """Devuelve los game_hash ya analizados en el módulo de errores."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT game_id FROM analyzed_errors").fetchall()
        return set(row[0] for row in rows)
    
def load_analyzed_tacticals_hashes():
    """Devuelve los game_hash ya analizados en el módulo de tactica."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute("SELECT game_id FROM analyzed_tacticals").fetchall()
        return set(row[0] for row in rows)
    
def save_analyzed_errors_hash(game_hash):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS analyzed_errors (game_id TEXT PRIMARY KEY, date_analyzed TEXT DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("INSERT OR IGNORE INTO analyzed_errors (game_id) VALUES (?)", (game_hash,))
        
def save_analyzed_tacticals_hash(game_hash):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS analyzed_tacticals (game_id TEXT PRIMARY KEY, date_analyzed TEXT DEFAULT CURRENT_TIMESTAMP)")
            conn.execute("INSERT OR IGNORE INTO analyzed_tacticals (game_id) VALUES (?)", (game_hash,))
    except sqlite3.Error as e:
        print(f"Error al guardar el hash de tácticas analizadas: {e}")
        raise


def load_analyzed_tacticals_hashes():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            result = conn.execute("SELECT game_id FROM analyzed_tacticals").fetchall()
            return set(row[0] for row in result)
    except sqlite3.Error as e:
        print(f"Error al cargar los hashes de tácticas analizadas: {e}")
        raise

def load_processed_exercises_hashes():
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute("SELECT game_hash FROM processed_games").fetchall()
        return set(row[0] for row in result)

def save_processed_exercises_hash(game_hash):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO processed_games (game_id) VALUES (?)", (game_hash,))
        
def get_game_id_by_game(game):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            game_hash = conn.execute("SELECT game_id FROM processed_games WHERE game_id = ?", (game.headers.get('GameHash', ''),)).fetchone()
            return game_hash[0] if game_hash else None
    except sqlite3.Error as e:
         print(f"Error al obtener el ID de la partida: {e}")
         raise
