#!/usr/bin/env python3
"""
Script para inicializar y probar el frontend React de Chess Trainer
"""

import os
import subprocess
import sys
import time
import webbrowser


def check_node_npm():
    """Verificar que Node.js y npm estén instalados"""
    print("🔍 Verificando Node.js y npm...")

    try:
        # Verificar Node.js
        node_version = subprocess.check_output(["node", "--version"], text=True).strip()
        print(f"✅ Node.js {node_version} encontrado")

        # Verificar npm
        npm_version = subprocess.check_output(["npm", "--version"], text=True).strip()
        print(f"✅ npm {npm_version} encontrado")

        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js o npm no encontrados")
        print("   Instala Node.js desde: https://nodejs.org/")
        return False


def install_frontend_dependencies():
    """Instalar dependencias del frontend"""
    print("📦 Instalando dependencias del frontend...")

    frontend_dir = os.path.join(os.path.dirname(__file__), "src", "frontend")

    if not os.path.exists(frontend_dir):
        print(f"❌ Directorio del frontend no encontrado: {frontend_dir}")
        return False

    try:
        # Cambiar al directorio del frontend
        original_dir = os.getcwd()
        os.chdir(frontend_dir)

        # Instalar dependencias
        print("   Ejecutando npm install...")
        subprocess.check_call(["npm", "install"], stdout=subprocess.DEVNULL)

        print("✅ Dependencias del frontend instaladas")

        # Volver al directorio original
        os.chdir(original_dir)
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Error instalando dependencias del frontend: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def start_frontend_server():
    """Iniciar el servidor de desarrollo del frontend"""
    print("🚀 Iniciando servidor de desarrollo React...")

    frontend_dir = os.path.join(os.path.dirname(__file__), "src", "frontend")

    try:
        # Cambiar al directorio del frontend
        os.chdir(frontend_dir)

        # Iniciar servidor de desarrollo
        process = subprocess.Popen(["npm", "run", "dev"])

        print("🔄 Esperando que el servidor esté listo...")
        time.sleep(8)

        return process
    except Exception as e:
        print(f"❌ Error iniciando servidor de desarrollo: {e}")
        return None


def open_browser():
    """Abrir el navegador con la aplicación"""
    print("🌐 Abriendo aplicación en el navegador...")

    try:
        webbrowser.open("http://localhost:5173")
        print("✅ Navegador abierto")
    except Exception as e:
        print(f"⚠️ No se pudo abrir el navegador automáticamente: {e}")
        print("   Abre manualmente: http://localhost:5173")


def show_frontend_info():
    """Mostrar información sobre el frontend"""
    print("\n🎯 Chess Trainer - Frontend React")
    print("=" * 40)
    print("🌐 URL: http://localhost:5173")
    print("⚛️ Framework: React 19 + Vite")
    print("🎨 UI: Material-UI")
    print("♟️ Chess: chess.js + react-chessboard")
    print("\n💡 Usuarios de prueba:")
    print("   - admin/admin123 (acceso completo)")
    print("   - analista/analista123 (análisis + navegación)")
    print("   - usuario/usuario123 (navegación básica)")
    print("\n📋 Funcionalidades disponibles:")
    print("   ✅ Sistema de autenticación JWT")
    print("   ✅ Navegación protegida por roles")
    print("   ✅ Tablero de ajedrez interactivo")
    print("   ✅ Sistema de logging progresivo")
    print("   ⏳ Navegador de partidas (próximamente)")
    print("   ⏳ Análisis con Stockfish (próximamente)")
    print("\nPresiona Ctrl+C para detener el servidor...")


def main():
    """Función principal"""
    print("⚛️ Chess Trainer - Inicialización de Frontend React")
    print("=" * 50)

    # Verificar herramientas necesarias
    if not check_node_npm():
        return

    # Instalar dependencias
    if not install_frontend_dependencies():
        return

    # Iniciar servidor
    server_process = start_frontend_server()
    if not server_process:
        return

    try:
        # Mostrar información
        show_frontend_info()

        # Abrir navegador
        open_browser()

        # Mantener el servidor corriendo
        server_process.wait()

    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servidor de desarrollo...")
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    main()
