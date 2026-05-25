"""
Test rápido del endpoint SHAP desde terminal
Útil para verificar que todo funciona antes de usar Postman
"""

import requests
import json

BASE_URL = "http://localhost:8000"
GAME_ID = "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb"

GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_header(text):
    print(f"\n{BLUE}{'='*80}")
    print(text)
    print(f"{'='*80}{RESET}")


def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")


def print_error(text):
    print(f"{RED}❌ {text}{RESET}")


def print_info(text):
    print(f"{YELLOW}📋 {text}{RESET}")


def test_login():
    """Test 1: Login y obtener token"""
    print_header("TEST 1: LOGIN")

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )

        if response.status_code == 200:
            data = response.json()
            token = data["access_token"]
            print_success(f"Login exitoso")
            print_info(f"Token: {token[:30]}...")
            return token
        else:
            print_error(f"Login falló: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_all_shap_values(token):
    """Test 2: Obtener todos los SHAP values"""
    print_header("TEST 2: OBTENER TODOS LOS SHAP VALUES")

    try:
        response = requests.get(
            f"{BASE_URL}/api/analysis/shap/game/{GAME_ID}",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Obtenidos {len(data)} SHAP values")

            # Distribución
            from collections import Counter

            distribution = Counter(item["error_label"] for item in data)
            print_info("Distribución de error_labels:")
            for label, count in distribution.most_common():
                pct = (count / len(data)) * 100
                print(f"   {label:<15} {count:>5,} ({pct:>5.1f}%)")

            # Primer registro
            if data:
                first = data[0]
                print_info("Primer registro:")
                print(f"   Move: {first['move_number']}")
                print(f"   Feature: {first['feature_name']}")
                print(f"   SHAP: {first['shap_value']:.4f}")
                print(f"   Error: {first['error_label']}")

            return True
        else:
            print_error(f"Request falló: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_specific_move(token):
    """Test 3: Obtener SHAP de jugada específica"""
    print_header("TEST 3: SHAP DE JUGADA ESPECÍFICA (Move #10)")

    try:
        response = requests.get(
            f"{BASE_URL}/api/analysis/shap/game/{GAME_ID}?move_number=10",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Obtenidos {len(data)} features para move #10")

            # Top features
            sorted_data = sorted(data, key=lambda x: abs(x["shap_value"]), reverse=True)
            print_info("Top 5 features con mayor impacto:")
            for item in sorted_data[:5]:
                print(
                    f"   {item['feature_name']:<25} SHAP={item['shap_value']:>7.4f}  Value={item['feature_value']}"
                )

            return True
        else:
            print_error(f"Request falló: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_top_n(token):
    """Test 4: Obtener top N features por jugada"""
    print_header("TEST 4: TOP 5 FEATURES POR JUGADA")

    try:
        response = requests.get(
            f"{BASE_URL}/api/analysis/shap/game/{GAME_ID}?top_n=5",
            headers={"Authorization": f"Bearer {token}"},
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Obtenidos {len(data)} SHAP values (top 5 por jugada)")

            # Contar jugadas
            moves = set(item["move_number"] for item in data)
            print_info(f"Jugadas cubiertas: {len(moves)}")
            print_info(f"Features por jugada: {len(data) / len(moves):.1f}")

            # Ejemplo de una jugada
            move_5_data = [item for item in data if item["move_number"] == 5]
            if move_5_data:
                print_info("Top features de jugada #5:")
                for item in move_5_data:
                    print(
                        f"   {item['feature_name']:<25} SHAP={item['shap_value']:>7.4f}"
                    )

            return True
        else:
            print_error(f"Request falló: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def main():
    print_header("🔬 TEST RÁPIDO DE ENDPOINT SHAP")
    print_info(f"Backend: {BASE_URL}")
    print_info(f"Game ID: {GAME_ID[:30]}...")

    results = []

    # Test 1: Login
    token = test_login()
    results.append(("Login", token is not None))

    if not token:
        print_error("No se pudo obtener token. Abortando tests.")
        return

    # Test 2: All SHAP values
    results.append(("Query completa", test_all_shap_values(token)))

    # Test 3: Specific move
    results.append(("Move específico", test_specific_move(token)))

    # Test 4: Top N
    results.append(("Top N features", test_top_n(token)))

    # Resumen
    print_header("📊 RESUMEN DE TESTS")
    for name, passed in results:
        icon = f"{GREEN}✅" if passed else f"{RED}❌"
        status = "PASS" if passed else "FAIL"
        print(f"{icon} {name:<20} {status}{RESET}")

    all_passed = all(passed for _, passed in results)
    print(f"\n{BLUE}{'='*80}{RESET}")
    if all_passed:
        print(f"{GREEN}✅ TODOS LOS TESTS PASARON{RESET}")
        print(f"{GREEN}✅ Sistema listo para Postman{RESET}")
    else:
        print(f"{RED}❌ ALGUNOS TESTS FALLARON{RESET}")
        print(f"{YELLOW}💡 Verifica que el backend esté corriendo{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")


if __name__ == "__main__":
    main()
