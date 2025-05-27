import os
import chess.pgn
import sqlite3
import argparse

from dotenv import load_dotenv
load_dotenv()  # Carga las variables del archivo .env

DB_PATH = os.environ.get("CHESS_TRAINER_DB")

if not DB_PATH or not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"❌ Database not found or CHESS_TRAINER_DB unset: {DB_PATH}")

def parse_and_save_pgn(pgn_path, db_path=DB_PATH, max_games=None):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    with open(pgn_path, encoding="utf-8") as pgn_file:
        count = 0
        while True:
            game = chess.pgn.read_game(pgn_file)
            if game is None or (max_games and count >= max_games):
                break

            headers = game.headers
            pgn_string = str(game)

            cursor.execute("""
                INSERT INTO games (
                    white_player, black_player, white_elo, black_elo, result,
                    event, site, date, eco, opening, pgn
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                headers.get("White", ""),
                headers.get("Black", ""),
                int(headers.get("WhiteElo", 0)) if headers.get("WhiteElo", "").isdigit() else None,
                int(headers.get("BlackElo", 0)) if headers.get("BlackElo", "").isdigit() else None,
                headers.get("Result", ""),
                headers.get("Event", ""),
                headers.get("Site", ""),
                headers.get("Date", ""),
                headers.get("ECO", ""),
                headers.get("Opening", ""),
                pgn_string
            ))

            count += 1
            print(f"Importing game #{count}: {headers.get('White', 'Unknown')} vs {headers.get('Black', 'Unknown')}")

    conn.commit()
    conn.close()
    print(f"✅ {count} game(s) imported successfully.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import PGN games into chess_trainer.db")
    parser.add_argument("--input", "-i", required=True, help="Path to the PGN file")
    parser.add_argument("--max", "-m", type=int, help="Maximum number of games to import")
    args = parser.parse_args()

    parse_and_save_pgn(args.input, max_games=args.max)
