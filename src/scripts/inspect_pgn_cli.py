# inspect_pgn_cli.py

import os
import logging
import dotenv

from modules.pgn_inspector import inspect_pgn_sources_from_folder, inspect_pgn_zip_files
dotenv.load_dotenv()

PGN_PATH = os.environ.get("PGN_PATH")

# Configuración del logger
logging.basicConfig(
    filename="inspection_log.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def inspect_all_pgns_in_folder(folder_path):
    print(f"🔍 Inspeccionando archivos comprimidos en carpeta: {folder_path}")
    zip_pgn_files_count = inspect_pgn_zip_files(folder_path)
    if zip_pgn_files_count == 0:
        print(f"❌ No se encontraron archivos comprimidos en: {folder_path}")
    else:
        print(
            f"🔍 Inspección de {zip_pgn_files_count} archivos comprimidos en carpeta completada: {folder_path}\n")

    print("🔍 Inspeccionando archivos PGN individuales...")
    pgn_files_count = inspect_pgn_sources_from_folder(folder_path)
    if pgn_files_count == 0:
        print(f"❌ No se encontraron archivos PGN en: {folder_path}")
    else:
        print(
            f"🔍 Inspección de {pgn_files_count} archivos PGN en carpeta completada: {folder_path}\n")

    print("🔍 Inspección de archivos PGN finalizada.\n")


if __name__ == "__main__":

    # Inspecciona la carpeta principal
    print(f"🔍 Inspeccionando carpeta: {PGN_PATH}")
    inspect_all_pgns_in_folder(PGN_PATH)

    # Inspecciona las subcarpetas de primer nivel
    for entry in os.listdir(PGN_PATH):
        subfolder_path = os.path.join(PGN_PATH, entry)
        if os.path.isdir(subfolder_path):
            print(f"\n🔎 Inspeccionando subcarpeta: {entry}")
            inspect_all_pgns_in_folder(subfolder_path)
