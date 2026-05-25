# -*- coding: utf-8 -*-
"""Verificar valores SHAP en base de datos"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Conectar a BD
DB_URL = "postgresql://postgres:chess_pass@localhost:5432/chess_trainer_db"
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("\n" + "=" * 80)
print("VERIFICACION DE DATOS SHAP EN BASE DE DATOS")
print("=" * 80 + "\n")

# 1. Contar análisis generados
result = session.execute(text("SELECT COUNT(*) FROM analysis_results")).fetchone()
print(f"[1/3] ANALYSIS_RESULTS:")
print(f"  Total análisis: {result[0]}")

# Ver últimos 5 análisis
result = session.execute(
    text(
        """
    SELECT id, game_id, username, error_level, total_moves, analyzed_at
    FROM analysis_results
    ORDER BY analyzed_at DESC
    LIMIT 5
"""
    )
).fetchall()

if result:
    print(f"\n  Ultimos 5 análisis:")
    for row in result:
        print(
            f"    - ID {row[0]}: {row[1][:32]}... | {row[2]} | {row[3]} | {row[4]} moves | {row[5]}"
        )

# 2. Contar SHAP values guardados
result = session.execute(text("SELECT COUNT(*) FROM move_shap_values")).fetchone()
print(f"\n[2/3] MOVE_SHAP_VALUES:")
print(f"  Total SHAP values: {result[0]}")

# Ver ejemplos
if result[0] > 0:
    result = session.execute(
        text(
            """
        SELECT analysis_id, move_number, feature_name, shap_value, feature_value
        FROM move_shap_values
        LIMIT 10
    """
        )
    ).fetchall()

    print(f"\n  Primeros 10 registros:")
    for row in result:
        print(
            f"    - Analysis {row[0]}, Move {row[1]}: {row[2]}={row[4]:.3f}, SHAP={row[3]:.6f}"
        )

# 3. Contar player feature importance
result = session.execute(
    text("SELECT COUNT(*) FROM player_feature_importance")
).fetchone()
print(f"\n[3/3] PLAYER_FEATURE_IMPORTANCE:")
print(f"  Total registros: {result[0]}")

# Ver top features
if result[0] > 0:
    result = session.execute(
        text(
            """
        SELECT username, feature_name, mean_abs_shap_value, total_samples
        FROM player_feature_importance
        ORDER BY mean_abs_shap_value DESC
        LIMIT 10
    """
        )
    ).fetchall()

    print(f"\n  Top 10 features por importancia:")
    for row in result:
        print(f"    - {row[0]}: {row[1]} | Impact: {row[2]:.6f} | Samples: {row[3]}")

print("\n" + "=" * 80 + "\n")
session.close()
