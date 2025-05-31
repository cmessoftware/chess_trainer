
import argparse
import pandas as pd
import os
from pathlib import Path
import hashlib
from modules.db_utils import was_game_already_processed
from modules.pgn_utils import parse_pgn_file,get_game_hash
from modules.report_utils import generate_features_from_game
import dotenv
dotenv.load_dotenv()

import sqlite3

DB_PATH = os.environ.get("CHESS_TRAINER_DB")
TRANING_DATA_PATH = os.environ.get("TRAINING_DATA_PATH", "/app/src/data/training_dataset.csv")
PGN_PATH = os.environ.get("PGN_PATH", "/app/src/data/games")

def init_features_table(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS features (
                game_id TEXT,
                move_number INTEGER,
                fen TEXT,
                move_san TEXT,
                move_uci TEXT,
                material_balance REAL,
                material_total REAL,
                num_pieces INTEGER,
                branching_factor INTEGER,
                self_mobility INTEGER,
                opponent_mobility INTEGER,
                phase TEXT,
                player_color TEXT,
                has_castling_rights INTEGER,
                move_number_global INTEGER,
                is_repetition INTEGER,
                is_low_mobility INTEGER
            );
        """)


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


def process_pgn_file(pgn_path, processed_hashes, skip_existing, max_games=100):
    print(f"📂 Procesando archivo: {pgn_path}")
    games = parse_pgn_file(pgn_path)
    print(f"🔍 Encontrados {len(games)} juegos en {pgn_path}")
    all_rows = []
    count = 0
    last_game_id = None

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

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["game_id"] = game_hash
    df["move_number_global"] = range(1, len(df) + 1)

    return df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir',default=PGN_PATH, required=False, help='Directorio con archivos .pgn')
    parser.add_argument('--output', default=TRANING_DATA_PATH,required=False, help='Archivo CSV de salida')
    parser.add_argument('--skip-existing', action='store_true', help='Evita reprocesar juegos ya analizados')
    parser.add_argument('--max-games',required=False, default=100, help='Máximo número de juegos a procesar (opcional, para pruebas)')
    args = parser.parse_args()

    input_path = Path(args.input_dir)
    if not input_path.is_dir():
        print(f"❌ Error: {args.input_dir} no es un directorio válido.")
        return

    processed_hashes = load_processed_hashes() if args.skip_existing else set()

    all_dfs = []
    for pgn_file in sorted(input_path.rglob("*.pgn")):
        processed_df = process_pgn_file(pgn_file, processed_hashes, args.skip_existing, args.max_games)
        all_dfs.append(processed_df)

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        print(f"📊 Se generaron {len(final_df)} filas con {len(final_df.columns)} columnas.")

        # Guardar en SQLite (solo)
        with sqlite3.connect(DB_PATH) as conn:
            existing_ids = pd.read_sql("SELECT DISTINCT game_id FROM features", conn)
            existing_set = set(existing_ids["game_id"])

            new_rows = final_df[~final_df["game_id"].isin(existing_set)]

            if not new_rows.empty:
                new_rows.to_sql("features", conn, if_exists="append", index=False)
                print(f"✅ Se guardaron {len(new_rows)} en tabla 'features' de {DB_PATH}")
            else:
                print("⚠️ No se generaron datos. ¿Todos los juegos ya estaban procesados?")

if __name__ == "__main__":
    main()
