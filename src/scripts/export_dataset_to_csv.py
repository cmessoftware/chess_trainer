import pandas as pd
import os
from pathlib import Path
import argparse
import dotenv
from datetime import datetime
from sqlalchemy import create_engine, text

dotenv.load_dotenv()

DB_URL = os.getenv("CHESS_TRAINER_DB")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
DEFAULT_OUTPUT_CSV = f"/app/src/data/training_dataset_{timestamp}.csv"


def export_training_dataset(output_csv):
    print(
        f"Exportando dataset de entrenamiento desde la base de datos {DB_URL} a {output_csv}...")

    if os.path.exists(output_csv):
        print(
            f"⚠️ El archivo {output_csv} ya existe. ¿Confirma eliminarlo? (S/N).")
        confirm = input().strip().upper()
        if confirm != 'S':
            print("Operación cancelada. El archivo no se ha modificado.")
            return

    if not DB_URL:
        raise ValueError("CHESS_TRAINER_DB no está definido.")

    engine = create_engine(DB_URL)

    # LEFT JOIN con tabla games (si existe) para agregar metadata
    query = """
    SELECT f.*, g."Site", g."Event", g."Date", g.white_player, g.black_player, g."Result"
    FROM features f
    LEFT JOIN games g ON f.game_id = g.game_id
    """

    with engine.connect() as conn:
        df = pd.read_sql_query(text(query), conn)

    df.to_csv(output_csv, index=False)
    print(f"✅ Dataset exportado a {output_csv} con {len(df)} filas.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Export training dataset from database to CSV.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_CSV,
                        help="Ruta del archivo CSV de salida (por defecto: %(default)s)")
    args = parser.parse_args()

    export_training_dataset(args.output)
