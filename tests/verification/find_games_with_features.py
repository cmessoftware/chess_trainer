#!/usr/bin/env python
"""
Script para encontrar game_ids con features en la base de datos.
"""
import psycopg2
import sys

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "chess_trainer_db",
    "user": "chess",
    "password": "chess_pass",
}


def get_games_with_features(limit=10):
    """Obtener game_ids que tienen features"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Obtener games con buen número de features (más de 20 movimientos)
        query = """
            SELECT game_id, COUNT(*) as move_count
            FROM features
            GROUP BY game_id
            HAVING COUNT(*) > 20
            ORDER BY COUNT(*) DESC
            LIMIT %s
        """

        cur.execute(query, (limit,))
        results = cur.fetchall()

        print("=" * 80)
        print(f"🎯 GAME IDS CON FEATURES (Top {limit})")
        print("=" * 80)

        if results:
            for idx, (game_id, move_count) in enumerate(results, 1):
                print(f"{idx}. {game_id} ({move_count} movimientos)")
        else:
            print("⚠️  No se encontraron partidas con features")

        cur.close()
        conn.close()

        return [r[0] for r in results]

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


if __name__ == "__main__":
    game_ids = get_games_with_features(limit=10)

    if game_ids:
        print(f"\n💡 Usa estos game_ids para pruebas:")
        print(f"GAME_IDS = [")
        for game_id in game_ids[:5]:
            print(f'    "{game_id}",')
        print(f"]")
