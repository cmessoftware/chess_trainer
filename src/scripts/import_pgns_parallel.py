import os
import sys
import traceback
from pathlib import Path
import chess
from dotenv import load_dotenv

# Add src to path for local imports when running from src/scripts
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.pgn_batch_loader import extract_pgn_files, extract_features_from_game
from db.repository.games_repository import GamesRepository
from sqlalchemy.orm import sessionmaker

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")
DB_PATH_URL = os.environ.get("CHESS_TRAINER_DB_URL")


def resolve_pgn_base_dir() -> Path:
    raw_pgn_path = os.environ.get("PGN_PATH")
    candidates: list[Path] = []

    if raw_pgn_path:
        configured = Path(raw_pgn_path).expanduser()
        if configured.is_absolute():
            candidates.append(configured)
        else:
            candidates.append((REPO_ROOT / configured).resolve())
            candidates.append((Path.cwd() / configured).resolve())

            parts = configured.parts
            if parts and parts[0].lower() == "src":
                candidates.append((REPO_ROOT.joinpath(*parts[1:])).resolve())
    else:
        candidates.append((REPO_ROOT / "data" / "games").resolve())
        candidates.append((REPO_ROOT / "src" / "data" / "games").resolve())

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


BASE_DIR = resolve_pgn_base_dir()
SOURCES = ["personal", "novice", "elite", "stockfish", "fide"]
BLOCK_SIZE = 1000

# Recoge todos los archivos válidos por fuente


def collect_pgn_files_by_source():
    pgn_dict = {}
    for source in SOURCES:
        source_path = BASE_DIR / source
        if not source_path.exists():
            print(f"[WARNING] No se encontró la carpeta de la fuente: {source_path}")
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
            games_batch = []
            
            try:
                for filename, pgn_io in extract_pgn_files(str(file_path)):
                    while True:
                        try:
                            game = chess.pgn.read_game(pgn_io)
                            if game is None:
                                break

                            pgn_str = str(game)
                            game_data = extract_features_from_game(pgn_str)
                            game_data["source"] = source

                            print(
                                f"[DISCOVER] Procesando partida: {game_data['game_id']}, source: {game_data['source']}, pgn: {game_data['pgn'][:50]}...")

                            if not repo.game_exists(game_data["game_id"]):
                                games_batch.append(game_data)
                                imported += 1
                                total_imported += 1
                                
                                # Batch insert every 100 games
                                if len(games_batch) >= 100:
                                    try:
                                        repo.save_games_batch(games_batch)
                                        games_batch = []
                                    except Exception as batch_error:
                                        print(f"[ERROR] Error guardando lote: {batch_error}")
                                        repo.rollback()
                                        games_batch = []
                            else:
                                print(
                                    f"[WARNING] Partida ya existe: {game_data['game_id']} - {game_data['pgn'][:50]}...")

                            if imported >= BLOCK_SIZE:
                                break
                        except Exception as game_error:
                            print(f"[ERROR] Error procesando partida individual: {game_error}")
                            continue
                            
                    pgn_io.close()
                    if imported >= BLOCK_SIZE:
                        break
                        
                # Save any remaining games in the batch
                if games_batch:
                    try:
                        repo.save_games_batch(games_batch)
                    except Exception as batch_error:
                        print(f"[ERROR] Error guardando lote final: {batch_error}")
                        repo.rollback()
                        
            except Exception as e:
                print(
                    f"[ERROR] Error procesando {file_path}: {e}\n{traceback.format_exc()}")
                # Roll back the current transaction
                repo.rollback()

            print(
                f"[SUCCESS] {imported} partidas importadas de {source} (archivo {file_path.name})")

    repo.close()
    print(
        f"🏁 Importación completa. Total partidas importadas: {total_imported}")


if __name__ == "__main__":
    import_balanced_games()

