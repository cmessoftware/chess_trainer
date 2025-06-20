from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
import sys
import traceback
import chess.pgn
import argparse
from db.db_utils import DBUtils
from modules.utils import show_spinner_message
from modules.pgn_batch_loader import extract_features_from_game, extract_pgn_files
from dotenv import load_dotenv
from db.repository.games_repository import GamesRepository
load_dotenv()
DB_PATH_URL = os.environ.get("CHESS_TRAINER_DB_URL")
PATH_PGN = os.environ.get("PATH_PGN")
db_utils = DBUtils()


def parse_and_save_pgn(pgn_path, db_url=DB_PATH_URL, max_games=None):
    try:
        if not os.path.exists(pgn_path):
            print(f"❌ Path does not exist: {pgn_path}")
            return

        if not db_url:
            print("❌ CHESS_TRAINER_DB_URL is not configured")
            return

        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        repo = GamesRepository(session_factory=lambda: session)
        count = 0
        pgn_files = extract_pgn_files(pgn_path)

        for filename, fileobj in pgn_files:
            print(f"📂 Processing file: {filename}")
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
                    # game_id = db_utils.compute_game_id(game)
                    show_spinner_message(
                        f"Processing game: {headers.get('White', 'Unknown')} vs {headers.get('Black', 'Unknown')}")

                    game_features = extract_features_from_game(pgn_string)

                    if repo.game_exists(game_features['game_id']):
                        print("⏭️ Already exists, skipping...")
                        continue

                    print(f"📖 Saving game data: {game_features}")
                    repo.save_game(game_features)

                    count += 1
                    print(
                        f"Importing game #{count}: {headers.get('White', 'Unknown')} vs {headers.get('Black', 'Unknown')}")

                    if max_games and count >= max_games:
                        print(f"⏹ Limit reached: {max_games}")
                        break
        repo.commit()
        repo.close()
        print(f"✅ {count} games imported.")
    except Exception as e:
        print(f"❌ Error processing PGN: {e}\n{traceback.format_exc()}")
        if e.__cause__:
            print("Original cause:", e.__cause__)
        sys.exit(1)
