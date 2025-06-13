from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, Text, MetaData, Table, select
import os
import sys
import traceback
import chess.pgn
import sqlite3
import argparse
import tempfile
import zipfile
import tarfile
import gzip
import bz2
import shutil

from dotenv import load_dotenv

from db.db_utils import DBUtils
from games import Games
from modules.utils import show_spinner_message
from pgn_loader import extract_pgn_files
from pgn_utils import extract_features_from_game
load_dotenv()  # Carga las variables del archivo .env

DB_PATH = os.environ.get("CHESS_TRAINER_DB")
PATH_PGN = os.environ.get("PATH_PGN")
db_utils = DBUtils()

if not DB_PATH or not os.path.exists(DB_PATH):
    raise FileNotFoundError(
        f"❌ Database not found or CHESS_TRAINER_DB unset: {DB_PATH}")


def parse_and_save_pgn(pgn_path, db_url=os.environ.get("CHESS_TRAINER_DB_URL"), max_games=None):
    try:
        if not os.path.exists(pgn_path):
            print(f"❌ La ruta no existe: {pgn_path}")
            return

        # db_url example: postgresql+psycopg2://user:password@host:port/dbname
        if not db_url:
            print("❌ CHESS_TRAINER_DB_URL environment variable not set")
            return

        engine = create_engine(db_url)
        metadata = MetaData()

        games = Table(
            "games", metadata,
            Column("game_id", String, primary_key=True),
            Column("white_player", String),
            Column("black_player", String),
            Column("white_elo", Integer),
            Column("black_elo", Integer),
            Column("result", String),
            Column("event", String),
            Column("site", String),
            Column("date", String),
            Column("eco", String),
            Column("opening", String),
            Column("pgn", Text),
            extend_existing=True
        )

        Session = sessionmaker(bind=engine)
        session = Session()
        count = 0

        pgn_files = extract_pgn_files(pgn_path)

        for filename, fileobj in pgn_files:
            print(f"📂 Procesando archivo: {filename}")
            if hasattr(fileobj, "mode") and "b" in getattr(fileobj, "mode", ""):
                import io
                fileobj = io.TextIOWrapper(fileobj, encoding="utf-8")
            with fileobj:
                while True:
                    game = chess.pgn.read_game(fileobj)
                    if game is None:
                        break
                    headers = game.headers
                    pgn_string = str(game)
                    game_id = db_utils.compute_game_id(game)

                    # Check if game already exists
                    stmt = select(games.c.game_id).where(
                        games.c.game_id == game_id)
                    exists = session.execute(stmt).first()
                    if exists:
                        show_spinner_message(f"⏭️ Processing...")
                        continue

                    games_features = extract_features_from_game(game)
                    print(games_features)
                    features = Games(games_features)

                    ins = games.insert().values(features)
                    session.execute(ins)

                    count += 1
                    print(
                        f"Importing game #{count}: {headers.get('White', 'Unknown')} vs {headers.get('Black', 'Unknown')}")

                    if max_games and count >= max_games:
                        print(f"⏹ Límite de partidas alcanzado: {max_games}")
                        session.commit()
                        session.close()
                        sys.exit(0)
        session.commit()
        session.close()
        print(f"✅ {count} game(s) imported successfully.")
    except Exception as e:
        print(
            f"❌ Error al procesar el archivo PGN: {e} - {traceback.format_exc()}")
        if e.__cause__:
            print("Original cause (inner exception):", e.__cause__)
        sys.exit(1)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description="Import or list PGN games from files.")
        parser.add_argument("--input", "-i", required=True,
                            help="Path to PGN file, directory or compressed file (.zip, .tar, .gz, .bz2)")
        parser.add_argument("--max", "-m", type=int,
                            help="Maximum number of games to import")
        parser.add_argument("--list", "-l", action="store_true",
                            help="List PGN files inside the input without importing")

        args = parser.parse_args()

        if args.list:
            print("📄 PGN files found:")
            for filename, _ in extract_pgn_files(args.input):
                print("•", filename)
            sys.exit(0)

        parse_and_save_pgn(args.input, max_games=args.max)
    except Exception as e:
        print(f"❌ Error al ejecutar el script: {e}")
        print(traceback.format_exc())
        sys.exit(1)
