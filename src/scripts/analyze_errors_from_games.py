import os
import sqlite3
import traceback
from modules.db_utils import (
    load_analyzed_hashes,
    save_analyzed_hash,
    init_analyzed_errors_table,
    insert_tactical_tags_to_db,
)
from modules.pgn_utils import load_all_games_from_dir, get_game_hash
from modules.tactical_analysis import detect_tactics_from_game


def main():
    init_analyzed_errors_table()
    analyzed = load_analyzed_hashes()
    folder = "data/games/"

    for game in load_all_games_from_dir(folder):
        game_hash = get_game_hash(game)
        if game_hash in analyzed:
            continue

        print(f"🔍 Analizando táctica: {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}")

        try:
            tags_df = detect_tactics_from_game(game)
            if len(tags_df) != 0:
                insert_tactical_tags_to_db(tags_df)
                
        except Exception as e:
            print(f"❌ Excepcion al analizar partida {game_hash} - {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}: {e} - {traceback.print_exc()}")
            if e.__cause__:
                print("🔗 Causa original (inner exception):", e.__cause__)
            continue  # ⚠️ No marcar como procesada si hay error

        save_analyzed_hash(game_hash)

if __name__ == "__main__":
    main()
