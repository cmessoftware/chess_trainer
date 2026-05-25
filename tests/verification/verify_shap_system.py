"""
Script final de verificación del sistema SHAP completo
Valida que todo esté funcionando correctamente
"""

import requests
import psycopg2
from collections import Counter

BASE_URL = "http://localhost:8000"
GREEN = "\033[92m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def check_database():
    """Verificar estado de la base de datos"""
    print(f"\n{BLUE}{'='*80}")
    print("1. VERIFICACIÓN DE BASE DE DATOS")
    print(f"{'='*80}{RESET}")

    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chess_trainer_db",
            user="chess",
            password="chess_pass",
        )
        cursor = conn.cursor()

        # Contar análisis
        cursor.execute("SELECT COUNT(*) FROM analysis_results")
        num_analyses = cursor.fetchone()[0]

        # Contar SHAP values
        cursor.execute("SELECT COUNT(*) FROM move_shap_values")
        num_shap = cursor.fetchone()[0]

        # Distribución error_labels
        cursor.execute(
            """
            SELECT error_label, COUNT(*) 
            FROM move_shap_values 
            WHERE error_label IS NOT NULL
            GROUP BY error_label
            ORDER BY COUNT(*) DESC
        """
        )
        distribution = cursor.fetchall()
        total = sum(count for _, count in distribution)

        # Verificar vista SQL
        cursor.execute("SELECT COUNT(*) FROM shap_values_with_games")
        num_view = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        print(f"\n{GREEN}✅ Base de datos conectada{RESET}")
        print(f"   - Análisis: {num_analyses}")
        print(f"   - SHAP values: {num_shap:,}")
        print(f"   - Vista SQL: {num_view:,} registros")

        if total > 0:
            print(f"\n📊 Distribución de error_labels:")
            for label, count in distribution:
                pct = (count / total) * 100
                print(f"   {label:<15} {count:>6,} ({pct:>5.1f}%)")

            # Verificar distribución realista
            good_pct = next(
                (
                    count / total * 100
                    for label, count in distribution
                    if label == "good"
                ),
                0,
            )
            if 75 <= good_pct <= 85:
                print(
                    f"\n{GREEN}✅ Distribución realista (good: {good_pct:.1f}%){RESET}"
                )
            else:
                print(f"\n{RED}⚠️  Distribución anormal (good: {good_pct:.1f}%){RESET}")
        else:
            print(f"\n{RED}❌ No hay SHAP values con error_labels{RESET}")
            return False

        return True

    except Exception as e:
        print(f"\n{RED}❌ Error en base de datos: {e}{RESET}")
        return False


def check_api():
    """Verificar que API esté funcionando"""
    print(f"\n{BLUE}{'='*80}")
    print("2. VERIFICACIÓN DE API")
    print(f"{'='*80}{RESET}")

    try:
        # Test health
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print(f"\n{GREEN}✅ API respondiendo en {BASE_URL}{RESET}")
        else:
            print(f"\n{RED}❌ API no responde (status: {response.status_code}){RESET}")
            return False

        # Test login
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"username": "admin", "password": "admin123"},
        )

        if response.status_code == 200:
            token = response.json()["access_token"]
            print(f"{GREEN}✅ Login funcional{RESET}")
            return token
        else:
            print(f"{RED}❌ Login falló (status: {response.status_code}){RESET}")
            return None

    except Exception as e:
        print(f"\n{RED}❌ Error conectando a API: {e}{RESET}")
        return None


def check_endpoint(token):
    """Verificar endpoint de SHAP"""
    print(f"\n{BLUE}{'='*80}")
    print("3. VERIFICACIÓN DE ENDPOINT SHAP")
    print(f"{'='*80}{RESET}")

    try:
        # Obtener un game_id
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
            SELECT DISTINCT game_id, COUNT(*) as count
            FROM shap_values_with_games
            GROUP BY game_id
            ORDER BY COUNT(*) DESC
            LIMIT 1
        """
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            print(f"{RED}❌ No hay games con SHAP values{RESET}")
            return False

        game_id, shap_count = result
        print(f"\n📋 Game de prueba: {game_id[:30]}... ({shap_count} SHAP values)")

        # Test 1: Query completa
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/analysis/shap/game/{game_id}", headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print(
                f"\n{GREEN}✅ Endpoint funcional: {len(data)} SHAP values obtenidos{RESET}"
            )

            # Verificar estructura
            if data:
                first = data[0]
                required_fields = [
                    "shap_id",
                    "analysis_id",
                    "game_id",
                    "username",
                    "error_label",
                    "move_number",
                    "feature_name",
                    "shap_value",
                ]

                missing = [f for f in required_fields if f not in first]
                if not missing:
                    print(f"{GREEN}✅ Estructura de respuesta correcta{RESET}")
                else:
                    print(f"{RED}❌ Campos faltantes: {missing}{RESET}")
                    return False

                # Verificar error_labels
                error_labels = [item["error_label"] for item in data]
                label_counts = Counter(error_labels)
                print(f"\n📊 Distribución en respuesta:")
                for label, count in label_counts.most_common():
                    pct = (count / len(data)) * 100
                    print(f"   {label:<15} {count:>5} ({pct:>5.1f}%)")
        else:
            print(f"\n{RED}❌ Endpoint falló (status: {response.status_code}){RESET}")
            print(response.text)
            return False

        # Test 2: Filtro por move_number
        response = requests.get(
            f"{BASE_URL}/api/analysis/shap/game/{game_id}?move_number=5",
            headers=headers,
        )

        if response.status_code == 200:
            data = response.json()
            print(
                f"\n{GREEN}✅ Filtro por move_number funcional: {len(data)} features{RESET}"
            )
        else:
            print(f"\n{RED}❌ Filtro por move_number falló{RESET}")
            return False

        # Test 3: Top N
        response = requests.get(
            f"{BASE_URL}/api/analysis/shap/game/{game_id}?top_n=3", headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            print(f"{GREEN}✅ Filtro top_n funcional: {len(data)} SHAP values{RESET}")
        else:
            print(f"{RED}❌ Filtro top_n falló{RESET}")
            return False

        return True

    except Exception as e:
        print(f"\n{RED}❌ Error verificando endpoint: {e}{RESET}")
        return False


def main():
    print(f"\n{BLUE}{'='*80}")
    print("🔬 VERIFICACIÓN COMPLETA DEL SISTEMA SHAP")
    print(f"{'='*80}{RESET}")

    results = []

    # 1. Base de datos
    results.append(("Base de datos", check_database()))

    # 2. API
    token = check_api()
    results.append(("API", token is not None))

    # 3. Endpoint SHAP
    if token:
        results.append(("Endpoint SHAP", check_endpoint(token)))
    else:
        results.append(("Endpoint SHAP", False))

    # Resumen
    print(f"\n{BLUE}{'='*80}")
    print("📊 RESUMEN DE VERIFICACIÓN")
    print(f"{'='*80}{RESET}")

    for name, status in results:
        icon = f"{GREEN}✅" if status else f"{RED}❌"
        print(f"\n{icon} {name}: {'FUNCIONAL' if status else 'FALLÓ'}{RESET}")

    all_passed = all(status for _, status in results)

    print(f"\n{BLUE}{'='*80}{RESET}")
    if all_passed:
        print(f"{GREEN}✅ SISTEMA SHAP COMPLETAMENTE FUNCIONAL{RESET}")
        print(f"{GREEN}✅ Datos confiables basados en distribución real{RESET}")
        print(f"{GREEN}✅ Endpoint API listo para uso en Postman/UI{RESET}")
    else:
        print(f"{RED}❌ SISTEMA SHAP CON ERRORES{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")


if __name__ == "__main__":
    main()
