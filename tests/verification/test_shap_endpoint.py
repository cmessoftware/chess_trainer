"""
Test del nuevo endpoint GET /api/analysis/shap/game/{game_id}

Consulta SHAP values de una partida específica usando la vista SQL.
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"


def login():
    """Login y obtener JWT token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login", data={"username": "admin", "password": "admin123"}
    )

    if response.status_code == 200:
        token = response.json()["access_token"]
        print(f"✅ Login exitoso - Token: {token[:20]}...")
        return token
    else:
        print(f"❌ Error en login: {response.status_code}")
        print(response.text)
        return None


def get_shap_values_by_game(token, game_id, move_number=None, top_n=None):
    """
    Consultar SHAP values de una partida específica

    Args:
        token: JWT token
        game_id: ID del game
        move_number: (opcional) Filtrar por jugada específica
        top_n: (opcional) Limitar a top N features por jugada
    """
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Construir parámetros de query
    params = {}
    if move_number is not None:
        params["move_number"] = move_number
    if top_n is not None:
        params["top_n"] = top_n

    # Request
    response = requests.get(
        f"{BASE_URL}/api/analysis/shap/game/{game_id}", headers=headers, params=params
    )

    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Consulta exitosa - {len(data)} SHAP values")
        return data
    else:
        print(f"\n❌ Error en consulta: {response.status_code}")
        print(response.text)
        return None


def main():
    print("=" * 80)
    print("TEST: Nuevo endpoint GET /api/analysis/shap/game/{game_id}")
    print("=" * 80)

    # 1. Login
    token = login()
    if not token:
        return

    # 2. Buscar un game_id con SHAP values
    print("\n📊 Consultando games con análisis SHAP...")
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
            SELECT DISTINCT game_id 
            FROM shap_values_with_games 
            LIMIT 3
        """
        )

        game_ids = [row[0] for row in cursor.fetchall()]
        print(f"✅ Games con SHAP: {game_ids}")

        cursor.close()
        conn.close()

        if not game_ids:
            print("❌ No hay games con SHAP values")
            return

        # Usar el primer game_id
        test_game_id = game_ids[0]

    except Exception as e:
        print(f"❌ Error consultando DB: {e}")
        return

    # 3. Test 1: Obtener todos los SHAP values del game
    print(f"\n{'='*80}")
    print(f"TEST 1: Obtener todos los SHAP values del game {test_game_id}")
    print(f"{'='*80}")

    shap_values = get_shap_values_by_game(token, test_game_id)

    if shap_values:
        print(f"\n📊 Total SHAP values: {len(shap_values)}")
        print(f"\n🎯 Primer SHAP value:")
        pprint(shap_values[0])

        # Summary por move
        moves = {}
        for sv in shap_values:
            move_num = sv["move_number"]
            if move_num not in moves:
                moves[move_num] = []
            moves[move_num].append(sv)

        print(f"\n📈 Resumen por jugada:")
        for move_num in sorted(moves.keys())[:5]:  # Primeras 5 jugadas
            print(f"  Move {move_num}: {len(moves[move_num])} features")

    # 4. Test 2: Obtener SHAP values de una jugada específica
    print(f"\n{'='*80}")
    print(f"TEST 2: Obtener SHAP values de la jugada #10")
    print(f"{'='*80}")

    shap_values_move = get_shap_values_by_game(token, test_game_id, move_number=10)

    if shap_values_move:
        print(f"\n📊 SHAP values en jugada #10: {len(shap_values_move)}")
        print(f"\n🔝 Top 5 features por impacto:")
        for i, sv in enumerate(
            sorted(shap_values_move, key=lambda x: abs(x["shap_value"]), reverse=True)[
                :5
            ]
        ):
            print(
                f"  {i+1}. {sv['feature_name']}: {sv['shap_value']:.4f} (value: {sv['feature_value']:.4f})"
            )

    # 5. Test 3: Obtener top 5 features por jugada
    print(f"\n{'='*80}")
    print(f"TEST 3: Obtener top 5 features por jugada")
    print(f"{'='*80}")

    shap_values_top = get_shap_values_by_game(token, test_game_id, top_n=5)

    if shap_values_top:
        print(f"\n📊 Total SHAP values (top 5 por jugada): {len(shap_values_top)}")

        # Summary por move
        moves_top = {}
        for sv in shap_values_top:
            move_num = sv["move_number"]
            if move_num not in moves_top:
                moves_top[move_num] = []
            moves_top[move_num].append(sv)

        print(f"\n📈 Primeras 3 jugadas con top 5 features:")
        for move_num in sorted(moves_top.keys())[:3]:
            print(f"\n  Move {move_num}:")
            for i, sv in enumerate(
                sorted(
                    moves_top[move_num],
                    key=lambda x: abs(x["shap_value"]),
                    reverse=True,
                )
            ):
                print(f"    {i+1}. {sv['feature_name']}: {sv['shap_value']:.4f}")

    print(f"\n{'='*80}")
    print("✅ Tests completados")
    print(f"{'='*80}")


if __name__ == "__main__":
    main()
