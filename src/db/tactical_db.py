# src/modules/tactical_db.py
import sqlite3
import json
import os
from typing import Dict, List
import dotenv

from db.db_utils import is_feature_in_db
dotenv.load_dotenv()

DB_PATH = os.environ.get("CHESS_TRAINER_DB")

#TODO: La insersión de tags y score_diff falla.
def update_features_tags_and_score_diff(game_id: str, tags: List[Dict]):
    try:
        if not tags:
            return
        
        print(f"📝 Actualizando {len(tags)} etiquetas tácticas para la partida {game_id}...:")
        
        updated_count = 0
        failed_updates = []

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for tag in tags:
                move_number = tag.get("move_number")
                player_color = tag.get("player_color")
                if player_color is None:
                    print(f"❌ Tag sin player_color: {tag}")
                    
                if is_feature_in_db(game_id):
                    print(f"✅ Insertando etiqueta: {tag.get('tag')} para la jugada {move_number} del jugador {player_color}")
                
                    sql = f"""
                        UPDATE features
                        SET tags = '{tag.get("tag")}' , score_diff = {tag.get("score_diff")}
                        WHERE game_id = '{game_id}' AND move_number = {move_number} AND player_color = {player_color}
                    """
                    print(f"sql = {sql}")
                    cursor.execute(sql)
                
                    # cursor.execute("""
                    #     INSERT OR IGNORE INTO features (game_id, move_number, player_color, tags, score_diff)
                    #     VALUES (?, ?, ?, ?, ?)
                    # """, (
                    #     game_id,
                    #     move_number,
                    #     player_color,
                    #     tag.get("tag"),
                    #     tag.get("score_diff")
                    # ))
                else:
                    print(f"❌ La partida {game_id} no existe en la base de datos. No se pueden insertar etiquetas.")
                    return
                
            if cursor.rowcount == 0:
                    failed_updates.append((move_number, player_color))
            else:
                    updated_count += 1
            
            if failed_updates:
                print(f"⚠️ No se actualizaron las jugadas: {failed_updates}")
                
                
            if updated_count == 0:
                print(f"⚠️ No se encontraron jugadas para actualizar en la partida {game_id}.")
                return
                        
            print(f"✅ {updated_count} etiquetas insertadas exitosamente para {game_id}") 
            
            conn.commit()
    except sqlite3.Error as e:
        print(f"❌ Expcepción al insertar etiquetas tácticas en la base de datos: {e}")
        raise


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
