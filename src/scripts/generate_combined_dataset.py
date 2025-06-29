import pandas as pd
from pathlib import Path

# --- Paths ---
BASE_DIR = Path("data/processed")
OUTPUT_FILE = "training_dataset.parquet"

# --- Cargar datasets por origen ---
sources = {
    "personal": BASE_DIR / "personal_games.parquet",
    "novice": BASE_DIR / "novice_games.parquet",
    "elite": BASE_DIR / "elite_games.parquet",
    "stockfish": BASE_DIR / "stockfish_games.parquet"
}

dfs = []
for label, path in sources.items():
    if path.exists():
        df = pd.read_parquet(path)
        df["source"] = label
        dfs.append(df)
    else:
        print(f"⚠️ Archivo no encontrado: {path}")

# --- Concatenar y balancear ---
df_all = pd.concat(dfs, ignore_index=True)

# (Opcional) Balanceo manual
# df_all = df_all.groupby("source").apply(lambda g: g.sample(n=min(50000, len(g)), random_state=42)).reset_index(drop=True)

# --- Guardar dataset combinado ---
df_all.to_parquet(BASE_DIR / OUTPUT_FILE, index=False)
print(
    f"✅ Dataset final guardado como {OUTPUT_FILE} con {len(df_all)} partidas.")
