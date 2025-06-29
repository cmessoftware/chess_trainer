import os
import traceback
from pathlib import Path
import chess
from dotenv import load_dotenv
from modules.pgn_batch_loader import extract_pgn_files, extract_features_from_game
from db.repository.games_repository import GamesRepository
from sqlalchemy.orm import sessionmaker

load_dotenv()
DB_PATH_URL = os.environ.get("CHESS_TRAINER_DB_URL")
BASE_DIR = Path(os.environ.get("PGN_PATH"))
SOURCES = ["personal", "novice", "elite", "stockfish", "fide"]
BLOCK_SIZE = 1000

# Recoge todos los archivos válidos por fuente


def collect_pgn_files_by_source():
    pgn_dict = {}
    for source in SOURCES:
        source_path = BASE_DIR / source
        if not source_path.exists():
            print(f"⚠️ No se encontró la carpeta de la fuente: {source_path}")
            continue

        file_list = []
        for root, _, files in os.walk(source_path):
            for name in files:
                if any(name.endswith(ext) for ext in [".pgn", ".zip", ".tar", ".gz", ".bz2"]):
                    file_list.append(Path(root) / name)

        pgn_dict[source] = file_list
    return pgn_dict

# Alterna entre fuentes importando BLOCK_SIZE partidas por tanda


def import_balanced_games():

    repo = GamesRepository()

    pgn_sources = collect_pgn_files_by_source()
    indices = {source: 0 for source in pgn_sources}
    exhausted = set()
    total_imported = 0

    print(f"🔁 Iniciando importación balanceada por bloques de {BLOCK_SIZE}")

    while len(exhausted) < len(pgn_sources):
        for source in SOURCES:
            if source in exhausted or source not in pgn_sources:
                continue

            files = pgn_sources[source]
            if indices[source] >= len(files):
                exhausted.add(source)
                continue

            file_path = files[indices[source]]
            indices[source] += 1

            print(f"📦 Procesando archivo {file_path.name} de fuente {source}")

            imported = 0
            try:
                for filename, pgn_io in extract_pgn_files(str(file_path)):
                    while True:
                        game = chess.pgn.read_game(pgn_io)
                        if game is None:
                            break

                        pgn_str = str(game)
                        game_data = extract_features_from_game(pgn_str)
                        game_data["source"] = source

                        print(
                            f"🔍 Procesando partida: {game_data['game_id']}, source: {game_data['source']}, pgn: {game_data['pgn'][:50]}...")

                        if not repo.game_exists(game_data["game_id"]):
                            repo.save_game(game_data)
                            imported += 1
                            total_imported += 1
                        else:
                            print(
                                f"⚠️ Partida ya existe: {game_data['game_id']} - {game_data['pgn'][:50]}...")

                        if imported >= BLOCK_SIZE:
                            break
                    pgn_io.close()
                    if imported >= BLOCK_SIZE:
                        break
            except Exception as e:
                print(
                    f"❌ Error procesando {file_path}: {e}\n{traceback.format_exc()}")

            print(
                f"✅ {imported} partidas importadas de {source} (archivo {file_path.name})")

    repo.commit()
    repo.close()
    print(
        f"🏁 Importación completa. Total partidas importadas: {total_imported}")


if __name__ == "__main__":
    import_balanced_games()
