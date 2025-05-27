import os
import sqlite3
import json
import io
import sys

# Permitir importar modules.* desde un script en src/scripts
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.tagging import detect_tags_from_game
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.environ.get("CHESS_TRAINER_DB")
if not DB_PATH or not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"❌ Database not found or CHESS_TRAINER_DB unset: {DB_PATH}")

def apply_tags_to_all_games():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, pgn FROM games WHERE tags IS NULL")
    rows = cursor.fetchall()

    for gid, pgn in rows:
        try:
            tags = detect_tags_from_game(pgn)
            tag_str = json.dumps(tags)
            cursor.execute("UPDATE games SET tags = ? WHERE id = ?", (tag_str, gid))
        except Exception as e:
            print(f"⚠️ Error tagging game {gid}: {e}")
    conn.commit()
    conn.close()
    print(f"✅ Tagged {len(rows)} game(s).")

if __name__ == "__main__":
    apply_tags_to_all_games()
