import sqlite3
import os

from dotenv import load_dotenv
load_dotenv()  # Carga las variables del archivo .env

import os
import sqlite3

DB_PATH = os.environ.get("CHESS_TRAINER_DB")

if os.path.exists(DB_PATH):
     raise FileExistsError(f"❌ Database already exists at: {DB_PATH}")
    

conn = sqlite3.connect(DB_PATH)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER,
    move_number INTEGER,
    san TEXT,
    fen TEXT,
    eval_cp INTEGER,
    FOREIGN KEY (game_id) REFERENCES games(id)
)
""")

conn.commit()
conn.close()
print(f"✅ Base de datos creada correctamente en {DB_PATH}")
