#!/usr/bin/env python
"""
Script para verificar game_ids y ejecutar pruebas de análisis SHAP.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# Game IDs a probar
GAME_IDS = [
    "6d1df9ea8d5c2d208f4a5b32c87bc62cf3f23e60511037c6dda337fc472980a3",
    "f195fb3ea8454c9f646eacabe04b4e46990de731be39d1f378b628c0c723f313",
    "c8392462c80815c9c39026a1f6bf4b9d363a6cbc78bc0e12d6db8676e6dfae4c",
    "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb",
]


class ChessTrainerTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.token = None

    def login(self, username: str, password: str) -> bool:
        """Autenticarse y obtener token JWT"""
        url = f"{self.base_url}/api/auth/login"
        payload = {"username": username, "password": password}

        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                print(f"✅ Login exitoso como: {username}")
                return True
            else:
                print(f"❌ Login fallido: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error en login: {e}")
            return False

    def _get_headers(self):
        """Obtener headers con autenticación"""
        if not self.token:
            raise ValueError("No hay token. Ejecuta login() primero.")
        return {"Authorization": f"Bearer {self.token}"}

    def run_analysis(self, game_id: str):
        """Ejecutar análisis ML + SHAP sobre una partida"""
        url = f"{self.base_url}/api/analysis/run"
        payload = {"game_id": game_id}

        print(f"\n{'='*80}")
        print(f"🧠 Ejecutando Análisis ML + SHAP")
        print(f"Game ID: {game_id[:16]}...")
        print(f"{'='*80}")

        try:
            response = requests.post(url, json=payload, headers=self._get_headers())
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                print(f"✅ ANÁLISIS EXITOSO!")
                print(f"   Analysis ID: {data.get('analysis_id')}")
                print(f"   Status: {data.get('status')}")
                print(f"   Message: {data.get('message')}")
                return data.get("analysis_id")
            else:
                error_data = response.json()
                print(f"❌ Error: {error_data.get('message', 'Unknown error')}")
                return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            return None

    def check_move_shap(self, game_id: str, move_number: int = 1):
        """Verificar SHAP values de un movimiento"""
        url = f"{self.base_url}/api/analysis/game/{game_id}/shap?move_number={move_number}"

        print(f"\n♟️  Consultando SHAP para movimiento {move_number}...")

        try:
            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()
                top_features = data.get("top_features", [])

                if top_features:
                    print(f"✅ SHAP values encontrados!")
                    print(f"   Error Level: {data.get('error_level')}")
                    print(f"   Top 5 Features:")
                    for i, feat in enumerate(top_features[:5], 1):
                        print(
                            f"      {i}. {feat.get('feature')}: {feat.get('impact'):.4f}"
                        )
                else:
                    print(f"⚠️  Sin SHAP values para este movimiento")

                return len(top_features) > 0
            else:
                print(f"❌ Error {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Exception: {e}")
            return False

    def check_global_importance(self):
        """Verificar feature importance global"""
        url = f"{self.base_url}/api/analysis/global-feature-importance?top_k=5"

        print(f"\n🧠 Consultando Feature Importance Global...")

        try:
            response = requests.get(url, headers=self._get_headers())

            if response.status_code == 200:
                data = response.json()

                if data:
                    print(f"✅ {len(data)} features encontradas!")
                    for i, feat in enumerate(data[:5], 1):
                        print(
                            f"   {i}. {feat.get('feature_name')}: {feat.get('mean_abs_shap_value'):.4f}"
                        )
                else:
                    print(f"⚠️  Sin datos de feature importance")

                return len(data) > 0
            else:
                print(f"❌ Error {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Exception: {e}")
            return False


def main():
    """Función principal"""
    print("=" * 80)
    print("🧪 PRUEBAS DE ANÁLISIS SHAP - MÚLTIPLES GAME IDS")
    print("=" * 80)

    tester = ChessTrainerTester()

    # Login
    if not tester.login(username="admin", password="admin123"):
        print("❌ No se pudo autenticar. Abortando pruebas.")
        return

    # Probar cada game_id
    successful_analyses = []
    failed_analyses = []

    for game_id in GAME_IDS:
        analysis_id = tester.run_analysis(game_id)

        if analysis_id:
            successful_analyses.append((game_id, analysis_id))
            # Verificar SHAP del primer movimiento
            tester.check_move_shap(game_id, move_number=1)
        else:
            failed_analyses.append(game_id)

    # Verificar feature importance global
    print("\n" + "=" * 80)
    tester.check_global_importance()

    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 80)
    print(f"✅ Análisis exitosos: {len(successful_analyses)}")
    print(f"❌ Análisis fallidos: {len(failed_analyses)}")

    if successful_analyses:
        print(f"\n🎯 IDs de análisis generados:")
        for game_id, analysis_id in successful_analyses:
            print(f"   - Analysis ID {analysis_id}: {game_id[:16]}...")

    if failed_analyses:
        print(f"\n⚠️  Game IDs sin features:")
        for game_id in failed_analyses:
            print(f"   - {game_id[:16]}...")


if __name__ == "__main__":
    main()
