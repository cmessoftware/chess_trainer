#!/usr/bin/env python
"""
Script de prueba para endpoints SHAP de Chess Trainer API.
"""
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"


class ChessTrainerAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token: Optional[str] = None

    def login(self, username: str, password: str) -> bool:
        """Autenticarse y obtener token JWT"""
        url = f"{self.base_url}/api/auth/login"
        payload = {"username": username, "password": password}

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print(f"✅ Login exitoso. Token: {self.token[:20]}...")
                return True
            else:
                print(f"❌ Login fallido: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error en login: {e}")
            return False

    def _get_headers(self):
        """Obtener headers con autenticación"""
        if not self.token:
            raise ValueError("No hay token. Ejecuta login() primero.")
        return {"Authorization": f"Bearer {self.token}"}

    def test_error_distribution(self, days: int = 30):
        """Probar endpoint de distribución de errores"""
        url = f"{self.base_url}/api/stats/error-distribution?days={days}"

        try:
            response = requests.get(url, headers=self._get_headers())
            print(f"\n📊 Error Distribution (último {days} días)")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Respuesta: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def test_error_trend(self, days: int = 30):
        """Probar endpoint de tendencia temporal"""
        url = f"{self.base_url}/api/stats/error-trend?days={days}"

        try:
            response = requests.get(url, headers=self._get_headers())
            print(f"\n📈 Error Trend (último {days} días)")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(
                    f"Respuesta ({len(data)} puntos): {json.dumps(data[:3], indent=2)}..."
                )
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def test_global_feature_importance(self, top_k: int = 10):
        """Probar endpoint de feature importance global"""
        url = f"{self.base_url}/api/analysis/global-feature-importance?top_k={top_k}"

        try:
            response = requests.get(url, headers=self._get_headers())
            print(f"\n🧠 Global Feature Importance (top {top_k})")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Respuesta ({len(data)} features): {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def test_move_shap(self, game_id: str, move_number: int = 1):
        """Probar endpoint de SHAP por movimiento"""
        url = f"{self.base_url}/api/analysis/game/{game_id}/shap?move_number={move_number}"

        try:
            response = requests.get(url, headers=self._get_headers())
            print(f"\n♟️  Move SHAP Explanation (move {move_number})")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Respuesta: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")

    def run_analysis(self, game_id: str):
        """Ejecutar análisis ML + SHAP sobre una partida"""
        url = f"{self.base_url}/api/analysis/run"
        payload = {"game_id": game_id}

        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            print(f"\n🧠 Ejecutando Análisis ML + SHAP")
            print(f"Game ID: {game_id}")
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Respuesta: {json.dumps(data, indent=2)}")
                return data.get("analysis_id")
            else:
                print(f"Error: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def run_all_tests(self, game_id: str):
        """Ejecutar todas las pruebas"""
        print("=" * 60)
        print("🧪 INICIANDO PRUEBAS DE ENDPOINTS SHAP")
        print("=" * 60)

        # Primero: Ejecutar análisis sobre la partida
        print("\n🔬 PASO 1: Ejecutar análisis ML + SHAP")
        analysis_id = self.run_analysis(game_id=game_id)

        if analysis_id:
            print(f"✅ Análisis creado con ID: {analysis_id}")
        else:
            print(
                "⚠️  No se pudo ejecutar análisis. Continuando con consulta de datos existentes..."
            )

        # Test 1: Error Distribution
        self.test_error_distribution(days=30)

        # Test 2: Error Trend
        self.test_error_trend(days=30)

        # Test 3: Global Feature Importance
        self.test_global_feature_importance(top_k=10)

        # Test 4: Move SHAP
        self.test_move_shap(game_id=game_id, move_number=1)

        print("\n" + "=" * 60)
        print("✅ PRUEBAS COMPLETADAS")
        print("=" * 60)


def main():
    """Función principal"""
    tester = ChessTrainerAPITester()

    # Login - priorizar usuario "cmess" ya que tiene análisis conocido
    usuarios_prueba = [
        ("cmess", "test123"),
        ("admin", "admin123"),
        ("user", "user123"),
        ("analyst", "analyst123"),
    ]

    login_exitoso = False
    for username, password in usuarios_prueba:
        print(f"\n🔐 Intentando login con: {username}")
        if tester.login(username=username, password=password):
            login_exitoso = True
            break

    if not login_exitoso:
        print("❌ No se pudo autenticar con ningún usuario. Abortando pruebas.")
        return

    # Game ID de ejemplo (del POSTMAN_SHAP_GUIDE.md - análisis confirmado)
    game_id = "00a474189fe12b8e90da2f2eaa9ea94a4daccd58291652c4b825a2b83b87b245"

    # Ejecutar todas las pruebas
    tester.run_all_tests(game_id=game_id)


if __name__ == "__main__":
    main()
