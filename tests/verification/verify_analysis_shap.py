# -*- coding: utf-8 -*-
"""Verificar análisis y SHAP values en BD"""
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configurar encoding para Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# DB URL
DB_URL = "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db"

# Game IDs de prueba
TEST_GAME_IDS = [
    "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3",
    "f195fb3ea8454c9f646eacabe04b4e46990de731be39d1f378b628c0c723f313",
    "c8392462c80815c9c39026a1f6bf4b9d363a6cbc78bc0e12d6db8676e6dfae4c",
    "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb",
]


def verify_analysis_shap():
    """Verificar estado de análisis y SHAP values"""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("\n" + "=" * 80)
    print("VERIFICACION DE ANALISIS Y SHAP VALUES")
    print("=" * 80 + "\n")

    # 1. Resumen global
    result = db.execute(
        text(
            """
        SELECT 
            COUNT(DISTINCT a.id) as total_analyses,
            COUNT(DISTINCT CASE WHEN shap_count > 0 THEN a.id END) as with_shap,
            COUNT(DISTINCT CASE WHEN shap_count = 0 THEN a.id END) as without_shap
        FROM analysis_results a
        LEFT JOIN (
            SELECT analysis_id, COUNT(*) as shap_count
            FROM move_shap_values
            GROUP BY analysis_id
        ) s ON a.id = s.analysis_id
    """
        )
    ).fetchone()

    print("RESUMEN GLOBAL:")
    print(f"  Total análisis: {result[0]}")
    print(f"  Con SHAP values: {result[1]}")
    print(f"  Sin SHAP values: {result[2]}")
    print()

    # 2. Detalles por game_id de prueba
    print("GAME IDS DE PRUEBA:")
    print("-" * 80)

    for i, gid in enumerate(TEST_GAME_IDS, 1):
        print(f"\n[{i}/4] {gid[:32]}...")

        # Análisis para este game_id
        analyses = db.execute(
            text(
                """
            SELECT 
                a.id, 
                a.username, 
                a.error_level,
                a.total_moves,
                a.analyzed_at,
                COALESCE(s.shap_count, 0) as shap_count
            FROM analysis_results a
            LEFT JOIN (
                SELECT analysis_id, COUNT(*) as shap_count
                FROM move_shap_values
                GROUP BY analysis_id
            ) s ON a.id = s.analysis_id
            WHERE a.game_id = :gid
            ORDER BY a.analyzed_at DESC
            LIMIT 3
        """
            ),
            {"gid": gid},
        ).fetchall()

        if not analyses:
            print("   [WARN] Sin análisis en BD")
            continue

        print(f"   Total análisis: {len(analyses)}")
        for analysis in analyses:
            status = "[OK]" if analysis[5] > 0 else "[EMPTY]"
            print(
                f"   {status} ID={analysis[0]}, user={analysis[1]}, moves={analysis[3]}, shap_values={analysis[5]}"
            )

    print("\n" + "=" * 80 + "\n")
    db.close()


if __name__ == "__main__":
    verify_analysis_shap()
