# -*- coding: utf-8 -*-
"""Eliminar análisis sin SHAP values para forzar nueva ejecución"""
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


def cleanup_empty_analyses():
    """Eliminar análisis sin SHAP values"""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("\n" + "=" * 80)
    print("CLEANUP DE ANALISIS SIN SHAP VALUES")
    print("=" * 80 + "\n")

    # Identificar análisis sin SHAP
    result = db.execute(
        text(
            """
        SELECT a.id, a.game_id, a.username, a.analyzed_at
        FROM analysis_results a
        LEFT JOIN move_shap_values m ON a.id = m.analysis_id
        WHERE m.analysis_id IS NULL
        ORDER BY a.id
    """
        )
    ).fetchall()

    if not result:
        print("[INFO] No hay análisis sin SHAP values")
        return

    print(f"[INFO] Encontrados {len(result)} análisis sin SHAP values:")
    for row in result:
        print(
            f"   - ID={row[0]}, game_id={row[1][:32]}..., user={row[2]}, fecha={row[3]}"
        )

    print(f"\n[ACTION] Eliminando {len(result)} análisis...")

    # Eliminar
    db.execute(
        text(
            """
        DELETE FROM analysis_results
        WHERE id IN (
            SELECT a.id
            FROM analysis_results a
            LEFT JOIN move_shap_values m ON a.id = m.analysis_id
            WHERE m.analysis_id IS NULL
        )
    """
        )
    )

    db.commit()
    print(f"[OK] {len(result)} análisis eliminados\n")

    # Verificar
    result = db.execute(
        text(
            """
        SELECT COUNT(*) FROM analysis_results
    """
        )
    ).fetchone()

    print(f"[INFO] Análisis restantes: {result[0]}")
    print("=" * 80 + "\n")

    db.close()


if __name__ == "__main__":
    cleanup_empty_analyses()
