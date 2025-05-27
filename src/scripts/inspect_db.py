import os
import sqlite3
import json

from dotenv import load_dotenv
load_dotenv()  # Carga las variables del archivo .env

DB_PATH = os.environ.get("CHESS_TRAINER_DB")

print(f"Conectando a la base de datos en: {DB_PATH}")

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"❌ Database file not found at: {DB_PATH}")

def inspect_latest_games(limit=10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, white_player, black_player, result, opening, tags
        FROM games
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    games = cursor.fetchall()
    conn.close()

    print(f"\n📋 Últimas {limit} partidas:")
    print("-" * 80)
    for game in games:
        game_id, white, black, result, opening, tags = game
        tag_list = json.loads(tags) if tags else []
        print(f"#{game_id} {white} vs {black} ({result})")
        print(f"   Apertura: {opening or 'N/A'}")
        print(f"   Etiquetas: {', '.join(tag_list) if tag_list else '—'}\n")

if __name__ == "__main__":
    inspect_latest_games()
