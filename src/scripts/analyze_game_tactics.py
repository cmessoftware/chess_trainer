import os
import sqlite3
import traceback
from typing import Dict, List
from modules.db_utils import (
    load_analyzed_tacticals_hashes,
    save_analyzed_tacticals_hash,
    init_analyzed_errors_table
)
from modules.pgn_utils import load_all_games_from_db, get_game_hash
from modules.tactical_analysis import detect_tactics_from_game
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.environ.get("CHESS_TRAINER_DB")



def insert_tactical_tags_to_db(game_id: str, tags: List[Dict]):
    try:
        if not tags:
            return
        
        print(f"📝 Insertando {len(tags)} etiquetas tácticas para la partida {game_id}...:")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for tag in tags:
                cursor.execute("""
                    UPDATE features
                    SET tags = ?, score_diff = ?
                    WHERE game_id = ? AND move_number = ?
                """, (
                    tag.get("tag"),
                    tag.get("score_diff"),
                    game_id,
                    tag.get("move_number")
                ))
            
            if cursor.rowcount == 0:
                print(f"⚠️ No se actualizó ninguna fila para game_id={game_id}, move={tag.get('move_number')}")
            else:
                print(f"✅ Se actualizó {cursor.rowcount} fila(s) para game_id={game_id}, move={tag.get('move_number')}")    
            
            conn.commit()
    except sqlite3.Error as e:
        print(f"Error al insertar etiquetas tácticas en la base de datos: {e}")
        raise


def analyze_game_tactics():
    init_analyzed_errors_table()
    analyzed = load_analyzed_tacticals_hashes()
    print(f"🔍 Cargando partidas ya analizadas... {len(analyzed)} partidas encontradas.")
    
    games = load_all_games_from_db()
    if not games:
        print("❌ No se encontraron partidas en la base de datos.")
        return
    
    for game in games:
        game_hash = get_game_hash(game)
        if game_hash in analyzed:
            print(f"✅ Partida {game_hash} : {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')} ya analizada, saltando...")
            continue

        print(f"🔍 Analizando táctica: {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}")

        try:
            tags_df = detect_tactics_from_game(game)
            insert_tactical_tags_to_db(game_hash, tags_df)
                
        except Exception as e:
            print(f"❌ Excepcion al analizar partida {game_hash} - {game.headers.get('White', '?')} vs {game.headers.get('Black', '?')}: {e} - {traceback.print_exc()}")
            if e.__cause__:
                print("🔗 Causa original (inner exception):", e.__cause__)
            continue  # ⚠️ No marcar como procesada si hay error

        save_analyzed_tacticals_hash(game_hash)

if __name__ == "__main__":
    analyze_game_tactics()
