import argparse
from concurrent.futures import ProcessPoolExecutor
from importlib import metadata
from io import StringIO
import os
import sys
import traceback
import chess
import chess.pgn
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from modules.pgn_utils import get_game_id, is_valid_pgn
from modules.features_generator import generate_features_from_game
from db.repository.features_repository import FeaturesRepository
from db.repository.processed_feature_repository import ProcessedFeaturesRepository
from db.repository.games_repository import GamesRepository
from db.db_utils import DBUtils

# Load environment variables
import dotenv
dotenv.load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
PGN_PATH = os.environ.get("PGN_PATH", "./data/games")
MAX_WORKERS = int(os.environ.get("MAX_WORKERS", 4))
FEATURES_PER_CHUNK = int(os.environ.get("FEATURES_PER_CHUNK", 500))

engine = create_engine(DB_URL)
metadata = MetaData()
db_utils = DBUtils()


def load_processed_hashes():
    print("🔍 Loading processed game hashes...")
    try:
        processed_repo = ProcessedFeaturesRepository(
            session_factory=lambda: sessionmaker(bind=engine)())
        processed_hashes = processed_repo.get_all()
        return set(processed_hashes)
    except Exception as e:
        print(f"❌ Error loading processed hashes: {e}")
        return set()


def process_chunk(pgn_list: list[str]):
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        features_repo = FeaturesRepository(
            session_factory=lambda: sessionmaker(bind=engine)())

        processed_features_repo = ProcessedFeaturesRepository(
            session_factory=lambda: sessionmaker(bind=engine)())

        if not pgn_list:
            print("🔍 No games to process in this chunk.")
            return

        processed_hashes = load_processed_hashes()

        for pgn_text in pgn_list:
            try:
                print(f"game pgn: {pgn_text[:200]}...")
                valid, parsed_game = is_valid_pgn(pgn_text)

                if not valid:
                    print(f"❌ Invalid PGN format: {pgn_text[:200]}...")
                    continue

                game_id = get_game_id(parsed_game)
                if game_id in processed_hashes:
                    print(f"⚠️ Game already processed: {game_id}, skipping.")
                    continue

                parsed_game = chess.pgn.read_game(StringIO(pgn_text))

                print(f"Processing game ID: {game_id}")
                print(
                    f"Processing game from database... {parsed_game.headers.get('White')} vs {parsed_game.headers.get('Black')}")

                features = generate_features_from_game(
                    parsed_game, game_id=game_id)

                if not isinstance(features, list) or not all(isinstance(f, dict) for f in features):
                    print(
                        f"❌ ERROR: generate_features_from_game devolvió formato inválido para {game_id}")
                    continue

                if len(features) == 0:
                    print(f"⚠️ No features generados para game {game_id}")
                    continue

                print(
                    f"🔍 Game {game_id} tiene {len(features)} features generados")
                print(
                    f"🔍 Features a agregar par para game {game_id}: {features}")

                features_repo.save_many_features(features)
                processed_features_repo.save_processed_hash(game_id)

                print(f"✅ Game {game_id} processed and features saved.")

            except Exception as e:
                print(f"❌ Error al procesar una partida:\n{pgn_text[:200]}...")
                print(f"🔍 Detalle del error: {e} - {traceback.format_exc()}")
                continue

        session.commit()
    except Exception as e:
        session.rollback()
        print(
            f"❌ Error en el procesamiento del chunk: {e} {traceback.format_exc()}")
        if e.__cause__:
            print(f"🔍 Causa del error: {e.__cause__}")
    finally:
        session.close()


def chunkify(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def main(max_games=1000):
    games_repo = GamesRepository()

    all_games = []

    try:
        offset = 0
        while len(all_games) < max_games:
            current_chunk = games_repo.get_games_by_pagination(
                offset=offset, limit=FEATURES_PER_CHUNK)
            if not current_chunk:
                break
            all_games.extend(current_chunk)
            offset += FEATURES_PER_CHUNK
    except Exception as e:
        print(f"⚠️ Error getting games: {e}")
        return

    if not all_games:
        print("🔍 No games to process.")
        return

    all_game_pgns = [game.pgn for game in all_games]
    chunks = list(chunkify(all_game_pgns, FEATURES_PER_CHUNK))
    print(f"🧩 Total chunks to process: {len(chunks)}")

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_chunk, chunk) for chunk in chunks]
        for future in futures:
            future.result()

    print("✅ Parallel import completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import chess games and generate features in parallel.")
    parser.add_argument('--max-games', required=False, default=1000,
                        help='Maximum number of games to process (optional, for testing)')
    args = parser.parse_args()
    try:
        if not DB_URL:
            raise ValueError(
                "CHESS_TRAINER_DB_URL environment variable is not set.")
        main(int(args.max_games))
    except Exception as e:
        print(f"❌ Error during import: {e}")
        if e.__cause__:
            print(f"🔍 Cause: {e.__cause__}")
        sys.exit(1)
