# pgn_inspector.py
from datetime import time
import logging
import os
from pathlib import Path
import zipfile
import tarfile
import bz2
import gzip
import chess.pgn
import io
from modules.utils import show_spinner_message
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm


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


def _inspect_single_zip(zip_path):
    try:
        result = inspect_pgn_sources_from_zip(zip_path)
        return zip_path.name, result
    except Exception as e:
        return zip_path.name, {"error": str(e)}


def inspect_pgn_zip_files(folder_path):
    zip_files = [Path(folder_path) /
                 f for f in os.listdir(folder_path) if f.endswith(".zip")]
    if not zip_files:
        msg = "❌ No se encontraron archivos .zip en la carpeta."
        print(msg)
        logging.warning(msg)
        return 0

    total_pgns = 0
    total_games = 0
    total_import_time = 0.0
    total_analysis_time = 0.0

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(_inspect_single_zip, path)
                   for path in zip_files]
        for future in tqdm(as_completed(futures), total=len(futures), desc="📦 Inspeccionando .zip"):
            zip_name, result = future.result()
            if "error" in result:
                msg = f"❌ Error al procesar {zip_name}: {result['error']}"
                print(msg)
                logging.error(msg)
                continue

            total_pgns += result["total_pgn_files"]
            total_games += result["total_games"]
            total_import_time += result["estimated_import_time_sec"]
            total_analysis_time += result["estimated_tactical_analysis_time_sec"]

            log_msg = (
                f"Archivo: {zip_name}\n"
                f"  🧾 PGNs encontrados: {result['total_pgn_files']}\n"
                f"  ♟️ Total de partidas: {result['total_games']}\n"
                f"  ⏱️ Estimado de importación: {result['estimated_import_time_sec']:.1f} s\n"
                f"  ⏱️ Estimado de análisis táctico: {result['estimated_tactical_analysis_time_sec']:.1f} s"
            )
            print(log_msg)
            logging.info(log_msg)

    def format_seconds(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02}:{minutes:02}:{secs:02}"

    summary = (
        "\n📊 RESUMEN FINAL\n"
        f"  Archivos ZIP procesados: {len(zip_files)}\n"
        f"  Archivos PGN totales: {total_pgns}\n"
        f"  Partidas totales: {total_games}\n"
        f"  ⏱️ Tiempo estimado total de importación: {format_seconds(total_import_time)}\n"
        f"  ⏱️ Tiempo estimado total de análisis táctico: {format_seconds(total_analysis_time)}"
    )

    print(summary)
    logging.info(summary)
    return total_games


def _count_games_in_file(file_path):
    import chess.pgn
    count = 0
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break
                count += 1
    except Exception:
        pass
    return str(file_path), count


def inspect_pgn_sources_from_folder(path):
    """
    Inspecciona archivos .pgn en una carpeta (no comprimidos).
    Devuelve el total de archivos PGN, partidas, y tiempo estimado.
    """
    total_pgn_files = 0
    total_games = 0

    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el path: {path}")

    pgn_files = []
    if path.is_dir():
        pgn_files = list(path.rglob("*.pgn"))
    elif path.suffix == ".pgn":
        pgn_files = [path]
    else:
        raise ValueError(
            f"El path proporcionado no es una carpeta ni un archivo .pgn: {path}")

    if not pgn_files:
        print(f"❌ No se encontraron archivos PGN en: {path}")
        return 0

    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(_count_games_in_file, f) for f in pgn_files]
        for future in tqdm(as_completed(futures), total=len(futures), desc="📂 Inspeccionando .pgn"):
            file_path, game_count = future.result()
            total_pgn_files += 1
            total_games += game_count

    import_time, tactics_time, total_time = estimate_processing_time(
        total_games)

    summary = {
        "total_pgn_files": total_pgn_files,
        "total_games": total_games,
        "estimated_import_time_sec": round(import_time, 2),
        "estimated_tactical_analysis_time_sec": round(tactics_time, 2),
        "estimated_total_time_sec": round(total_time, 2)
    }

    print(summary)
    logging.info(summary)
    return total_games


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
                fileobj = io.TextIOWrapper(
                    io.BytesIO(fileobj), encoding="utf-8")
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

    import_time, tactics_time, total_time = estimate_processing_time(
        total_games)

    return {
        "total_pgn_files": total_pgn_files,
        "total_games": total_games,
        "estimated_import_time_sec": round(import_time, 2),
        "estimated_tactical_analysis_time_sec": round(tactics_time, 2),
        "estimated_total_time_sec": round(total_time, 2)
    }
