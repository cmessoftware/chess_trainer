# -*- coding: utf-8 -*-
"""Pruebas SHAP simplificadas - Version sin emojis"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import requests
import json
from pathlib import Path

# Configuracion
BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api"

# Credenciales de prueba
TEST_USER = {"username": "admin", "password": "admin123"}

# Game IDs de prueba
TEST_GAME_IDS = [
    "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3",
    "f195fb3ea8454c9f646eacabe04b4e46990de731be39d1f378b628c0c723f313",
    "c8392462c80815c9c39026a1f6bf4b9d363a6cbc78bc0e12d6db8676e6dfae4c",
    "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb",
]


def test_shap():
    """Probar analisis SHAP con game_ids que tienen features"""

    print("\n" + "=" * 80)
    print("PRUEBAS DE ANALISIS SHAP")
    print("=" * 80 + "\n")

    # 1. Login
    print("[1/3] Autenticando...")
    response = requests.post(f"{API_URL}/auth/login", json=TEST_USER)
    if response.status_code != 200:
        print(f"   [ERROR] Login fallido: {response.status_code}")
        print(f"   {response.text}")
        return

    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("   [OK] Autenticado correctamente\n")

    # 2. Ejecutar analisis para cada game_id
    print("[2/3] Ejecutando analisis SHAP...")
    print("-" * 80)

    success = 0
    failed = 0

    for i, game_id in enumerate(TEST_GAME_IDS, 1):
        print(f"\n[{i}/4] Analizando: {game_id[:32]}...")

        # Ejecutar analisis
        response = requests.post(
            f"{API_URL}/analysis/run", headers=headers, json={"game_id": game_id}
        )

        if response.status_code == 200:
            result = response.json()
            print(f"   [OK] Analisis completado")
            print(f"   - Accuracy: {result.get('accuracy', 'N/A')}")
            print(f"   - Moves analizados: {result.get('total_moves', 'N/A')}")
            success += 1
        else:
            print(f"   [FAIL] Status: {response.status_code}")
            print(f"   - Error: {response.text[:200]}")
            failed += 1

    # 3. Verificar valores SHAP guardados
    print("\n" + "=" * 80)
    print("[3/3] Consultando valores SHAP guardados...")
    print("-" * 80)

    for i, game_id in enumerate(TEST_GAME_IDS, 1):
        print(f"\n[{i}/4] {game_id[:32]}...")

        # Consultar SHAP values para move_number=1
        response = requests.get(
            f"{API_URL}/analysis/game/{game_id}/shap",
            headers=headers,
            params={"move_number": 1},
        )

        if response.status_code == 200:
            shap_data = response.json()
            print(f"   [OK] SHAP data obtenido")
            print(f"   - Move: {shap_data.get('move_number', '?')}")
            print(f"   - Error level: {shap_data.get('error_level', '?')}")
            print(f"   - Top features: {len(shap_data.get('top_features', []))}")
        else:
            print(f"   [FAIL] Status: {response.status_code}")
            if response.text:
                print(f"   - Error: {response.text[:200]}")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Exitosos: {success}")
    print(f"Fallidos: {failed}")
    print(f"Total: {len(TEST_GAME_IDS)}")
    print()


if __name__ == "__main__":
    test_shap()
