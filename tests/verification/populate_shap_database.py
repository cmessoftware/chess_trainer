"""
Script para ejecutar múltiples análisis y poblar la base de datos
con SHAP values confiables
"""

import requests
import psycopg2
from time import sleep

BASE_URL = "http://localhost:8000"


def login():
    """Login y obtener JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login", json={"username": "admin", "password": "admin123"}
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login exitoso")
        return token
    else:
        print(f"❌ Error en login: {response.status_code}")
        return None


def get_games_with_features():
    """Obtener game_ids que tienen features"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chess_trainer_db",
            user="chess",
            password="chess_pass",
        )
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT game_id, COUNT(*) as num_moves
            FROM features 
            WHERE move_number IS NOT NULL
            GROUP BY game_id
            HAVING COUNT(*) >= 10
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """
        )

        games = cursor.fetchall()
        cursor.close()
        conn.close()

        return games

    except Exception as e:
        print(f"❌ Error obteniendo games: {e}")
        return []


def run_analysis(token, game_id):
    """Ejecutar análisis en un game"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.post(
        f"{BASE_URL}/api/analysis/run", headers=headers, json={"game_id": game_id}
    )

    if response.status_code == 200:
        data = response.json()
        return data["analysis_id"]
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")
        return None


def get_shap_distribution():
    """Obtener estadísticas de error_labels en toda la base de datos"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chess_trainer_db",
            user="chess",
            password="chess_pass",
        )
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 
                error_label, 
                COUNT(*) as count,
                COUNT(DISTINCT analysis_id) as num_analyses
            FROM move_shap_values
            WHERE error_label IS NOT NULL
            GROUP BY error_label
            ORDER BY COUNT(*) DESC
        """
        )

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return results

    except Exception as e:
        print(f"❌ Error obteniendo distribución: {e}")
        return []


def main():
    print("=" * 80)
    print("EJECUTAR MÚLTIPLES ANÁLISIS CON ERROR_LABELS CONFIABLES")
    print("=" * 80)

    # Login
    token = login()
    if not token:
        return

    # Obtener games
    print("\n📋 Obteniendo games con features...")
    games = get_games_with_features()
    print(f"✅ {len(games)} games disponibles")

    if not games:
        print("❌ No hay games con features suficientes")
        return

    # Ejecutar análisis
    print(f"\n{'='*80}")
    print("🔬 EJECUTANDO ANÁLISIS")
    print(f"{'='*80}\n")

    analysis_ids = []
    for i, (game_id, num_moves) in enumerate(games[:5], 1):  # Primeros 5
        print(f"[{i}/5] Game: {game_id[:20]}... ({num_moves} moves)")
        analysis_id = run_analysis(token, game_id)
        if analysis_id:
            print(f"      ✅ Analysis ID: {analysis_id}")
            analysis_ids.append(analysis_id)
        sleep(0.5)  # Evitar saturación

    # Estadísticas finales
    print(f"\n{'='*80}")
    print("📊 ESTADÍSTICAS FINALES")
    print(f"{'='*80}\n")

    distribution = get_shap_distribution()
    total = sum(r[1] for r in distribution)

    print(f"Total SHAP values: {total:,}")
    print(
        f"Total análisis: {analysis_ids[0] if analysis_ids else 0} - {analysis_ids[-1] if len(analysis_ids) > 1 else analysis_ids[0] if analysis_ids else 0}"
    )
    print(f"\n{'Error Label':<15} {'Count':<10} {'Analyses':<10} {'Percentage'}")
    print("-" * 55)

    for label, count, num_analyses in distribution:
        percentage = (count / total) * 100
        print(f"{label:<15} {count:<10,} {num_analyses:<10} {percentage:>6.2f}%")

    print(f"\n{'='*80}")
    print("✅ Análisis completados - Base de datos poblada con SHAP confiables")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
