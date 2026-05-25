#!/usr/bin/env python
"""
Script para generar features para game_ids específicos.
"""
import os
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

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
    """Generar features para game_ids específicos"""
    from modules.features_generator import generate_features_from_game
    from modules.pgn_utils import pgn_str_to_game
    from db.repository.features_repository import FeaturesRepository
    from db.repository.games_repository import GamesRepository

    # Configurar Stockfish
    stockfish_path = Path(__file__).parent / "bin" / "stockfish.exe"
    if stockfish_path.exists():
        os.environ["STOCKFISH_PATH"] = str(stockfish_path)
        print(f"✅ Stockfish configurado: {stockfish_path}")
    else:
        print(f"⚠️  Stockfish no encontrado en: {stockfish_path}")

    # Conectar a BD
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)

    games_repo = GamesRepository(Session)
    features_repo = FeaturesRepository(Session)
    print("=" * 80)

    successful = 0
    failed = 0

    for idx, game_id in enumerate(game_ids, 1):
        print(f"\n[{idx}/{len(game_ids)}] Procesando: {game_id[:16]}...")

        try:
            # Obtener PGN de la BD
            game_record = games_repo.get_game_by_id(game_id)

            if not game_record:
                print(f"   ❌ Game ID no encontrado en la base de datos")
                failed += 1
                continue

            if not game_record.pgn:
                print(f"   ❌ Sin PGN en el registro")
                failed += 1
                continue

            # Verificar si ya tiene features
            existing_features = features_repo.get_by_game_id(game_id)
            if existing_features:
                print(f"   ⏭️  Ya tiene {len(existing_features)} features - saltando")
                continue

            # Parsear PGN
            game = pgn_str_to_game(game_record.pgn)
            if not game:
                print(f"   ❌ Error parseando PGN")
                failed += 1
                continue

            # Generar features
            print(f"   🔬 Generando features...")
            features = generate_features_from_game(game, game_id)

            if not features:
                print(f"   ❌ No se generaron features")
                failed += 1
                continue

            # Guardar en BD
            print(f"   💾 Guardando {len(features)} features...")
            features_repo.bulk_insert(features)
            session.commit()

            print(f"   ✅ {len(features)} features guardadas exitosamente")
            successful += 1

        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback

            traceback.print_exc()
            session.rollback()
            failed += 1

    session.close()

    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN")
    print("=" * 80)
    print(f"✅ Exitosas: {successful}")
    print(f"❌ Fallidas: {failed}")
    print(f"📦 Total procesadas: {len(game_ids)}")

    return successful, failed


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generar features para game_ids específicos"
    )
    parser.add_argument("--game-ids", nargs="+", help="Lista de game_ids a procesar")
    args = parser.parse_args()

    # Usar game_ids de argumentos o los predefinidos
    game_ids_to_process = args.game_ids if args.game_ids else TARGET_GAME_IDS

    print(f"\n🎯 Procesando {len(game_ids_to_process)} game_ids...")
    for gid in game_ids_to_process:
        print(f"   - {gid[:32]}...")

    successful, failed = generate_features_for_games(game_ids_to_process)

    if successful > 0:
        print(f"\n✅ Proceso completado. {successful} partidas con features generadas.")
    else:
        print(f"\n⚠️  No se generaron features.")

    sys.exit(0 if failed == 0 else 1)
