import os
import sys
import traceback
import chess.pgn
import sqlite3
import argparse

from dotenv import load_dotenv

from modules.db_utils import compute_game_id
from modules.utils import show_spinner_message
load_dotenv()  # Carga las variables del archivo .env

DB_PATH = os.environ.get("CHESS_TRAINER_DB")

if not DB_PATH or not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"❌ Database not found or CHESS_TRAINER_DB unset: {DB_PATH}")


def parse_and_save_pgn(pgn_path, db_path=DB_PATH, max_games=None):
    
    try:
        
        if not os.path.exists(pgn_path):
            print(f"❌ La ruta no existe: {pgn_path}")
            return
        if not os.path.isdir(pgn_path):
            print(f"❌ Se esperaba un directorio, no un archivo: {pgn_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        count = 0
    
        for filename in os.listdir(pgn_path):
            if not filename.endswith(".pgn"):
                continue  # ignorar archivos no PGN

            file_path = os.path.join(pgn_path, filename)
            print(f"📂 Procesando archivo: {file_path}")

            with open(file_path, encoding="utf-8") as pgn_file:
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    headers = game.headers
                    pgn_string = str(game)
                    game_id = compute_game_id(game)
                    
                    # Verificar si el juego ya existe en la base de datos
                    cursor.execute("SELECT 1 FROM games WHERE game_id = ?", (game_id,))
                    if cursor.fetchone() is not None:
                        show_spinner_message(f"⏭️ Processing...")
                        continue
                    # Insertar el juego en la base de datos

                    cursor.execute("""
                        INSERT INTO games (
                            game_id,      
                            white_player, 
                            black_player, 
                            white_elo, 
                            black_elo, 
                            result,
                            event,
                            site,
                            date,
                            eco,
                            opening,
                            pgn
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        game_id,
                        headers.get("White",      ""),
                        headers.get("Black",      ""),
                        int(headers.get("WhiteElo", 0)) if headers.get("WhiteElo", "").isdigit() else None,
                        int(headers.get("WhiteElo", "0")) if headers.get("WhiteElo", "").isdigit() else None,
                        headers.get("Result",     "0-0"),
                        headers.get("Event",      ""),
                        headers.get("Site",       ""),
                        headers.get("Date",       ""),
                        headers.get("ECO",        ""),
                        headers.get("Opening",    ""),
                        pgn_string
                    ))

                    count += 1
                    print(f"Importing game #{count}: {headers.get('White', 'Unknown')} vs {headers.get('Black', 'Unknown')}")

                    if max_games and count >= max_games:
                        print(f"⏹ Límite de partidas alcanzado: {max_games}")
                        sys.exit(0)
        conn.commit()
        conn.close()
        print(f"✅ {count} game(s) imported successfully.")
    except Exception as e:
        print(f"❌ Error al procesar el archivo PGN: {e} - {traceback.format_exc()}")
        if e.__cause__:
            print("Original casue (inner exception):", e.__cause__)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import PGN games into chess_trainer.db")
    parser.add_argument("--input", "-i", required=True, help="Path to the PGN file")
    parser.add_argument("--max", "-m", type=int, help="Maximum number of games to import")
    args = parser.parse_args()

    parse_and_save_pgn(args.input, max_games=args.max)
