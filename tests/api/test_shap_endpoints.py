"""
Script de testing para endpoints de SHAP Analysis API.
Equivalente a colección de Postman para FUNCIONALIDAD 3.6

Requisitos:
- Backend corriendo en localhost:8000
- Usuario admin con password admin123
- Features extraídas para alguna partida

Uso:
    conda activate chess_trainer
    python tests/api/test_shap_endpoints.py
"""

import requests
import json
from datetime import datetime


# Configuración
API_BASE = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"


def print_section(title):
    """Helper para imprimir secciones"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def login():
    """1. Login y obtener token JWT"""
    print_section("🔐 TEST 1: Login")

    response = requests.post(
        f"{API_BASE}/auth/login", json={"username": USERNAME, "password": PASSWORD}
    )

    if response.status_code == 200:
        data = response.json()
        token = data.get("access_token")
        print(f"✅ Login exitoso")
        print(f"📝 Token: {token[:50]}...")
        return token
    else:
        print(f"❌ Login falló: {response.status_code}")
        print(f"Response: {response.text}")
        return None


def test_run_analysis(token, game_id):
    """2. Ejecutar análisis ML + SHAP"""
    print_section("🧠 TEST 2: POST /api/analysis/run")

    headers = {"Authorization": f"Bearer {token}"}
    payload = {"game_id": game_id}

    response = requests.post(
        f"{API_BASE}/api/analysis/run", json=payload, headers=headers
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ Análisis ejecutado")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data.get("analysis_id")
    else:
        print(f"❌ Error: {response.text[:500]}")
        return None


def test_error_distribution(token):
    """3. Obtener distribución de errores"""
    print_section("📊 TEST 3: GET /api/stats/error-distribution")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE}/api/stats/error-distribution?days=30", headers=headers
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Distribución obtenida")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ Error: {response.text[:500]}")
        return None


def test_error_trend(token):
    """4. Obtener evolución temporal"""
    print_section("📈 TEST 4: GET /api/stats/error-trend")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE}/api/stats/error-trend?days=90&interval_days=7", headers=headers
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Tendencia obtenida ({len(data)} puntos)")
        if data:
            print("Primeros 3 puntos:")
            print(json.dumps(data[:3], indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ Error: {response.text[:500]}")
        return None


def test_global_feature_importance(token):
    """5. Obtener feature importance global (SHAP)"""
    print_section("🧠 TEST 5: GET /api/analysis/global-feature-importance")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE}/api/analysis/global-feature-importance?top_k=10", headers=headers
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Feature importance obtenida ({len(data)} features)")
        if data:
            print("Top 5 features:")
            print(json.dumps(data[:5], indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ Error: {response.text[:500]}")
        return None


def test_move_shap_explanation(token, game_id, move_number=10):
    """6. Obtener explicación SHAP para una jugada"""
    print_section(f"♟️  TEST 6: GET /api/analysis/game/{game_id}/shap")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE}/api/analysis/game/{game_id}/shap?move_number={move_number}",
        headers=headers,
    )

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Explicación SHAP obtenida para jugada {move_number}")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ Error: {response.text[:500]}")
        return None


def test_analysis_history(token):
    """7. Obtener historial de análisis"""
    print_section("📜 TEST 7: GET /api/analysis/history")

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE}/api/analysis/history?limit=5", headers=headers)

    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Historial obtenido ({data.get('total', 0)} análisis)")
        if data.get("results"):
            print("Primeros 3 análisis:")
            print(json.dumps(data["results"][:3], indent=2, ensure_ascii=False))
        return data
    else:
        print(f"❌ Error: {response.text[:500]}")
        return None


def get_sample_game_id(token):
    """Helper: Obtener un game_id de muestra con features"""
    print_section("🔍 Obteniendo game_id de muestra")

    try:
        import os
        import sqlalchemy

        engine = sqlalchemy.create_engine(os.getenv("CHESS_TRAINER_DB_URL"))

        query = """
        SELECT DISTINCT game_id 
        FROM public.features 
        LIMIT 1
        """

        with engine.connect() as conn:
            result = conn.execute(sqlalchemy.text(query))
            row = result.fetchone()
            if row:
                game_id = row[0]
                print(f"✅ Game ID encontrado: {game_id}")
                return game_id

        print("❌ No se encontraron partidas con features")
        return None

    except Exception as e:
        print(f"❌ Error obteniendo game_id: {e}")
        return None


def main():
    """Ejecutar suite completa de tests"""
    print("\n" + "=" * 60)
    print("  🧪 TESTING SUITE - SHAP ANALYSIS API")
    print("  FUNCIONALIDAD 3.6 - ML + SHAP Dashboard")
    print("=" * 60)

    # 1. Login
    token = login()
    if not token:
        print("\n❌ Abortando: Login falló")
        return

    # 2. Obtener game_id de muestra
    game_id = get_sample_game_id(token)
    if not game_id:
        print(
            "\n⚠️  No hay game_id disponible. Probando endpoints sin análisis previo..."
        )
        game_id = "dummy_game_123"  # Fallback

    # 3. Ejecutar análisis ML
    analysis_id = test_run_analysis(token, game_id)

    # 4. Obtener distribución de errores
    test_error_distribution(token)

    # 5. Obtener evolución temporal
    test_error_trend(token)

    # 6. Obtener feature importance global
    test_global_feature_importance(token)

    # 7. Obtener explicación SHAP por jugada
    if game_id != "dummy_game_123":
        test_move_shap_explanation(token, game_id, move_number=10)

    # 8. Obtener historial
    test_analysis_history(token)

    # Resumen final
    print_section("📊 RESUMEN")
    print("✅ Suite de testing completada")
    print(f"🕒 Timestamp: {datetime.now().isoformat()}")
    print(f"🔗 API Base: {API_BASE}")
    print(f"👤 Usuario: {USERNAME}")
    print("\n💡 Para Postman:")
    print("   1. Importar colección desde este script")
    print("   2. Configurar variable {{token}} con el access_token")
    print("   3. Ejecutar requests con Bearer {{token}}")


if __name__ == "__main__":
    main()
