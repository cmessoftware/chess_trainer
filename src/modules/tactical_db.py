# src/modules/tactical_db.py
import sqlite3
import json
import os
import dotenv
dotenv.load_dotenv()

DB_PATH = os.environ.get("CHESS_TRAINER_DB")

def init_tactical_exercises_table(db_path=DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS tactical_exercises (
            id TEXT PRIMARY KEY,
            fen TEXT NOT NULL,
            move TEXT NOT NULL,
            uci TEXT NOT NULL,
            tags TEXT NOT NULL,
            source_game_id TEXT
        )
        """)

def save_tactic_to_db(tactic, db_path=DB_PATH):
    print(f"📝 Guardando táctica: {tactic['id']}")
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
        INSERT OR REPLACE INTO tactical_exercises (id, fen, move, uci, tags, source_game_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (
            tactic["id"],
            tactic["fen"],
            tactic["move"],
            tactic["uci"],
            json.dumps(tactic["tags"]),
            tactic.get("source_game_id")
        ))
        
        

def bulk_import_tactics_from_json(folder_path="data/tactics", db_path=DB_PATH):
    files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    for filename in files:
        filepath = os.path.join(folder_path, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for i, tactic in enumerate(data):
                    if "id" not in tactic:
                        tactic["id"] = f"{filename[:-5]}_{i}"
                    save_tactic_to_db(tactic, db_path)
            elif isinstance(data, dict):
                if "id" not in data:
                    data["id"] = filename[:-5]
                save_tactic_to_db(data, db_path)
