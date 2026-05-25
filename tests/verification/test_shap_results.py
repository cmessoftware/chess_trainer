import requests
import json

# Login
token_resp = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"username": "admin", "password": "admin123"},
)
token = token_resp.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

game_id = "00a474189fe12b8e90da2f2eaa9ea94a4daccd58291652c4b825a2b83b87b245"

print("=" * 80)
print("ENDPOINTS DISPONIBLES PARA VER RESULTADOS DEL ANÁLISIS")
print("=" * 80)
print()

# 1. SHAP por movimiento
print("1️⃣ GET /api/analysis/game/{game_id}/shap?move_number=1")
print("   📝 Valores SHAP para cada movimiento de la partida")
print(f"   🔗 {{{{baseUrl}}}}/api/analysis/game/{game_id}/shap?move_number=1")
resp1 = requests.get(
    f"http://localhost:8000/api/analysis/game/{game_id}/shap", headers=headers
)
print(f"   📊 Status: {resp1.status_code}")
if resp1.status_code == 200:
    data = resp1.json()
    shap_count = len(data.get("shap_values", []))
    print(f"   ✅ Resultados: {shap_count} movimientos con valores SHAP")
    if data.get("shap_values"):
        first_move = data["shap_values"][0]
        print(f"   📍 Ejemplo (movimiento #1):")
        print(f'      move_number: {first_move.get("move_number")}')
        print(f'      predicted_error: {first_move.get("predicted_error_level")}')
        print(
            f'      top_3_features: {list(first_move.get("shap_values", {}).keys())[:3]}'
        )
else:
    print(f"   ❌ Error: {resp1.json()}")
print()

# 2. Importancia global
print("2️⃣ GET /api/analysis/global-feature-importance")
print("   📝 Ranking de features más importantes globalmente")
print("   🔗 {{baseUrl}}/api/analysis/global-feature-importance")
resp2 = requests.get(
    "http://localhost:8000/api/analysis/global-feature-importance", headers=headers
)
print(f"   📊 Status: {resp2.status_code}")
if resp2.status_code == 200:
    data = resp2.json()
    print(f"   ✅ Top 5 features más importantes:")
    for idx, feat in enumerate(data[:5], 1):
        print(f'      {idx}. {feat["feature_name"]}: {feat["mean_abs_shap"]:.4f}')
else:
    print(f"   ❌ Error: {resp2.json()}")
print()

# 3. Distribución de errores
print("3️⃣ GET /api/stats/error-distribution")
print("   📝 Conteo de blunders, mistakes, inaccuracies, good moves")
print("   🔗 {{baseUrl}}/api/stats/error-distribution")
resp3 = requests.get(
    "http://localhost:8000/api/stats/error-distribution", headers=headers
)
print(f"   📊 Status: {resp3.status_code}")
if resp3.status_code == 200:
    data = resp3.json()
    print(f"   ✅ Distribución:")
    for item in data.get("distribution", []):
        print(
            f'      {item["error_level"]}: {item["count"]} ({item["percentage"]:.1f}%)'
        )
else:
    print(f"   ❌ Error: {resp3.json()}")
print()

# 4. Tendencia temporal
print("4️⃣ GET /api/stats/error-trend?days=30")
print("   📝 Evolución de errores en los últimos 30 días")
print("   🔗 {{baseUrl}}/api/stats/error-trend?days=30")
resp4 = requests.get(
    "http://localhost:8000/api/stats/error-trend?days=30", headers=headers
)
print(f"   📊 Status: {resp4.status_code}")
if resp4.status_code == 200:
    data = resp4.json()
    trend_count = len(data.get("trend", []))
    print(f"   ✅ Puntos de datos: {trend_count}")
    if data.get("trend"):
        print(f"   📅 Ejemplo (último día):")
        last = data["trend"][-1]
        print(f'      date: {last.get("date")}')
        print(f'      avg_error: {last.get("avg_error_level")}')
else:
    print(f"   ❌ Error: {resp4.json()}")
print()

print("=" * 80)
print("💡 CÓMO USAR EN POSTMAN:")
print("=" * 80)
print()
print("1. Copia cualquiera de las URLs mostradas arriba")
print("2. Crea un nuevo GET request en Postman")
print("3. En Headers, agrega: Authorization: Bearer {{authToken}}")
print("4. Envía el request")
print()
print("🎯 Para visualización en frontend, estos datos alimentan:")
print("   - Gráfico de barras: endpoint #2 (feature importance)")
print("   - Gráfico circular: endpoint #3 (error distribution)")
print("   - Gráfico de líneas: endpoint #4 (error trend)")
print("   - Panel interactivo: endpoint #1 (SHAP por movimiento)")
