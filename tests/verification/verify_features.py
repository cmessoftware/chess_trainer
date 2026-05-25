# -*- coding: utf-8 -*-
"""Verificar features guardadas - Version sin emojis"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path
import dotenv

# Cargar variables de entorno
dotenv.load_dotenv()

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
if not DB_URL:
    print("[ERROR] CHESS_TRAINER_DB_URL no encontrada")
    sys.exit(1)

# Game IDs de prueba
TEST_GAME_IDS = [
    "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3",
    "f195fb3ea8454c9f646eacabe04b4e46990de731be39d1f378b628c0c723f313",
    "c8392462c80815c9c39026a1f6bf4b9d363a6cbc78bc0e12d6db8676e6dfae4c",
    "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb",
]


def verify():
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("\n" + "=" * 80)
    print("VERIFICACION DE FEATURES GUARDADAS")
    print("=" * 80 + "\n")

    # 1. Estado global
    result = session.execute(
        text(
            """
        SELECT 
            COUNT(DISTINCT game_id) as total_games,
            COUNT(DISTINCT CASE WHEN feature_count > 0 THEN game_id END) as games_with_features,
            COUNT(DISTINCT CASE WHEN feature_count = 0 THEN game_id END) as games_without_features
        FROM (
            SELECT 
                g.game_id,
                COUNT(f.game_id) as feature_count
            FROM games g
            LEFT JOIN features f ON g.game_id = f.game_id
            GROUP BY g.game_id
        ) subq
    """
        )
    ).fetchone()

    print("RESUMEN GLOBAL:")
    print(f"  Total partidas: {result[0]:,}")
    print(f"  Con features: {result[1]:,}  ({result[1]/result[0]*100:.2f}%)")
    print(f"  Sin features: {result[2]:,}  ({result[2]/result[0]*100:.2f}%)")
    print()

    # 2. Verificar game_ids de prueba
    print("GAME IDS DE PRUEBA:")
    print("-" * 80)

    for i, gid in enumerate(TEST_GAME_IDS, 1):
        result = session.execute(
            text(
                """
            SELECT COUNT(*) FROM features WHERE game_id = :gid
        """
            ),
            {"gid": gid},
        ).fetchone()

        feature_count = result[0]
        status = "[OK]" if feature_count > 0 else "[FAIL]"

        print(f"{status} [{i}/4] {gid[:32]}... -> {feature_count} features")

    print("\n" + "=" * 80 + "\n")
    session.close()


if __name__ == "__main__":
    verify()
