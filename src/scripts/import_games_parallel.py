# src/scripts/import_games_parallel.py

import os
import sys
import traceback
from typing import IO
import chess
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from concurrent.futures import ProcessPoolExecutor
from db.models.games import Games
from db.repository.games_repository import GamesRepository
from modules.pgn_batch_loader import load_pgn_batches, parse_game_text
from modules.pgn_utils import split_pgn_file_by_games

# Allow relative imports from /src
sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..')))

dotenv.load_dotenv()
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
PGN_PATH = os.environ.get("PGN_PATH", "./data/games")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
GAMES_PER_CHUNK = int(os.environ.get("GAMES_PER_CHUNK", 500))

games_repo = GamesRepository()


def process_chunk(games_texts):
    print(f"🔍 Processing chunk of {len(games_texts)} games...")
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        for game_text in games_texts:
            # Show only the first 50 characters
            print(f"🔍 Processing game: {game_text[:50]}...")
            parsed = parse_game_text(game_text)
            print(f"🔍 Parsed game: {parsed}")
            print(
                f"🔍 Processing game: {parsed.get('game_id', 'unknown')}")
            if parsed:
                game = Games(**parsed)
                # Check if the game already exists by its PK (game_id)
                if games_repo.is_game_in_db(game.game_id):
                    print(
                        f"⚠️ Game already exists in games: {game.game_id}, skipping.")
                    continue
                session.add(game)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"❌ Error in process: {e}")
    finally:
        session.close()


def main():
    batched_files = load_pgn_batches(PGN_PATH, batch_size=20)
    print(f"batched_files type: {type(batched_files)}")
    all_chunks = []
    pgn_handle: IO = None
    for batch in batched_files:
        for filename, file_obj in batch:
            try:
                print(f"🔍 Processing file: {filename}")
                while True:
                    pgn_handle = chess.pgn.read_game(file_obj)
                    if pgn_handle is None:
                        print(f"🔍 No more games in {filename}, breaking.")
                        break
                    chunks = split_pgn_file_by_games(
                        pgn_handle, GAMES_PER_CHUNK)
                    all_chunks.extend(chunks)
            except Exception as e:
                print(
                    f"⚠️ Error processing {pgn_handle}: {e} - {traceback.format_exc()}")

    print(f"🧩 Total chunks to process: {len(all_chunks)}")

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_chunk, chunk)
                   for chunk in all_chunks]
        for future in futures:
            future.result()  # wait for each result to catch errors

    print("✅ Parallel import completed.")


if __name__ == "__main__":
    try:
        if not DB_URL:
            raise ValueError(
                "CHESS_TRAINER_DB_URL environment variable is not set.")
        if not os.path.exists(PGN_PATH):
            raise FileNotFoundError(f"PGN_PATH does not exist: {PGN_PATH}")
        main()
    except Exception as e:
        print(f"❌ Error during import: {e} - {traceback.format_exc()}")
        if hasattr(e, 'args'):
            print(f"🔍 Args: {e.args}")
        if e.__cause__:
            print(f"🔍 Cause: {e.__cause__}")
        sys.exit(1)
