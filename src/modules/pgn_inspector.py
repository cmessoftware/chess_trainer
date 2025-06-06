# pgn_inspector.py
from pathlib import Path
import zipfile
import tarfile
import bz2
import gzip
import chess.pgn
import io
from modules.utils import show_spinner_message

def estimate_processing_time(num_games, avg_time_per_game=0.05, avg_tactical_analysis_time=0.15):
    """
    Estima el tiempo de procesamiento de importación y análisis táctico.
    Los tiempos por defecto son estimaciones conservadoras en segundos por partida.
    """
    import_time = num_games * avg_time_per_game
    tactics_time = num_games * avg_tactical_analysis_time
    total_time = import_time + tactics_time
    return import_time, tactics_time, total_time

def count_games_in_pgn(file_like):
    """Cuenta la cantidad de partidas PGN en un archivo ya abierto (modo texto)."""
    count = 0
    while True:
        show_spinner_message("🔍 Counting games in pgn files...")
        try:
            game = chess.pgn.read_game(file_like)
            if game is None:
                break
            count += 1
        except Exception:
            break
    return count

def inspect_pgn_sources_from_zip(path):
    """
    Inspecciona archivos .pgn, incluso dentro de .zip, .tar, .gz, y .bz2.
    Devuelve el total de archivos PGN, partidas, y tiempo estimado.
    """
    total_pgn_files = 0
    total_games = 0

    def handle_pgn_stream(filename, fileobj):
        nonlocal total_pgn_files, total_games
        total_pgn_files += 1
        try:
            if isinstance(fileobj, (bytes, bytearray)):
                fileobj = io.TextIOWrapper(io.BytesIO(fileobj), encoding="utf-8")
            elif not isinstance(fileobj, io.TextIOBase):
                fileobj = io.TextIOWrapper(fileobj, encoding="utf-8")
            total_games += count_games_in_pgn(fileobj)
        except Exception:
            pass

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el path: {path}")

    def process_file(filepath):
        if filepath.suffix == ".pgn":
            with open(filepath, "r", encoding="utf-8") as f:
                handle_pgn_stream(str(filepath), f)
        elif filepath.suffix == ".zip":
            with zipfile.ZipFile(filepath, "r") as zipf:
                for name in zipf.namelist():
                    if name.endswith(".pgn"):
                        with zipf.open(name) as f:
                            handle_pgn_stream(name, f)
                    elif name.endswith(".bz2"):
                        with zipf.open(name) as bz:
                            decompressed = bz2.decompress(bz.read())
                            handle_pgn_stream(name, decompressed)
        elif filepath.suffix == ".tar":
            with tarfile.open(filepath, "r") as tarf:
                for member in tarf.getmembers():
                    if member.name.endswith(".pgn"):
                        with tarf.extractfile(member) as f:
                            handle_pgn_stream(member.name, f)
                    elif member.name.endswith(".bz2"):
                        with tarf.extractfile(member) as f:
                            decompressed = bz2.decompress(f.read())
                            handle_pgn_stream(member.name, decompressed)
        elif filepath.suffix == ".bz2":
            with bz2.open(filepath, "rb") as f:
                decompressed = f.read()
                handle_pgn_stream(str(filepath), decompressed)
        elif filepath.suffix == ".gz":
            with gzip.open(filepath, "rt", encoding="utf-8") as f:
                handle_pgn_stream(str(filepath), f)

    if path.is_dir():
        for file in path.rglob("*"):
            if file.suffix in [".pgn", ".zip", ".tar", ".bz2", ".gz"]:
                process_file(file)
    else:
        process_file(path)

    import_time, tactics_time, total_time = estimate_processing_time(total_games)

    return {
        "total_pgn_files": total_pgn_files,
        "total_games": total_games,
        "estimated_import_time_sec": round(import_time, 2),
        "estimated_tactical_analysis_time_sec": round(tactics_time, 2),
        "estimated_total_time_sec": round(total_time, 2)
    }
