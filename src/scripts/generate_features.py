# Configuration of SQLAlchemy for Postgres
# Example: "postgresql://user:password@host:port/dbname"

# Definition of the table using SQLAlchemy

import argparse
import bz2
import gzip
from importlib import metadata
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
import zipfile

from altair import Column
import pandas as pd
from sqlalchemy import String, Table, insert, select
from modules.pgn_utils import get_game_hash, parse_games_from_orm
from repository.games_repository import GameRepository
from sqlalchemy import create_engine, MetaData
from db.db_utils import DBUtils
import dotenv
dotenv.load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
# Define default paths
PGN_PATH = os.environ.get("PGN_PATH")
TRANING_DATA_PATH = os.environ.get("TRANING_DATA_PATH")

db_utils = DBUtils()
engine = create_engine(DATABASE_URL)
metadata = MetaData()


def ensure_table_exists():
    processed_features_table = Table(
        "processed_features", metadata, autoload_with=engine)
    metadata.create_all(engine, tables=[processed_features_table])


def load_processed_hashes():
    ensure_table_exists()
    with engine.connect() as conn:
        processed_features_table = Table(
            "processed_features",
            metadata,
            autoload_with=engine
        )
        result = conn.execute(processed_features_table.select()).mappings()
        return set(row["game_id"] for row in result)


def save_processed_hash(game_hash):
    # Use SQLAlchemy to insert into the processed_features table
    processed_features_table = Table(
        "processed_features",
        metadata,
        autoload_with=engine
    )
    with engine.begin() as conn:
        stmt = insert(processed_features_table).values(
            game_id=game_hash).on_conflict_do_nothing(index_elements=['game_id'])
        conn.execute(stmt)


def extract_zip_recursive(zip_path, extract_to):
    """Extract zip files recursively, including zips inside zips."""
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_to)
        for file in z.namelist():
            extracted_file = Path(extract_to) / file
            if extracted_file.is_file() and extracted_file.suffix.lower() == ".zip":
                # Extract nested zip in a temporary subdirectory
                nested_dir = extracted_file.parent / \
                    (extracted_file.stem + "_unzipped")
                nested_dir.mkdir(exist_ok=True)
                extract_zip_recursive(extracted_file, nested_dir)
                extracted_file.unlink()  # Delete the nested zip after extraction


def find_pgn_files(path):
    """Search for .pgn files in a directory, recursively extracting zips if necessary."""
    temp_dirs = []
    pgn_files = []

    def _find(path):
        if Path(path).is_file():
            if Path(path).suffix.lower() == ".pgn":
                pgn_files.append(Path(path))
            elif Path(path).suffix.lower() == ".zip":
                temp_dir = tempfile.mkdtemp()
                temp_dirs.append(temp_dir)
                extract_zip_recursive(path, temp_dir)
                _find(temp_dir)
        elif Path(path).is_dir():
            for item in Path(path).iterdir():
                _find(item)

    _find(path)
    return pgn_files, temp_dirs


def extract_bz2(bz2_path, extract_to):
    out_path = Path(extract_to) / Path(bz2_path).with_suffix('').name
    with bz2.open(bz2_path, 'rb') as f_in, open(out_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    return out_path


def extract_gz(gz_path, extract_to):
    out_path = Path(extract_to) / Path(gz_path).with_suffix('').name
    with gzip.open(gz_path, 'rb') as f_in, open(out_path, 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
    return out_path


def extract_tar(tar_path, extract_to):
    with tarfile.open(tar_path, 'r:*') as tar:
        tar.extractall(path=extract_to)


def find_pgn_files(path):
    """Search for .pgn files in a directory, recursively extracting zips, bz2, gz, tar if necessary."""
    temp_dirs = []
    pgn_files = []

    def _find(path):
        p = Path(path)
        if p.is_file():
            ext = p.suffix.lower()
            if ext == ".pgn":
                pgn_files.append(p)
            elif ext == ".zip":
                temp_dir = tempfile.mkdtemp()
                temp_dirs.append(temp_dir)
                extract_zip_recursive(p, temp_dir)
                _find(temp_dir)
            elif ext == ".bz2":
                temp_dir = tempfile.mkdtemp()
                temp_dirs.append(temp_dir)
                out_file = extract_bz2(p, temp_dir)
                _find(out_file)
            elif ext == ".gz":
                temp_dir = tempfile.mkdtemp()
                temp_dirs.append(temp_dir)
                out_file = extract_gz(p, temp_dir)
                _find(out_file)
            elif ext == ".tar" or p.name.endswith(".tar.gz") or p.name.endswith(".tgz"):
                temp_dir = tempfile.mkdtemp()
                temp_dirs.append(temp_dir)
                extract_tar(p, temp_dir)
                _find(temp_dir)
        elif p.is_dir():
            for item in p.iterdir():
                _find(item)

    _find(path)
    return pgn_files, temp_dirs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-games', required=False, default=100,
                        help='Maximum number of games to process (optional, for testing)')
    args = parser.parse_args()
    input_path = Path(PGN_PATH)

    input_path = Path(args.input_dir)
    max_games = int(args.max_games) if args.max_games else None
    if not input_path.is_dir():
        print(f"❌ Error: {args.input_dir} is not a valid directory.")
        return

    repo = GameRepository()

    all_dfs = []
    games = repo.get_all_games()

    print(f"🔍 Found {len(games)} games in the database")

    for i, (game_id, game) in enumerate(parse_games_from_orm(games)):
        if i >= int(args.max_games):
            print(
                f"🔍 Reached max_games limit: {args.max_games}. Stopping processing.")
            break

        game_hash = get_game_hash(game)
        print(f"🔍 Processing game {game_hash}...")

        processed_df = db_utils.process_game_from_db(game)

        if isinstance(processed_df, tuple):
            processed_df = processed_df[0]

        print(
            f"📄 Processed game {game_hash} with {len(processed_df)} rows: {processed_df.head()}")

        all_dfs.append(processed_df)
        print(f"🔍 Total games processed: {len(all_dfs)}")
        print("📊 all_dfs:", all_dfs)

        if all_dfs:
            final_df = pd.concat(all_dfs, ignore_index=True)
            print(
                f"📊 Generated {len(final_df)} rows with {len(final_df.columns)} columns.")

        # Save to DB (only)
        with engine.begin() as conn:
            # Read the IDs of games already processed in the 'features' table
            features_table = Table(
                "features", MetaData(), autoload_with=engine)
            stmt = select(features_table.c.game_id).distinct()
            result = conn.execute(stmt)
            existing_ids = set(row[0] for row in result)

            print(
                f"🔍 Loading IDs of already processed games: {len(existing_ids)} IDs found.")
            print(
                f"🔍 Filtering already processed games: {len(existing_ids)} games already processed.")

            print("Columns in final_df:", final_df.columns.tolist())
            print("First rows:", final_df.head())

            new_rows = final_df[~final_df["game_id"].isin(existing_ids)]

            print(
                f"🔍 Filtering already existing rows: {len(new_rows)} new rows to insert. {new_rows}")

            if not new_rows.empty:
                # Insert the new data using SQLAlchemy
                new_rows.to_sql("features", con=engine,
                                if_exists="append", index=False, method="multi")
                print(
                    f"✅ Saved {len(new_rows)} in 'features' table of the database")
            else:
                print("⚠️ No data generated. All games are already processed")


if __name__ == "__main__":
    main()
