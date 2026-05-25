"""
Limpiar análisis antiguos (sin error_label) y ejecutar nuevos análisis de prueba
"""

import requests
import psycopg2

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
        print(response.text)
        return None


def clean_old_analyses():
    """Eliminar análisis antiguos sin error_label"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chess_trainer_db",
            user="chess",
            password="chess_pass",
        )
        cursor = conn.cursor()

        # Contar análisis sin error_label
        cursor.execute(
            """
            SELECT COUNT(DISTINCT m.analysis_id)
            FROM move_shap_values m
            WHERE m.error_label IS NULL
        """
        )
        count_before = cursor.fetchone()[0]
        print(f"\n🗑️  Análisis antiguos sin error_label: {count_before}")

        if count_before > 0:
            # Borrar move_shap_values sin error_label
            cursor.execute(
                """
                DELETE FROM move_shap_values
                WHERE error_label IS NULL
            """
            )

            # Borrar analysis_results orphan
            cursor.execute(
                """
                DELETE FROM analysis_results
                WHERE id NOT IN (SELECT DISTINCT analysis_id FROM move_shap_values)
            """
            )

            conn.commit()
            print(f"✅ Análisis antiguos eliminados")
        else:
            print(f"✅ No hay análisis antiguos para eliminar")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error limpiando análisis: {e}")


def get_test_game_ids():
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
            SELECT DISTINCT game_id 
            FROM features 
            WHERE move_number IS NOT NULL
            LIMIT 3
        """
        )

        game_ids = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return game_ids

    except Exception as e:
        print(f"❌ Error obteniendo game_ids: {e}")
        return []


def run_analysis(token, game_id):
    """Ejecutar análisis en un game"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.post(
        f"{BASE_URL}/api/analysis/run", headers=headers, json={"game_id": game_id}
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Análisis completado: ID={data['analysis_id']}")
        return data["analysis_id"]
    else:
        print(f"\n❌ Error en análisis: {response.status_code}")
        print(response.text)
        return None


def check_error_label_distribution():
    """Verificar distribución de error_labels en los nuevos análisis"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chess_trainer_db",
            user="chess",
            password="chess_pass",
        )
        cursor = conn.cursor()

        print(f"\n{'='*80}")
        print("📊 DISTRIBUCIÓN DE ERROR_LABELS EN MOVE_SHAP_VALUES")
        print(f"{'='*80}")

        cursor.execute(
            """
            SELECT error_label, COUNT(*) as count
            FROM move_shap_values
            WHERE error_label IS NOT NULL
            GROUP BY error_label
            ORDER BY COUNT(*) DESC
        """
        )

        results = cursor.fetchall()
        total = sum(row[1] for row in results)

        if total == 0:
            print("⚠️  No hay datos con error_label")
        else:
            print(f"\nTotal registros: {total:,}")
            print(f"\n{'Error Label':<15} {'Count':<10} {'Percentage'}")
            print("-" * 40)
            for label, count in results:
                percentage = (count / total) * 100
                print(f"{label:<15} {count:<10,} {percentage:>6.2f}%")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"❌ Error verificando distribución: {e}")


def main():
    print("=" * 80)
    print("TEST: Predicción ML de error_labels en SHAP")
    print("=" * 80)

    # 1. Login
    token = login()
    if not token:
        return

    # 2. Limpiar análisis antiguos
    clean_old_analyses()

    # 3. Obtener game_ids de prueba
    print("\n📋 Obteniendo game_ids para análisis...")
    game_ids = get_test_game_ids()
    print(f"✅ Game IDs disponibles: {game_ids}")

    if not game_ids:
        print("❌ No hay game_ids con features")
        return

    # 4. Ejecutar análisis en 2-3 games
    print(f"\n{'='*80}")
    print("🔬 EJECUTANDO ANÁLISIS CON PREDICCIÓN ML")
    print(f"{'='*80}")

    for game_id in game_ids[:2]:  # Solo 2 para prueba
        print(f"\n🎯 Analizando game: {game_id}")
        analysis_id = run_analysis(token, game_id)
        if analysis_id:
            print(f"   Analysis ID: {analysis_id}")

    # 5. Verificar distribución de error_labels
    check_error_label_distribution()

    print(f"\n{'='*80}")
    print("✅ Test completado")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
