"""
Script simple para verificar que el endpoint SHAP devuelve los nuevos campos.

IMPORTANTE: Primero debes obtener un token válido desde Postman:
1. POST http://localhost:8000/api/ auth/login con credentials válidas
2. Copiar el token aquí

Luego ejecutar este script.
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

# PEGAR TOKEN DE POSTMAN AQUÍ:
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImNtZXNzMTMxNSIsImV4cCI6MTc0MDgyMTI1NH0.Kx7nCi3rH-xrE5RLHMu4r5LwCZHXh3DYCHXHQiPf6Bs"  # Cambiar por token válido

# Game ID con SHAP existente (pero con NULL en los nuevos campos)
GAME_ID = "cmess1315-vs-manuelfrp79-2024-08-18-00-15-00"


def check_shap_fields():
    """Verificar campos en SHAP values existentes"""
    print("=" * 70)
    print("🔍 Verificando Campos de SHAP")
    print("=" * 70)
    print(f"\nGame ID: {GAME_ID}")
    print(f"Endpoint: GET /api/analysis/shap/game/{GAME_ID}\n")

    try:
        response = requests.get(
            f"{API_BASE_URL}/api/analysis/shap/game/{GAME_ID}",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )

        if response.status_code == 401:
            print("❌ Token inválido o expirado")
            print("\n📝 Para obtener un token válido:")
            print("   1. Abre Postman")
            print("   2. POST http://localhost:8000/api/auth/login")
            print('   3. Body: {"username": "tu_usuario", "password": "tu_password"}')
            print("   4. Copia el token de la respuesta")
            print("   5. Pégalo en este script (línea 16)")
            return False

        response.raise_for_status()
        data = response.json()

        shap_values = data.get("shap_values", [])

        if not shap_values:
            print("⚠️  No se encontraron SHAP values para este game_id")
            return False

        print(f"✅ {len(shap_values)} SHAP values encontrados\n")

        # Analizar primer SHAP value
        first = shap_values[0]

        print("=" * 70)
        print("📊 ESTRUCTURA DEL SHAP VALUE:")
        print("=" * 70)

        # Campos esperados
        expected_new_fields = {
            "move_san": "Notación algebraica (e.g., 'Nf3')",
            "move_uci": "Notación UCI (e.g., 'g1f3')",
            "fen": "Posición FEN",
            "player_color": "Color del jugador ('white'/'black')",
        }

        existing_fields = {
            "move_number": "Número de jugada",
            "feature_name": "Nombre del feature",
            "shap_value": "Valor SHAP",
            "error_label": "Clasificación ML",
        }

        print("\n🆕 CAMPOS NUEVOS:")
        all_new_present = True
        for field, description in expected_new_fields.items():
            value = first.get(field)
            has_data = value and value not in ["N/A", None, ""]
            status = "✅" if has_data else "⚠️"
            display_value = str(value)[:40] if value else "NULL"
            print(f"  {status} {field:15} = {display_value}")
            print(f"      ({description})")
            if not has_data:
                all_new_present = False

        print("\n📋 CAMPOS EXISTENTES:")
        for field, description in existing_fields.items():
            value = first.get(field)
            display_value = str(value)[:40] if value else "NULL"
            print(f"  ✓ {field:15} = {display_value}")

        print("\n" + "=" * 70)
        if all_new_present:
            print("🎉 ÉXITO: Todos los campos nuevos tienen datos")
            print("=" * 70)
            print("\n📝 Ejemplo completo:")
            print(json.dumps(first, indent=2))
        else:
            print("⚠️  ADVERTENCIA: Algunos campos nuevos están vacíos (NULL)")
            print("=" * 70)
            print(
                "\n💡 Esto es esperado si el SHAP se generó ANTES de aplicar las migrations."
            )
            print("   Para poblar los campos:")
            print("   1. DELETE el análisis existente:")
            print(f"      DELETE http://localhost:8000/api/analysis/{GAME_ID}")
            print("   2. Regenera el SHAP:")
            print(f"      POST http://localhost:8000/api/analysis/shap")
            print(f'      Body: {{"game_id": "{GAME_ID}"}}')

        return all_new_present

    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al API")
        print("   Verifica que esté corriendo en http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    check_shap_fields()
