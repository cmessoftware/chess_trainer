"""
Script para importar un PGN personal del usuario
Guarda las partidas con el usuario que las importó
"""

import os
import sys
import uuid
from pathlib import Path
import chess.pgn
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from db.repository.games_repository import GamesRepository
from modules.pgn_batch_loader import extract_features_from_game

load_dotenv()


def import_personal_pgn(file_path: str, username: str, source: str = "personal"):
    """
    Importa un archivo PGN personal marcándolo con el usuario

    Args:
        file_path: Ruta al archivo PGN
        username: Usuario que importa
        source: Fuente de las partidas (default: "personal")

    Returns:
        dict: {"imported": int, "skipped": int, "batch_id": str}
    """
    repo = GamesRepository()
    imported = 0
    skipped = 0

    # Generar batch_id único para este archivo
    batch_id = str(uuid.uuid4())

    print(f"📦 Importando {file_path} para usuario {username}")
    print(f"📦 Batch ID: {batch_id}")

    try:
        with open(file_path) as pgn_file:
            while True:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break

                try:
                    # Extraer features del juego
                    pgn_str = str(game)
                    game_data = extract_features_from_game(pgn_str)
                    game_data["source"] = source
                    game_data["imported_by"] = username  # Marcar usuario
                    game_data["import_batch_id"] = batch_id  # Agrupar por batch

                    # Verificar si ya existe
                    if not repo.game_exists(game_data["game_id"]):
                        repo.save_game(game_data)
                        repo.commit()  # Commit individual
                        imported += 1
                        print(f"✅ Importada: {game_data['game_id']}")
                    else:
                        skipped += 1
                        print(f"⏭️  Ya existe: {game_data['game_id']}")

                except Exception as e:
                    # Si falla una partida, hacer rollback de esa sola y continuar
                    repo.rollback()
                    skipped += 1
                    print(f"⚠️ Error en partida (skip): {str(e)[:100]}")
                    continue

        print(f"🏁 Importación completa: {imported} importadas, {skipped} omitidas")
        print(f"📦 Batch ID: {batch_id}")
        return {"imported": imported, "skipped": skipped, "batch_id": batch_id}

    except Exception as e:
        repo.rollback()
        print(f"❌ Error: {e}")
        raise e
    finally:
        repo.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python import_personal_pgn.py <archivo_pgn> <username> [source]")
        sys.exit(1)

    file_path = sys.argv[1]
    username = sys.argv[2]
    source = sys.argv[3] if len(sys.argv) > 3 else "personal"

    import_personal_pgn(file_path, username, source)
