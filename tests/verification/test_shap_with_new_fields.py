"""
Script para regenerar SHAP de una partida y verificar que incluya los nuevos campos.

Pasos:
1. Login y obtener token
2. Eliminar análisis existente (si existe)
3. Regenerar análisis SHAP
4. Verificar que los campos move_san, move_uci, fen, player_color están presentes
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"
USERNAME = "test_admin"
PASSWORD = "test_password"

# Game ID de test (una de las 4 partidas con SHAP existente)
GAME_ID = "cmess1315-vs-manuelfrp79-2024-08-18-00-15-00"


def ensure_test_user_exists():
    """Crear usuario de test si no existe"""
    try:
        print("\n0️⃣  Verificando usuario de test...")
        response = requests.post(
            f"{API_BASE_URL}/api/auth/register",
            json={
                "username": USERNAME,
                "password": PASSWORD,
                "email": "test@example.com",
            },
        )
        if response.status_code == 200:
            print(f"✅ Usuario {USERNAME} creado")
        else:
            print(f"ℹ️  Usuario {USERNAME} ya existe o hubo un error")
    except Exception as e:
        print(f"ℹ️  {e}")


def login():
    """Obtener token de autenticación"""
    print("\n1️⃣  Obteniendo token...")
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD},
    )
    response.raise_for_status()
    token = response.json()["token"]
    print("✅ Token obtenido")
    return token


def delete_existing_analysis(game_id, token):
    """Eliminar análisis existente si existe"""
    print(f"\n2️⃣  Eliminando análisis existente para {game_id}...")
    try:
        response = requests.delete(
            f"{API_BASE_URL}/api/analysis/{game_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code == 200:
            print("✅ Análisis anterior eliminado")
        elif response.status_code == 404:
            print("ℹ️  No había análisis previo")
        else:
            print(f"⚠️  Status code: {response.status_code}")
    except Exception as e:
        print(f"ℹ️  No se pudo eliminar análisis previo: {e}")


def generate_shap_analysis(game_id, token):
    """Generar nuevo análisis SHAP"""
    print(f"\n3️⃣  Generando análisis SHAP para {game_id}...")
    response = requests.post(
        f"{API_BASE_URL}/api/analysis/shap",
        json={"game_id": game_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    if response.status_code != 200:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return False

    result = response.json()
    print(f"✅ Análisis generado!")
    print(f"   Total SHAP values: {result.get('total_shap_values', 'N/A')}")
    print(
        f"   Accuracy: {result.get('model_accuracy', 'N/A'):.2%}"
        if result.get("model_accuracy")
        else ""
    )
    return True


def verify_shap_fields(game_id, token):
    """Verificar que los nuevos campos están presentes"""
    print(f"\n4️⃣  Verificando nuevos campos en SHAP...")
    response = requests.get(
        f"{API_BASE_URL}/api/analysis/shap/game/{game_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    response.raise_for_status()

    data = response.json()
    shap_values = data.get("shap_values", [])

    if not shap_values:
        print("❌ No se encontraron SHAP values")
        return False

    print(f"✅ {len(shap_values)} SHAP values encontrados")

    # Verificar primer SHAP value
    first = shap_values[0]

    print("\n" + "=" * 70)
    print("📊 EJEMPLO DE SHAP VALUE CON NUEVOS CAMPOS:")
    print("=" * 70)

    required_fields = ["move_san", "move_uci", "fen", "player_color"]
    all_present = True

    for field in required_fields:
        value = first.get(field)
        status = "✅" if value and value != "N/A" else "❌"
        print(f"{status} {field}: {value}")
        if not value or value == "N/A":
            all_present = False

    if all_present:
        print("\n" + "=" * 70)
        print("✅ TODOS LOS CAMPOS NUEVOS ESTÁN PRESENTES")
        print("=" * 70)

        # Mostrar ejemplo completo
        print(
            f"""
📍 Move {first.get('move_number')}: {first.get('move_san')} ({first.get('move_uci')})
   Jugador: {first.get('player_color')}
   Clasificación: {first.get('error_label')}
   Feature: {first.get('feature_name')}
   SHAP Value: {first.get('shap_value'):.4f}
   FEN: {first.get('fen')[:50]}...
        """
        )
    else:
        print("\n" + "=" * 70)
        print("⚠️  ALGUNOS CAMPOS ESTÁN VACÍOS")
        print("=" * 70)

    return all_present


def main():
    print("=" * 70)
    print("🔬 TEST: Regenerar SHAP con Nuevos Campos")
    print("=" * 70)

    try:
        # 0. Asegurar que el usuario existe
        ensure_test_user_exists()

        # 1. Login
        token = login()

        # 2. Eliminar análisis anterior
        delete_existing_analysis(GAME_ID, token)

        # Esperar un poco
        print("\n⏳ Esperando 2 segundos...")
        time.sleep(2)

        # 3. Generar nuevo análisis
        success = generate_shap_analysis(GAME_ID, token)

        if not success:
            print("\n❌ No se pudo generar el análisis")
            return

        # Esperar a que se complete el procesamiento
        print("\n⏳ Esperando 3 segundos para que se complete...")
        time.sleep(3)

        # 4. Verificar campos
        all_ok = verify_shap_fields(GAME_ID, token)

        if all_ok:
            print("\n🎉 ¡TEST EXITOSO! Los nuevos campos están funcionando.")
            print("🌐 Puedes verificar en Postman o en el navegador:")
            print(f"   GET {API_BASE_URL}/api/analysis/shap/game/{GAME_ID}")
        else:
            print("\n⚠️  Algunos campos no tienen datos. Verifica los logs del API.")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: No se puede conectar al API")
        print("   Asegúrate de que el API esté corriendo en http://localhost:8000")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
