import os
from pathlib import Path
from modules.pgn_utils import load_games_from_pgn  # adaptá esto a tu función real
import pandas as pd

# --- Configuración ---
BASE_DIR = Path("data/games")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

sources = ["personal", "novice", "elite", "stockfish"]
output_suffix = "_games.parquet"

def import_all_sources():
    for source in sources:
        source_path = BASE_DIR / source
        all_games = []
        for file in source_path.glob("*.pgn"):
            print(f"📥 Procesando {file.name} ({source})...")
            games = load_games_from_pgn(file, source=source)
            all_games.extend(games)
        if all_games:
            df = pd.DataFrame(all_games)
            output_file = OUTPUT_DIR / f"{source}{output_suffix}"
            df.to_parquet(output_file, index=False)
            print(f"✅ Guardado: {output_file} ({len(df)} partidas)")
        else:
            print(f"⚠️ No se encontraron partidas para '{source}'")

if __name__ == "__main__":
    import_all_sources()