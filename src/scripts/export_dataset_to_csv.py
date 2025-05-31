import sqlite3
import pandas as pd
import os
from pathlib import Path
import argparse
import dotenv
dotenv.load_dotenv()

DB_PATH = os.getenv("CHESS_TRAINER_DB")
OUTPUT_CSV = "/app/src/data/training_dataset.csv"

def export_training_dataset():
    print(f"Exportando dataset de entrenamiento desde la base de datos {DB_PATH} a {OUTPUT_CSV}...")
    
    if os.path.exists(OUTPUT_CSV):
        print(f"⚠️ El archivo {OUTPUT_CSV} ya existe. ¿Confirma eliminarlo? (S/N).")
        confirm = input().strip().upper()
        if confirm != 'S':
            print("Operación cancelada. El archivo no se ha modificado.")
            return
    
    if not DB_PATH:
        raise ValueError("CHESS_TRAINER_DB no está definido.")
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"No se encuentra la base de datos: {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        # LEFT JOIN con tabla games (si existe) para agregar metadata
        query = """
        SELECT f.*, g.Site, g.Event, g.Date, g.white_player , g.black_player, g.Result
        FROM features f
        LEFT JOIN games g ON f.game_id = g.game_id
        """
        df = pd.read_sql_query(query, conn)

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"✅ Dataset exportado a {OUTPUT_CSV} con {len(df)} filas.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export training dataset from database to CSV.")
    parser.add_argument("--output", default=OUTPUT_CSV, help="Ruta del archivo CSV de salida (por defecto: %(default)s)")
    args = parser.parse_args()

    OUTPUT_CSV = args.output
    export_training_dataset()
