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
from modules.utils import show_spinner_message
load_dotenv()  # Carga las variables del archivo .env

DB_PATH = os.environ.get("CHESS_TRAINER_DB")
PATH_PGN = os.environ.get("PATH_PGN")
db_utils = DBUtils()

if not DB_PATH or not os.path.exists(DB_PATH):
    raise FileNotFoundError(
        f"❌ Database not found or CHESS_TRAINER_DB unset: {DB_PATH}")


def extract_pgn_files(input_path):
    def is_pgn_file(name):
        return name.endswith(".pgn")

    def extract_from_nested_compressed(name, byte_stream):
        # Detect inner compressed formats
        if name.endswith(".bz2"):
            with bz2.open(byte_stream, "rt", encoding="utf-8") as f:
                with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".pgn", encoding="utf-8") as tmp:
                    shutil.copyfileobj(f, tmp)
                    tmp.flush()
                    tmp.seek(0)
                    yield name.replace(".bz2", ""), open(tmp.name, encoding="utf-8")
        elif name.endswith(".gz"):
            with gzip.open(byte_stream, "rt", encoding="utf-8") as f:
                with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".pgn", encoding="utf-8") as tmp:
                    shutil.copyfileobj(f, tmp)
                    tmp.flush()
                    tmp.seek(0)
                    yield name.replace(".gz", ""), open(tmp.name, encoding="utf-8")
        elif name.endswith(".pgn"):
            with tempfile.NamedTemporaryFile("w+b", delete=False) as tmp:
                tmp.write(byte_stream.read())
                tmp.flush()
                yield name, open(tmp.name, encoding="utf-8")

    if os.path.isdir(input_path):
        for filename in os.listdir(input_path):
            yield from extract_pgn_files(os.path.join(input_path, filename))

    elif zipfile.is_zipfile(input_path):
        with zipfile.ZipFile(input_path) as zf:
            for name in zf.namelist():
                with zf.open(name) as f:
                    yield from extract_from_nested_compressed(name, f)

    elif tarfile.is_tarfile(input_path):
        with tarfile.open(input_path) as tf:
            for member in tf.getmembers():
                if member.isfile():
                    f = tf.extractfile(member)
                    if f:
                        yield from extract_from_nested_compressed(member.name, f)

    elif input_path.endswith(".gz") or input_path.endswith(".bz2"):
        # Single compressed file on disk
        yield from extract_from_nested_compressed(input_path, open(input_path, "rb"))

    elif is_pgn_file(input_path):
        yield input_path, open(input_path, encoding="utf-8")

    else:
        print(f"❌ Unsupported file or format: {input_path}")


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

        for filename, fileobj in extract_pgn_files(pgn_path):
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

                    ins = games.insert().values(
                        game_id=game_id,
                        white_player=headers.get("White", ""),
                        black_player=headers.get("Black", ""),
                        white_elo=int(headers.get("WhiteElo", 0)) if headers.get(
                            "WhiteElo", "").isdigit() else None,
                        black_elo=int(headers.get("BlackElo", "0")) if headers.get(
                            "BlackElo", "").isdigit() else None,
                        result=headers.get("Result", "0-0"),
                        event=headers.get("Event", ""),
                        site=headers.get("Site", ""),
                        date=headers.get("Date", ""),
                        eco=headers.get("ECO", ""),
                        opening=headers.get("Opening", ""),
                        pgn=pgn_string
                    )
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
