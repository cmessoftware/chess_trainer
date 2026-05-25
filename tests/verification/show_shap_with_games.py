# -*- coding: utf-8 -*-
"""Consultar SHAP values con información de la partida asociada"""
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


def show_shap_with_games():
    """Mostrar SHAP values con información completa de la partida"""
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    db = Session()

    print("\n" + "=" * 120)
    print(" " * 35 + "SHAP VALUES CON INFORMACIÓN DE PARTIDA")
    print("=" * 120 + "\n")

    # 1. Estructura de las tablas
    print("1. ESTRUCTURA DE RELACIONES:")
    print("-" * 120)
    print(
        """
    move_shap_values
    ├── analysis_id (FK) ──→ analysis_results.id
    │                        ├── game_id
    │                        ├── username  
    │                        ├── error_level
    │                        └── analyzed_at
    ├── move_number
    ├── feature_name
    ├── shap_value
    └── feature_value
    """
    )
    print()

    # 2. Consulta con JOIN
    print("2. CONSULTA SQL CON JOIN:")
    print("-" * 120)

    query = """
    SELECT 
        m.id as shap_id,
        a.game_id,
        a.username,
        a.error_level,
        m.move_number,
        m.feature_name,
        m.shap_value,
        m.feature_value,
        a.analyzed_at
    FROM move_shap_values m
    INNER JOIN analysis_results a ON m.analysis_id = a.id
    ORDER BY a.id, m.move_number, ABS(m.shap_value) DESC
    LIMIT 20
    """

    print(query)
    print()

    # 3. Ejecutar consulta
    print("3. PRIMEROS 20 REGISTROS:")
    print("-" * 120)

    result = db.execute(text(query)).fetchall()

    print(
        f"{'SHAP ID':<10} {'Game ID':<35} {'User':<15} {'Move':<6} {'Feature':<25} {'Impact':<10}"
    )
    print("-" * 120)

    for row in result:
        game_id_short = row[1][:32] + "..."
        print(
            f"{row[0]:<10} {game_id_short:<35} {row[2]:<15} {row[4]:<6} {row[5]:<25} {row[6]:<10.4f}"
        )

    print("\n")

    # 4. Resumen por partida
    print("4. RESUMEN: SHAP VALUES AGRUPADOS POR PARTIDA:")
    print("-" * 120)

    summary_query = """
    SELECT 
        a.game_id,
        a.username,
        a.error_level,
        COUNT(m.id) as total_shap_values,
        COUNT(DISTINCT m.move_number) as total_moves,
        AVG(ABS(m.shap_value)) as avg_abs_impact
    FROM analysis_results a
    LEFT JOIN move_shap_values m ON a.id = m.analysis_id
    GROUP BY a.game_id, a.username, a.error_level
    ORDER BY COUNT(m.id) DESC
    """

    summary = db.execute(text(summary_query)).fetchall()

    print(
        f"{'Game ID':<35} {'Usuario':<20} {'Nivel':<12} {'SHAP Values':<15} {'Moves':<8} {'Avg Impact':<12}"
    )
    print("-" * 120)

    for row in summary:
        game_id_short = row[0][:32] + "..."
        print(
            f"{game_id_short:<35} {row[1]:<20} {row[2]:<12} {row[3]:<15} {row[4]:<8} {row[5]:<12.4f}"
        )

    print("\n")

    # 5. Ejemplo detallado de una partida completa
    print("5. EJEMPLO DETALLADO - PARTIDA COMPLETA CON SUS SHAP VALUES:")
    print("-" * 120)

    # Tomar la primera partida
    first_game = db.execute(
        text(
            """
        SELECT DISTINCT a.game_id, a.id as analysis_id, a.username, a.total_moves
        FROM analysis_results a
        INNER JOIN move_shap_values m ON a.id = m.analysis_id
        ORDER BY a.id DESC
        LIMIT 1
    """
        )
    ).fetchone()

    if first_game:
        print(f"Game ID: {first_game[0]}")
        print(f"Analysis ID: {first_game[1]}")
        print(f"Usuario: {first_game[2]}")
        print(f"Total movimientos: {first_game[3]}")
        print()

        # Top 5 moves con mayor impacto SHAP
        print("   Top 5 movimientos con mayor impacto SHAP total:")
        print("   " + "-" * 110)

        top_moves = db.execute(
            text(
                """
            SELECT 
                m.move_number,
                COUNT(*) as features_count,
                SUM(ABS(m.shap_value)) as total_impact,
                a.game_id
            FROM move_shap_values m
            INNER JOIN analysis_results a ON m.analysis_id = a.id
            WHERE a.game_id = :gid
            GROUP BY m.move_number, a.game_id
            ORDER BY SUM(ABS(m.shap_value)) DESC
            LIMIT 5
        """
            ),
            {"gid": first_game[0]},
        ).fetchall()

        for i, move in enumerate(top_moves, 1):
            print(
                f"   {i}. Movimiento #{move[0]}: Impacto total = {move[2]:.4f} ({move[1]} features)"
            )

        print()

        # Detalles del primer movimiento
        print(f"   Detalle del movimiento #{top_moves[0][0]} (mayor impacto):")
        print("   " + "-" * 110)

        move_details = db.execute(
            text(
                """
            SELECT 
                m.feature_name,
                m.shap_value,
                m.feature_value,
                a.game_id
            FROM move_shap_values m
            INNER JOIN analysis_results a ON m.analysis_id = a.id
            WHERE a.game_id = :gid AND m.move_number = :move
            ORDER BY ABS(m.shap_value) DESC
        """
            ),
            {"gid": first_game[0], "move": top_moves[0][0]},
        ).fetchall()

        print(
            f"   {'Feature':<30} {'SHAP Value':<15} {'Feature Value':<15} {'Game ID (parcial)':<25}"
        )
        print("   " + "-" * 110)
        for detail in move_details:
            game_short = detail[3][:20] + "..."
            print(
                f"   {detail[0]:<30} {detail[1]:<15.4f} {detail[2]:<15.2f} {game_short:<25}"
            )

    print("\n")

    # 6. Query recomendado para uso general
    print("6. QUERY RECOMENDADO PARA CONSULTAR SHAP VALUES CON GAME_ID:")
    print("-" * 120)
    print(
        """
SELECT 
    a.game_id,
    a.username,
    m.move_number,
    m.feature_name,
    m.shap_value,
    m.feature_value,
    a.error_level,
    a.analyzed_at
FROM move_shap_values m
INNER JOIN analysis_results a ON m.analysis_id = a.id
WHERE a.game_id = 'TU_GAME_ID_AQUI'
ORDER BY m.move_number, ABS(m.shap_value) DESC;
    """
    )

    print("\n" + "=" * 120 + "\n")

    db.close()


if __name__ == "__main__":
    show_shap_with_games()
