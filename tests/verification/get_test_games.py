#!/usr/bin/env python
"""
Script para obtener game_ids con features y análisis de la base de datos.
"""
import psycopg2
import os

# Configuración de la base de datos
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "chess_trainer_db",
    "user": "chess",
    "password": "chess_pass",
}


def get_analyzed_games():
    """Obtener game_ids que ya tienen análisis"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Obtener análisis existentes
    cur.execute(
        """
        SELECT id, game_id, username, error_level, total_moves, blunder_count, mistake_count
        FROM analysis_results
        LIMIT 5
    """
    )

    results = cur.fetchall()

    print("=" * 80)
    print("📊 ANÁLISIS EXISTENTES EN LA BASE DE DATOS")
    print("=" * 80)

    if results:
        for row in results:
            (
                analysis_id,
                game_id,
                username,
                error_level,
                total_moves,
                blunders,
                mistakes,
            ) = row
            print(f"\n✅ Analysis ID: {analysis_id}")
            print(f"   Game ID: {game_id}")
            print(f"   Usuario: {username}")
            print(f"   Error Level: {error_level}")
            print(f"   Total Moves: {total_moves}")
            print(f"   Blunders: {blunders}, Mistakes: {mistakes}")
    else:
        print("\n⚠️  No hay análisis en la base de datos")

    cur.close()
    conn.close()

    return results


def get_games_with_features():
    """Obtener game_ids que tienen features calculadas"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Obtener games con features
    cur.execute(
        """
        SELECT DISTINCT game_id
        FROM features
        LIMIT 5
    """
    )

    results = cur.fetchall()

    print("\n" + "=" * 80)
    print("🎯 PARTIDAS CON FEATURES CALCULADAS")
    print("=" * 80)

    if results:
        for idx, (game_id,) in enumerate(results, 1):
            print(f"{idx}. {game_id}")
    else:
        print("\n⚠️  No hay partidas con features")

    cur.close()
    conn.close()

    return [r[0] for r in results]


def main():
    try:
        print("\n🔍 CONSULTANDO BASE DE DATOS CHESS TRAINER")
        print("=" * 80)

        # Obtener análisis existentes
        analyzed_games = get_analyzed_games()

        # Obtener partidas con features
        games_with_features = get_games_with_features()

        # Resumen
        print("\n" + "=" * 80)
        print("📋 RESUMEN")
        print("=" * 80)
        print(f"Análisis existentes: {len(analyzed_games)}")
        print(f"Partidas con features: {len(games_with_features)}")

        if analyzed_games:
            print(f"\n💡 Game ID recomendado para pruebas:")
            print(f"   {analyzed_games[0][1]}")
        elif games_with_features:
            print(f"\n💡 Game ID recomendado para nuevo análisis:")
            print(f"   {games_with_features[0]}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nAsegúrate de que PostgreSQL esté corriendo:")
        print("  docker-compose up -d postgres")


if __name__ == "__main__":
    main()
