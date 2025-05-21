import sys
import os
import pandas as pd

src_path = "/src"
dir = os.getcwd()
src_full_path = os.path.join(dir, src_path)
if src_full_path not in sys.path:
    sys.path.insert(0, src_full_path)
print(src_full_path)

from analyze_games import GamesAnalyzer

user = "cmess1315"
user = ["cmess1315", "cmess4401"]

# Define the path to the PGN file
games_path = "/app/data/games/cmess1315_chesscom_202505.pgn"
analyzer = GamesAnalyzer()

# Check if the file exists
print("Ruta del archivo:", games_path)
print("Verificando existencia del archivo:", os.path.exists(games_path))

# Load games with try-except to catch errors
try:
    games = analyzer.load_games(games_path)
    print("Contenido de games:", games)
    print("Tipo de games:", type(games))
    print("Primer elemento de games:", games[0] if games else "Lista vacía")
    print("Tipo del primer elemento:", type(games[0]) if games else "N/A")
except Exception as e:
    print(f"Error al cargar los juegos: {e}")

# Try to analyze the games
if games is not None:
    try:
        df, summary = analyzer.analyze_multiple_games(games, platform="chesscom")
        print("Summary:", summary)
        print("DataFrame:")
        print(df)
    except Exception as e:
        print(f"Error al analizar los juegos: {e}")
else:
    print("No se puede analizar porque games es None")

analyzer.close()