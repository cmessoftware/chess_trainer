# tests/test_pipeline.py
import sqlite3
import os
import json
from pathlib import Path

DB_PATH = os.environ.get("CHESS_TRAINER_DB")
TACTICS_PATH = Path("data/tactics/elite")

def test_db_exists():
    assert os.path.exists(DB_PATH), "DB file not found"

def test_games_table_structure():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(games)")
    columns = {col[1] for col in cursor.fetchall()}
    conn.close()
    assert {"id", "pgn", "tags"}.issubset(columns)

def test_tags_populated():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM games WHERE tags IS NOT NULL")
    count = cursor.fetchone()[0]
    conn.close()
    assert count > 0, "No games have tags"

def test_exercise_files_exist_and_valid():
    files = list(TACTICS_PATH.glob("*.json"))
    assert len(files) > 0, "No tactics files found"
    for f in files:
        with open(f) as jf:
            data = json.load(jf)
            assert "fen" in data and "uci" in data and "id" in data
