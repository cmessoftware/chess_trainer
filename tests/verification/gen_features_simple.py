# -*- coding: utf-8 -*-
"""
Script para generar features para game_ids especificos.
"""
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configurar encoding para Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import dotenv

dotenv.load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")

# Game IDs a procesar
TARGET_GAME_IDS = [
    "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3",
    "f195fb3ea8454c9f646eacabe04b4e46990de731be39d1f378b628c0c723f313",
    "c8392462c80815c9c39026a1f6bf4b9d363a6cbc78bc0e12d6db8676e6dfae4c",
    "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb",
]


def generate_features_for_games(game_ids):
    """Generar features para game_ids especificos"""
    from modules.features_generator import generate_features_from_game
    from modules.pgn_utils import pgn_str_to_game
    from db.models.games import Games
    from db.models.features import Features

    # Configurar Stockfish
    stockfish_path = Path(__file__).parent / "bin" / "stockfish.exe"
    if stockfish_path.exists():
        os.environ["STOCKFISH_PATH"] = str(stockfish_path)
        print(f"[OK] Stockfish configurado: {stockfish_path}")
    else:
        print(f"[WARN] Stockfish no encontrado en: {stockfish_path}")

    # Conectar a BD
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)

    print("=" * 80)
    print(f"GENERANDO FEATURES PARA {len(game_ids)} PARTIDAS")
    print("=" * 80)

    successful = 0
    failed = 0

    for idx, game_id in enumerate(game_ids, 1):
        print(f"\n[{idx}/{len(game_ids)}] Procesando: {game_id[:16]}...")

        session = Session()

        try:
            # Obtener PGN de la BD
            game_record = session.query(Games).filter_by(game_id=game_id).first()

            if not game_record:
                print(f"   [ERROR] Game ID no encontrado en la base de datos")
                failed += 1
                session.close()
                continue

            if not game_record.pgn:
                print(f"   [ERROR] Sin PGN en el registro")
                failed += 1
                session.close()
                continue

            # Verificar si ya tiene features
            existing_features = (
                session.query(Features).filter_by(game_id=game_id).count()
            )
            if existing_features > 0:
                print(f"   [SKIP] Ya tiene {existing_features} features")
                session.close()
                continue

            # Parsear PGN
            game = pgn_str_to_game(game_record.pgn)
            if not game:
                print(f"   [ERROR] Error parseando PGN")
                failed += 1
                session.close()
                continue

            # Generar features
            print(f"   [INFO] Generando features...")
            features = generate_features_from_game(game, game_id)

            if not features or len(features) == 0:
                print(f"   [ERROR] No se generaron features")
                failed += 1
                session.close()
                continue

            # Guardar en BD
            print(f"   [INFO] Guardando {len(features)} features...")

            # Bulk insert usando la sesion directamente
            feature_objects = [Features(**f) for f in features]
            session.bulk_save_objects(feature_objects)
            session.commit()

            print(f"   [OK] {len(features)} features guardadas exitosamente")
            successful += 1

        except Exception as e:
            print(f"   [ERROR] {e}")
            import traceback

            traceback.print_exc()
            session.rollback()
            failed += 1
        finally:
            session.close()

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Exitosas: {successful}")
    print(f"Fallidas: {failed}")
    print(f"Total procesadas: {len(game_ids)}")

    return successful, failed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generar features para game_ids especificos"
    )
    parser.add_argument("--game-ids", nargs="+", help="Lista de game_ids a procesar")
    args = parser.parse_args()

    # Usar game_ids de argumentos o los predefinidos
    game_ids_to_process = args.game_ids if args.game_ids else TARGET_GAME_IDS

    print(f"\nProcesando {len(game_ids_to_process)} game_ids...")
    for gid in game_ids_to_process:
        print(f"   - {gid[:32]}...")

    successful, failed = generate_features_for_games(game_ids_to_process)

    if successful > 0:
        print(
            f"\n[SUCCESS] Proceso completado. {successful} partidas con features generadas."
        )
    else:
        print(f"\n[WARNING] No se generaron features.")

    sys.exit(0 if failed == 0 else 1)
