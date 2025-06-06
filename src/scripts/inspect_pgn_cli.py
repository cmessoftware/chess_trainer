# inspect_pgn_cli.py

import os
import time
import logging

from modules.pgn_inspector import inspect_pgn_sources_from_zip

# Configuración del logger
logging.basicConfig(
    filename="inspection_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def inspect_all_zips_in_folder(folder_path):
    zip_files = [f for f in os.listdir(folder_path) if f.endswith(".zip")]
    if not zip_files:
        msg = "❌ No se encontraron archivos .zip en la carpeta."
        print(msg)
        logging.warning(msg)
        return

    total_pgns = 0
    total_games = 0
    total_import_time = 0.0
    total_analysis_time = 0.0

    for zip_name in zip_files:
        zip_path = os.path.join(folder_path, zip_name)
        print(f"\n📦 Inspeccionando: {zip_name}")
        start = time.time()

        try:
            result = inspect_pgn_sources_from_zip(zip_path)
        except Exception as e:
            msg = f"❌ Error al procesar {zip_name}: {e}"
            print(msg)
            logging.error(msg)
            continue

        elapsed = time.time() - start
        total_pgns += result["total_pgn_files"]
        total_games += result["total_games"]
        total_import_time += result["estimated_import_time_sec"]
        total_analysis_time += result["estimated_tactical_analysis_time_sec"]

        log_msg = (
            f"Archivo: {zip_name}\n"
            f"  🧾 PGNs encontrados: {result['total_pgn_files']}\n"
            f"  ♟️ Total de partidas: {result['total_games']}\n"
            f"  ⏱️ Estimado de importación: {result['estimated_import_time_sec']:.1f} s\n"
            f"  ⏱️ Estimado de análisis táctico: {result['estimated_tactical_analysis_time_sec']:.1f} s\n"
            f"  ✅ Completado en {elapsed:.1f} s"
        )

        print(log_msg)
        logging.info(log_msg)

    # Resumen Final
    summary = (
        "\n📊 RESUMEN FINAL\n"
        f"  Archivos ZIP procesados: {len(zip_files)}\n"
        f"  Archivos PGN totales: {total_pgns}\n"
        f"  Partidas totales: {total_games}\n"
        f"  ⏱️ Tiempo estimado total de importación: {total_import_time:.1f} s\n"
        f"  ⏱️ Tiempo estimado total de análisis táctico: {total_analysis_time:.1f} s"
    )

    print(summary)
    logging.info(summary)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analiza todos los archivos ZIP en una carpeta.")
    parser.add_argument("--folder", "-f", required=True, help="Ruta a la carpeta que contiene los ZIP")
    args = parser.parse_args()
    inspect_all_zips_in_folder(args.folder)
