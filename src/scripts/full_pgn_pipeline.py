
import os

import chess
from modules.generate_dataset_from_pgn import generate_dataset_from_pgn
from tactical_analysis import process_csv
from extract_move_times import extract_move_times
from modules.db_utils import is_game_in_db, compute_game_id
import argparse


def run_import_if_needed(pgn_path):
    with open(pgn_path, encoding="utf-8") as f:
        while True:
            game = chess.pgn.read_game(f)
            if game is None:
                break
            game_id = compute_game_id(game)
            if not is_game_in_db(game_id):
                print(f"🆕 Importando partidas desde: {pgn_path}")
                os.system(f"python scripts/import_games.py --input {pgn_path}")
                return
    print("✅ Todas las partidas ya fueron importadas.")

def full_pipeline(pgn_path, output_prefix, limit_games=None):
    base_csv = f"{output_prefix}_base.csv"
    enriched_csv = f"{output_prefix}_enriched.csv"
    time_csv = f"{output_prefix}_times.csv"

    print(f"Procesando PGN: {pgn_path}")
    generate_dataset_from_pgn(pgn_path, base_csv, limit_games=limit_games)

    print("Aplicando análisis táctico con Stockfish...")
    process_csv(base_csv, enriched_csv)

    print("Analizando tiempos por jugada (si existen anotaciones de reloj)...")
    try:
        extract_move_times(pgn_path, time_csv, limit_games=limit_games)
        print(f"Tiempos extraídos a: {time_csv}")
    except Exception as e:
        print("No se pudo extraer tiempos: ", e)

    print(f"Pipeline completo. Dataset final: {enriched_csv}")
    if __name__ == "__main__":

        parser = argparse.ArgumentPaFrser(description="Run the full PGN processing pipeline.")
        parser.add_argument("pgn_path", type=str, help="Path to the PGN file.")
        parser.add_argument("output_prefix", type=str, help="Prefix for output files.")
        parser.add_argument("--limit_games", type=int, default=None, help="Limit the number of games to process.")

        args = parser.parse_args()
        full_pipeline(args.pgn_path, args.output_prefix, limit_games=args.limit_games)
