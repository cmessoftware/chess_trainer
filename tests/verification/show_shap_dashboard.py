# -*- coding: utf-8 -*-
"""Visualización de resultados SHAP - Dashboard interactivo"""
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


def show_shap_results():
    """Mostrar resultados SHAP de forma amigable"""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("\n" + "=" * 100)
    print(" " * 35 + "RESULTADOS SHAP - DASHBOARD")
    print("=" * 100 + "\n")

    # 1. Resumen de análisis
    result = db.execute(
        text(
            """
        SELECT 
            a.id,
            a.game_id,
            a.username,
            a.error_level,
            a.total_moves,
            a.blunder_count,
            a.mistake_count,
            a.inaccuracy_count,
            a.good_move_count,
            a.accuracy_percentage,
            a.analyzed_at,
            COUNT(m.id) as shap_count
        FROM analysis_results a
        LEFT JOIN move_shap_values m ON a.id = m.analysis_id
        GROUP BY a.id
        ORDER BY a.analyzed_at DESC
        LIMIT 10
    """
        )
    ).fetchall()

    print("1. ANÁLISIS RECIENTES (últimos 10)")
    print("-" * 100)
    print(
        f"{'ID':<5} {'Game ID':<35} {'Usuario':<20} {'Nivel':<12} {'Moves':<7} {'Accuracy':<10} {'SHAP':<8}"
    )
    print("-" * 100)

    for row in result:
        game_id_short = row[1][:32] + "..."
        accuracy = f"{row[9]:.1f}%" if row[9] else "N/A"
        print(
            f"{row[0]:<5} {game_id_short:<35} {row[2]:<20} {row[3]:<12} {row[4]:<7} {accuracy:<10} {row[11]:<8}"
        )

    print("\n")

    # 2. Top features globalmente
    print("2. TOP 10 FEATURES MÁS IMPORTANTES (Global)")
    print("-" * 100)

    result = db.execute(
        text(
            """
        SELECT 
            feature_name,
            AVG(ABS(shap_value)) as avg_abs_impact,
            COUNT(*) as count,
            AVG(shap_value) as avg_impact
        FROM move_shap_values
        GROUP BY feature_name
        ORDER BY AVG(ABS(shap_value)) DESC
        LIMIT 10
    """
        )
    ).fetchall()

    print(
        f"{'Feature':<30} {'Impacto Promedio':<18} {'Direccion':<15} {'Muestras':<10}"
    )
    print("-" * 100)

    for row in result:
        direction = "Positivo" if row[3] > 0 else "Negativo"
        print(f"{row[0]:<30} {row[1]:<18.4f} {direction:<15} {row[2]:<10}")

    print("\n")

    # 3. Ejemplo detallado de una partida
    print("3. EJEMPLO DETALLADO - Primera partida analizada")
    print("-" * 100)

    # Obtener primer análisis
    first_analysis = db.execute(
        text(
            """
        SELECT id, game_id, username, total_moves
        FROM analysis_results
        ORDER BY analyzed_at DESC
        LIMIT 1
    """
        )
    ).fetchone()

    if first_analysis:
        analysis_id = first_analysis[0]
        print(f"Análisis ID: {analysis_id}")
        print(f"Game ID: {first_analysis[1][:32]}...")
        print(f"Usuario: {first_analysis[2]}")
        print(f"Total movimientos: {first_analysis[3]}")
        print()

        # Movimiento 1 - Top 5 features
        print("   Movimiento 1 - Top 5 features con mayor impacto:")
        print("   " + "-" * 90)

        shap_move1 = db.execute(
            text(
                """
            SELECT 
                feature_name,
                shap_value,
                feature_value
            FROM move_shap_values
            WHERE analysis_id = :aid AND move_number = 1
            ORDER BY ABS(shap_value) DESC
            LIMIT 5
        """
            ),
            {"aid": analysis_id},
        ).fetchall()

        for i, row in enumerate(shap_move1, 1):
            impact_dir = "aumenta" if row[1] > 0 else "reduce"
            print(
                f"   {i}. {row[0]:<30} Impacto: {row[1]:>8.4f}  ({impact_dir} prediccion)"
            )
            print(f"      Valor de la feature: {row[2]:.2f}")

        print()

        # Movimiento con mayor impacto SHAP
        print("   Movimiento con mayor impacto total SHAP:")
        print("   " + "-" * 90)

        max_impact_move = db.execute(
            text(
                """
            SELECT 
                move_number,
                SUM(ABS(shap_value)) as total_impact,
                COUNT(*) as features_count
            FROM move_shap_values
            WHERE analysis_id = :aid
            GROUP BY move_number
            ORDER BY SUM(ABS(shap_value)) DESC
            LIMIT 1
        """
            ),
            {"aid": analysis_id},
        ).fetchone()

        if max_impact_move:
            print(f"   Movimiento #{max_impact_move[0]}")
            print(f"   Impacto total: {max_impact_move[1]:.4f}")
            print(f"   Features analizadas: {max_impact_move[2]}")

            # Top 3 features de ese movimiento
            print(f"\n   Top 3 features del movimiento #{max_impact_move[0]}:")

            top_features = db.execute(
                text(
                    """
                SELECT feature_name, shap_value, feature_value
                FROM move_shap_values
                WHERE analysis_id = :aid AND move_number = :move
                ORDER BY ABS(shap_value) DESC
                LIMIT 3
            """
                ),
                {"aid": analysis_id, "move": max_impact_move[0]},
            ).fetchall()

            for i, feat in enumerate(top_features, 1):
                print(f"      {i}. {feat[0]}: {feat[1]:.4f} (valor={feat[2]:.2f})")

    print("\n")

    # 4. Estadísticas por usuario
    print("4. ESTADÍSTICAS POR USUARIO")
    print("-" * 100)

    user_stats = db.execute(
        text(
            """
        SELECT 
            username,
            COUNT(DISTINCT a.id) as total_analyses,
            AVG(accuracy_percentage) as avg_accuracy,
            SUM(total_moves) as total_moves_analyzed
        FROM analysis_results a
        GROUP BY username
        ORDER BY COUNT(DISTINCT a.id) DESC
    """
        )
    ).fetchall()

    print(
        f"{'Usuario':<25} {'Análisis':<12} {'Accuracy Prom':<18} {'Moves Totales':<15}"
    )
    print("-" * 100)

    for row in user_stats:
        accuracy = f"{row[2]:.1f}%" if row[2] else "N/A"
        print(f"{row[0]:<25} {row[1]:<12} {accuracy:<18} {row[3]:<15}")

    print("\n" + "=" * 100)
    print("\nPara consultar via API REST:")
    print("  GET  http://localhost:8000/api/analysis/game/{game_id}/shap?move_number=1")
    print("  GET  http://localhost:8000/api/analysis/global-feature-importance")
    print('  POST http://localhost:8000/api/analysis/run  (body: {"game_id": "..."})')
    print("\n" + "=" * 100 + "\n")

    db.close()


if __name__ == "__main__":
    show_shap_results()
