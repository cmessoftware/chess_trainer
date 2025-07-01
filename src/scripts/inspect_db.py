import os
import json
from dotenv import load_dotenv
from db.postgres_utils import execute_postgres_query

load_dotenv()  # Carga las variables del archivo .env

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")

print(f"Conectando a la base de datos PostgreSQL: {DB_URL}")

if not DB_URL:
    raise ValueError("❌ CHESS_TRAINER_DB_URL environment variable not set")


def inspect_latest_games(limit=10):
    query = """
        SELECT id, white_player, black_player, result, opening, tags
        FROM games
        ORDER BY id DESC
        LIMIT %s
    """

    games = execute_postgres_query(query, (limit,))

    print(f"\n📋 Últimas {limit} partidas:")
    print("-" * 80)
    for game in games:
        game_id, white, black, result, opening, tags = game['id'], game[
            'white_player'], game['black_player'], game['result'], game['opening'], game['tags']
        tag_list = json.loads(tags) if tags else []
        print(f"#{game_id} {white} vs {black} ({result})")
        print(f"   Apertura: {opening or 'N/A'}")
        print(f"   Etiquetas: {', '.join(tag_list) if tag_list else '—'}\n")


if __name__ == "__main__":
    inspect_latest_games()
