# chess_trainer/scripts/generate_exercises_from_elite.py

import os
import sqlite3
import chess.pgn
from modules.exercise_utils import generate_exercise_from_game
from modules.pgn_utils import hash_game
from db.db_utils import init_db, load_processed_exercises_hashes, save_processed_exercises_hash
from modules.config_utils import get_valid_paths_from_env

DB_PATH = get_valid_paths_from_env(["CHESS_TRAINER_DB"])[0] 
PGN_DIR = "data/elite_games/"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_games (
                game_hash TEXT PRIMARY KEY,
                date_processed TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def main():
    init_db()
    processed = load_processed_exercises_hashes()
    for fname in os.listdir(PGN_DIR):
        if not fname.endswith(".pgn"):
            continue
        with open(os.path.join(PGN_DIR, fname)) as f:
            game = chess.pgn.read_game(f)
            h = hash_game(game)
            if h in processed:
                continue
            generate_exercise_from_game(game)
            save_processed_exercises_hash(h)

if __name__ == "__main__":
    main()
