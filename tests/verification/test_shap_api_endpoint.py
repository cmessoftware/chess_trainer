"""
Test completo del endpoint GET /api/analysis/shap/game/{game_id}
Consulta SHAP values con game information usando la vista SQL
"""

import requests
from pprint import pprint

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


def get_analyzed_games_from_db():
    """Obtener game_ids con análisis SHAP"""
    import psycopg2

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
            SELECT DISTINCT game_id, COUNT(*) as shap_count
            FROM shap_values_with_games
            GROUP BY game_id
            ORDER BY COUNT(*) DESC
            LIMIT 3
        """
        )

        games = cursor.fetchall()
        cursor.close()
        conn.close()

        return games

    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def test_endpoint_all_shap(token, game_id):
    """Test 1: Obtener todos los SHAP values de un game"""
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{BASE_URL}/api/analysis/shap/game/{game_id}", headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Endpoint respondió: {len(data)} SHAP values")

        # Analizar distribución
        from collections import Counter

        error_counts = Counter(item["error_label"] for item in data)
        total = len(data)

        print(f"\n📊 Distribución de error_labels:")
        for label, count in error_counts.most_common():
            pct = (count / total) * 100
            print(f"   {label:<15} {count:>5} ({pct:>5.1f}%)")

        # Mostrar primeros 3 SHAP values
        print(f"\n🎯 Primeros 3 SHAP values:")
        for i, item in enumerate(data[:3], 1):
            print(f"\n   [{i}] Move {item['move_number']}: {item['feature_name']}")
            print(f"       SHAP value: {item['shap_value']:.4f}")
            print(f"       Feature value: {item['feature_value']:.4f}")
            print(f"       Error label: {item['error_label']}")
            print(f"       Game ID: {item['game_id'][:20]}...")

        return data
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return None


def test_endpoint_move_specific(token, game_id, move_number):
    """Test 2: Obtener SHAP values de una jugada específica"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"move_number": move_number}

    response = requests.get(
        f"{BASE_URL}/api/analysis/shap/game/{game_id}", headers=headers, params=params
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Jugada #{move_number}: {len(data)} features")

        # Top 5 features por impacto
        sorted_data = sorted(data, key=lambda x: abs(x["shap_value"]), reverse=True)

        print(f"\n🔝 Top 5 features con mayor impacto:")
        for i, item in enumerate(sorted_data[:5], 1):
            print(
                f"   {i}. {item['feature_name']:<25} SHAP={item['shap_value']:>7.4f}  Value={item['feature_value']:>7.2f}"
            )

        return data
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return None


def test_endpoint_top_n(token, game_id, top_n):
    """Test 3: Obtener top N features por jugada"""
    headers = {"Authorization": f"Bearer {token}"}
    params = {"top_n": top_n}

    response = requests.get(
        f"{BASE_URL}/api/analysis/shap/game/{game_id}", headers=headers, params=params
    )

    if response.status_code == 200:
        data = response.json()

        # Agrupar por move_number
        from collections import defaultdict

        by_move = defaultdict(list)
        for item in data:
            by_move[item["move_number"]].append(item)

        print(f"\n✅ Top {top_n} features por jugada:")
        print(f"   Total moves: {len(by_move)}")
        print(f"   Total SHAP values: {len(data)}")

        # Mostrar primeras 3 jugadas
        print(f"\n📋 Primeras 3 jugadas:")
        for move_num in sorted(by_move.keys())[:3]:
            features = by_move[move_num]
            print(f"\n   Move {move_num} ({len(features)} features):")
            for feat in sorted(
                features, key=lambda x: abs(x["shap_value"]), reverse=True
            ):
                print(f"      {feat['feature_name']:<25} {feat['shap_value']:>7.4f}")

        return data
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return None


def main():
    print("=" * 80)
    print("TEST COMPLETO: Endpoint GET /api/analysis/shap/game/{game_id}")
    print("=" * 80)

    # Login
    token = login()
    if not token:
        return

    # Obtener game con más SHAP values
    print("\n📋 Obteniendo games con análisis SHAP...")
    games = get_analyzed_games_from_db()

    if not games:
        print("❌ No hay games con análisis SHAP")
        return

    test_game_id, shap_count = games[0]
    print(f"✅ Game seleccionado: {test_game_id[:30]}... ({shap_count} SHAP values)")

    # Test 1: Todos los SHAP values
    print(f"\n{'='*80}")
    print("TEST 1: Obtener TODOS los SHAP values del game")
    print(f"{'='*80}")
    test_endpoint_all_shap(token, test_game_id)

    # Test 2: SHAP values de una jugada específica
    print(f"\n{'='*80}")
    print("TEST 2: Obtener SHAP values de la jugada #10")
    print(f"{'='*80}")
    test_endpoint_move_specific(token, test_game_id, 10)

    # Test 3: Top N features por jugada
    print(f"\n{'='*80}")
    print("TEST 3: Obtener top 5 features por jugada")
    print(f"{'='*80}")
    test_endpoint_top_n(token, test_game_id, 5)

    print(f"\n{'='*80}")
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print(f"{'='*80}")
    print(
        f"\n💡 Endpoint disponible en: GET {BASE_URL}/api/analysis/shap/game/{{game_id}}"
    )
    print(f"   Query params opcionales:")
    print(f"   - move_number: Filtrar por jugada específica")
    print(f"   - top_n: Limitar a top N features por jugada")


if __name__ == "__main__":
    main()
