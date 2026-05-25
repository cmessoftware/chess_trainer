# -*- coding: utf-8 -*-
"""Prueba directa del AnalysisService para debugging de SHAP persistence"""
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
from api.services.analysis_service import AnalysisService

# DB URL
DB_URL = "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db"

# Game ID de prueba (sabemos que tiene features)
TEST_GAME_ID = "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3"


def test_analysis_service():
    """Ejecutar análisis directamente y capturar toda la salida"""
    print("\n" + "=" * 80)
    print("PRUEBA DIRECTA DE ANALYSIS SERVICE")
    print("=" * 80 + "\n")

    # Username único para forzar nuevo análisis
    import time

    test_username = f"test_user_debug_{int(time.time())}"

    # Conectar a BD
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Verificar features
    result = db.execute(
        text(
            """
        SELECT COUNT(*) FROM features WHERE game_id = :gid
    """
        ),
        {"gid": TEST_GAME_ID},
    ).fetchone()

    print(f"[INFO] Features para game_id: {result[0]}")

    if result[0] == 0:
        print("[ERROR] No hay features para este game_id")
        return

    # Instanciar servicio
    print("\n[1/3] Instanciando AnalysisService...")
    service = AnalysisService()
    print("   [OK] Servicio instanciado\n")

    # Ejecutar análisis
    print(f"[2/3] Ejecutando análisis para game_id: {TEST_GAME_ID[:32]}...")
    print(f"      Usuario: {test_username}")
    print("-" * 80)

    try:
        analysis_id = service.analyze_game(
            db=db, game_id=TEST_GAME_ID, username=test_username
        )

        print("-" * 80)
        print(f"\n[OK] Análisis completado: analysis_id={analysis_id}\n")

    except Exception as e:
        print(f"\n[ERROR] Análisis falló: {e}\n")
        import traceback

        traceback.print_exc()
        return

    # Verificar resultados en BD
    print("[3/3] Verificando persistencia en BD...")
    print("-" * 80)

    # analysis_results
    result = db.execute(
        text(
            """
        SELECT id, game_id, username, error_level, total_moves, 
               blunder_count, mistake_count, inaccuracy_count, good_move_count
        FROM analysis_results
        WHERE id = :aid
    """
        ),
        {"aid": analysis_id},
    ).fetchone()

    if result:
        print("\n[OK] analysis_results:")
        print(f"   - ID: {result[0]}")
        print(f"   - game_id: {result[1][:32]}...")
        print(f"   - username: {result[2]}")
        print(f"   - error_level: {result[3]}")
        print(f"   - total_moves: {result[4]}")
        print(
            f"   - blunders: {result[5]}, mistakes: {result[6]}, inaccuracies: {result[7]}, good: {result[8]}"
        )
    else:
        print("[FAIL] No se encontró el análisis en analysis_results")

    # move_shap_values
    result = db.execute(
        text(
            """
        SELECT COUNT(*) FROM move_shap_values WHERE analysis_id = :aid
    """
        ),
        {"aid": analysis_id},
    ).fetchone()

    shap_count = result[0]
    print(
        f"\n{'[OK]' if shap_count > 0 else '[FAIL]'} move_shap_values: {shap_count} registros"
    )

    if shap_count > 0:
        # Mostrar algunos ejemplos
        examples = db.execute(
            text(
                """
            SELECT move_number, feature_name, shap_value, feature_value
            FROM move_shap_values
            WHERE analysis_id = :aid
            ORDER BY move_number, ABS(shap_value) DESC
            LIMIT 5
        """
            ),
            {"aid": analysis_id},
        ).fetchall()

        print("\n   Ejemplos de SHAP values:")
        for ex in examples:
            print(
                f"   - Move {ex[0]}: {ex[1]} = {ex[2]:.4f} (feature_value={ex[3]:.2f})"
            )

    # player_feature_importance
    result = db.execute(
        text(
            """
        SELECT COUNT(*) FROM player_feature_importance 
        WHERE username = :user
    """
        ),
        {"user": test_username},
    ).fetchone()

    importance_count = result[0]
    print(
        f"\n{'[OK]' if importance_count > 0 else '[FAIL]'} player_feature_importance: {importance_count} registros"
    )

    if importance_count > 0:
        # Top features
        top_features = db.execute(
            text(
                """
            SELECT feature_name, mean_abs_shap_value, total_samples
            FROM player_feature_importance
            WHERE username = :user
            ORDER BY mean_abs_shap_value DESC
            LIMIT 5
        """
            ),
            {"user": test_username},
        ).fetchall()

        print("\n   Top features por importancia:")
        for feat in top_features:
            print(f"   - {feat[0]}: {feat[1]:.4f} (n={feat[2]})")

    print("\n" + "=" * 80 + "\n")
    db.close()


if __name__ == "__main__":
    test_analysis_service()
