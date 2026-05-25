#!/usr/bin/env python3
"""
Script para inicializar y probar la API de Chess Trainer
"""

import sys
import os
import subprocess
import requests
import time


def install_dependencies():
    """Instalar dependencias de la API"""
    print("📦 Instalando dependencias de la API...")

    api_dir = os.path.join(os.path.dirname(__file__), "src", "api")
    requirements_file = os.path.join(api_dir, "requirements.txt")

    if os.path.exists(requirements_file):
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "-r", requirements_file]
            )
            print("✅ Dependencias instaladas correctamente")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando dependencias: {e}")
            return False
    else:
        print(f"❌ No se encontró requirements.txt en {requirements_file}")
        return False


def start_api_server():
    """Iniciar el servidor de la API"""
    print("🚀 Iniciando servidor de la API...")

    api_dir = os.path.join(os.path.dirname(__file__), "src", "api")

    try:
        # Cambiar al directorio de la API
        os.chdir(api_dir)

        # Iniciar uvicorn
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ]
        )

        print("🔄 Esperando que la API esté lista...")
        time.sleep(5)

        return process
    except Exception as e:
        print(f"❌ Error iniciando servidor: {e}")
        return None


def test_api_endpoints():
    """Probar endpoints básicos de la API"""
    print("🔍 Probando endpoints de la API...")

    base_url = "http://localhost:8000"

    try:
        # Probar endpoint raíz
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Endpoint raíz funcionando")
            print(f"   Respuesta: {response.json()}")
        else:
            print(f"❌ Endpoint raíz falló: {response.status_code}")

        # Probar health check
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check funcionando")
        else:
            print(f"❌ Health check falló: {response.status_code}")

        # Probar login con usuario demo
        login_data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{base_url}/auth/login", json=login_data, timeout=10)
        if response.status_code == 200:
            print("✅ Login funcionando")
            token_data = response.json()
            print(f"   Token obtenido para usuario: {token_data['user']['username']}")
            return token_data["access_token"]
        else:
            print(f"❌ Login falló: {response.status_code}")
            print(f"   Error: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error conectando con la API: {e}")
        return None

    return None


def test_protected_endpoints(token):
    """Probar endpoints protegidos"""
    if not token:
        print("⚠️ Saltando pruebas de endpoints protegidos (sin token)")
        return

    print("🔒 Probando endpoints protegidos...")

    base_url = "http://localhost:8000"
    headers = {"Authorization": f"Bearer {token}"}

    try:
        # Probar obtener partida
        response = requests.get(
            f"{base_url}/chess/games/1", headers=headers, timeout=10
        )
        if response.status_code == 200:
            print("✅ Endpoint de partida funcionando")
            game_data = response.json()
            print(f"   Partida: {game_data['white']} vs {game_data['black']}")
        else:
            print(f"❌ Endpoint de partida falló: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error en endpoints protegidos: {e}")


def main():
    """Función principal"""
    print("🎯 Chess Trainer - Inicialización de API FastAPI")
    print("=" * 50)

    # Instalar dependencias
    if not install_dependencies():
        return

    # Iniciar servidor
    server_process = start_api_server()
    if not server_process:
        return

    try:
        # Probar endpoints
        token = test_api_endpoints()
        test_protected_endpoints(token)

        print("\n🎉 API iniciada correctamente!")
        print("📖 Documentación disponible en: http://localhost:8000/docs")
        print("🔄 ReDoc disponible en: http://localhost:8000/redoc")
        print("\n💡 Usuarios de prueba:")
        print("   - admin/admin123 (acceso completo)")
        print("   - analista/analista123 (análisis + navegación)")
        print("   - usuario/usuario123 (navegación básica)")
        print("\nPresiona Ctrl+C para detener el servidor...")

        # Mantener el servidor corriendo
        server_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor...")
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    main()
