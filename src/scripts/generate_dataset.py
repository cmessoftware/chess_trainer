
import argparse
import pandas as pd
import os
from pathlib import Path
import hashlib
from db.db_utils import was_game_already_processed
from modules.pgn_utils import parse_pgn_file,get_game_hash
from modules.report_utils import generate_features_from_game
from db.repository.game_repository import GameRepository
import dotenv
dotenv.load_dotenv()

import sqlite3
import zipfile
import tempfile
import shutil
import bz2
import gzip
import tarfile

DB_PATH = os.environ.get("CHESS_TRAINER_DB")
TRANING_DATA_PATH = os.environ.get("TRAINING_DATA_PATH")
PGN_PATH = os.environ.get("PGN_PATH", "/app/src/data/games")


def ensure_error_analysis_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS errors_analyzed (game_id TEXT PRIMARY KEY);")

def load_analyzed_game_ids():
    with sqlite3.connect(DB_PATH) as conn:
        result = conn.execute("SELECT game_id FROM errors_analyzed").fetchall()
        return set(row[0] for row in result)

def save_analyzed_game_id(game_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO errors_analyzed (game_id) VALUES (?);", (game_id,))

def ensure_table_exists():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS processed_games (game_hash TEXT PRIMARY KEY);")

def load_processed_hashes():
    with sqlite3.connect(DB_PATH) as conn:
        ensure_table_exists()
        # Cargar hashes de juegos procesados
        result = conn.execute("SELECT game_id FROM processed_games").fetchall()
        return set(row[0] for row in result)

def save_processed_hash(game_hash):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("INSERT OR IGNORE INTO processed_games (game_id) VALUES (?);", (game_hash,))

def compute_game_hash(game):
    return hashlib.md5(str(game).encode('utf-8')).hexdigest()


def process_games_from_db(games, max_games ,skip_existing=True):
    print(f"🔍 Encontrados {len(games)} juegos en la base de datos")
    all_rows = []
    count = 0
   
    for game in games:
        game_hash = get_game_hash(game)
        print(f"🔍 Procesando juego: {game_hash}")
        if skip_existing and was_game_already_processed(game_hash):
            print(f"⏩ Saltando {game_hash}, ya procesado")
            continue
        if max_games and count >= int(max_games):
            print(f"⏹️  Máximo de juegos procesados ({max_games}) alcanzado. Deteniendo.")
            break
        count += 1
        if not game or not game.headers or not game.mainline_moves():
            print(f"⚠️  Juego inválido o incompleto. Saltando.")
            continue

        rows = generate_features_from_game(game)
        if rows:
            all_rows.extend(rows)
            save_processed_hash(game_hash)
            last_game_id = game.headers.get("Site") or game.headers.get("Event") + "_" + game.headers.get("Date")

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["game_id"] = game_hash
    df["move_number_global"] = range(1, len(df) + 1)

    return df

def extract_zip_recursive(zip_path, extract_to):
    """Extrae archivos zip recursivamente, incluyendo zips dentro de zips."""
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(extract_to)
        for file in z.namelist():
            extracted_file = Path(extract_to) / file
            if extracted_file.is_file() and extracted_file.suffix.lower() == ".zip":
                # Extraer zip anidado en un subdirectorio temporal
                nested_dir = extracted_file.parent / (extracted_file.stem + "_unzipped")
                nested_dir.mkdir(exist_ok=True)
                extract_zip_recursive(extracted_file, nested_dir)
                extracted_file.unlink()  # Eliminar el zip anidado después de extraer

def find_pgn_files(path):
    """Busca archivos .pgn en un directorio, descomprimiendo zips recursivamente si es necesario."""
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

def process_pgn_file(pgn_path, processed_hashes, skip_existing, max_games=100):
    all_rows = []
    count = 0
    last_game_id = None

    # Buscar archivos .pgn (descomprime zips recursivamente si es necesario)
    pgn_files, temp_dirs = find_pgn_files(pgn_path)

    for file in sorted(pgn_files):
        print(f"📂 Procesando archivo: {file}")
        games = parse_pgn_file(file)
        print(f"🔍 Encontrados {len(games)} juegos en {file}")

        for game in games:
            game_hash = get_game_hash(game)
            if skip_existing and was_game_already_processed(game_hash):
                print(f"⏩ Saltando {game_hash}, ya procesado")
                continue
            if max_games and count >= int(max_games):
                print(f"⏹️  Máximo de juegos procesados ({max_games}) alcanzado. Deteniendo.")
                break
            count += 1
            if not game or not game.headers or not game.mainline_moves():
                print(f"⚠️  Juego inválido o incompleto. Saltando.")
                continue

            game_hash = compute_game_hash(game)
            if skip_existing and game_hash in processed_hashes:
                print(f"⏭️  Juego ya procesado (hash={game_hash}). Saltando.")
                continue

            rows = generate_features_from_game(game)
            if rows:
                all_rows.extend(rows)
                save_processed_hash(game_hash)
                last_game_id = game.headers.get("Site") or game.headers.get("Event") + "_" + game.headers.get("Date")
        if max_games and count >= int(max_games):
            break

    # Limpiar temporales
    for d in temp_dirs:
        shutil.rmtree(d, ignore_errors=True)

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["game_id"] = game_hash
    df["move_number_global"] = range(1, len(df) + 1)

    return df
    
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
    """Busca archivos .pgn en un directorio, descomprimiendo zips, bz2, gz, tar recursivamente si es necesario."""
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

# def process_pgn_file(pgn_path, processed_hashes, skip_existing, max_games=100):
#     all_rows = []
#     count = 0
#     last_game_id = None

#     # Buscar archivos .pgn (descomprime zips, bz2, gz, tar recursivamente si es necesario)
#     pgn_files, temp_dirs = find_pgn_files(pgn_path)

#     for file in sorted(pgn_files):
#         print(f"📂 Procesando archivo: {file}")
#         games = parse_pgn_file(file)
#         print(f"🔍 Encontrados {len(games)} juegos en {file}")

#         for game in games:
#             game_hash = get_game_hash(game)
#             if skip_existing and was_game_already_processed(game_hash):
#                 print(f"⏩ Saltando {game_hash}, ya procesado")
#                 continue
#             if max_games and count >= int(max_games):
#                 print(f"⏹️  Máximo de juegos procesados ({max_games}) alcanzado. Deteniendo.")
#                 break
#             count += 1
#             if not game or not game.headers or not game.mainline_moves():
#                 print(f"⚠️  Juego inválido o incompleto. Saltando.")
#                 continue

#             game_hash = compute_game_hash(game)
#             if skip_existing and game_hash in processed_hashes:
#                 print(f"⏭️  Juego ya procesado (hash={game_hash}). Saltando.")
#                 continue

#             rows = generate_features_from_game(game)
#             if rows:
#                 all_rows.extend(rows)
#                 save_processed_hash(game_hash)
#                 last_game_id = game.headers.get("Site") or game.headers.get("Event") + "_" + game.headers.get("Date")
#         if max_games and count >= int(max_games):
#             break

#     # Limpiar temporales
#     for d in temp_dirs:
#         shutil.rmtree(d, ignore_errors=True)

#     if not all_rows:
#         return pd.DataFrame()

#     df = pd.DataFrame(all_rows)
#     df["game_id"] = game_hash
#     df["move_number_global"] = range(1, len(df) + 1)

#     return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir',default=PGN_PATH, required=False, help='Directorio con archivos .pgn')
    parser.add_argument('--output', default=TRANING_DATA_PATH,required=False, help='Archivo CSV de salida')
    parser.add_argument('--skip-existing', default=True, action='store_true', help='Evita reprocesar juegos ya analizados')
    parser.add_argument('--max-games',required=False, default=100, help='Máximo número de juegos a procesar (opcional, para pruebas)')
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    if not input_path.is_dir():
        print(f"❌ Error: {args.input_dir} no es un directorio válido.")
        return

    repo =  GameRepository()
    processed_hashes = load_processed_hashes() if args.skip_existing else set()

    all_dfs = []
    for pgn_file in sorted(input_path.rglob("*.pgn")):
        processed_df = process_pgn_file(pgn_file, processed_hashes, args.skip_existing, args.max_games)
        all_dfs.append(processed_df)
        
    games = repo.get_all_games()
    
    for game in games:
        game_hash = get_game_hash(game)
        if args.skip_existing and was_game_already_processed(game_hash):
            print(f"⏩ Saltando {game_hash}, ya procesado")
            continue
        processed_df = process_games_from_db([game], args.max_games, args.skip_existing)
        all_dfs.append(processed_df)
 
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        print(f"📊 Se generaron {len(final_df)} filas con {len(final_df.columns)} columnas.")

        # Guardar en SQLite (solo)
        with sqlite3.connect(DB_PATH) as conn:
            existing_ids = pd.read_sql("SELECT DISTINCT game_id FROM features", conn)
            
            print(f"🔍 Cargando IDs de juegos ya procesados: {len(existing_ids)} IDs encontrados.")
            
            existing_set = set(existing_ids["game_id"])
            
            print(f"🔍 Filtrando juegos ya procesados: {len(existing_set)} juegos ya procesados.")

            new_rows = final_df[~final_df["game_id"].isin(existing_set)]
            
            print(f"🔍 Filtrando filas ya existentes: {len(new_rows)} nuevas filas a insertar. {new_rows}")

            if not new_rows.empty:
                new_rows.to_sql("features", conn, if_exists="append", index=False)
                print(f"✅ Se guardaron {len(new_rows)} en tabla 'features' de {DB_PATH}")
            else:
                print("⚠️ No se generaron datos. Todos los juegos ya están procesados")

if __name__ == "__main__":
    main()
