#!/usr/bin/env python3
"""
Script maestro para inicializar Chess Trainer con React + FastAPI
Sistema completo: Frontend moderno + Backend ML + Base de datos PostgreSQL
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
import signal
from pathlib import Path


class ChessTrainerLauncher:
    """Lanzador principal de Chess Trainer"""

    def __init__(self):
        self.api_process = None
        self.frontend_process = None
        self.running = True

    def setup_signal_handler(self):
        """Configurar manejador de señales para cierre limpio"""

        def signal_handler(signum, frame):
            print(f"\n🛑 Recibida señal {signum}. Cerrando servicios...")
            self.stop_services()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def check_dependencies(self):
        """Verificar dependencias del sistema"""
        print("🔍 Verificando dependencias del sistema...")

        # Verificar Python
        python_version = sys.version_info
        if python_version.major < 3 or (
            python_version.major == 3 and python_version.minor < 8
        ):
            print("❌ Se requiere Python 3.8 o superior")
            return False
        print(f"✅ Python {python_version.major}.{python_version.minor} encontrado")

        # Verificar conda y entorno chess_trainer
        try:
            conda_envs = subprocess.check_output(
                ["conda", "env", "list"], text=True, shell=True
            )
            if "chess_trainer" in conda_envs:
                print("✅ Entorno conda 'chess_trainer' encontrado")
            else:
                print("❌ Entorno conda 'chess_trainer' no encontrado")
                print(
                    "   Crea el entorno con: conda create -n chess_trainer python=3.9"
                )
                return False
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Conda no encontrado. Instálalo desde: https://www.anaconda.com/")
            return False

        # Verificar Node.js (con diferentes comandos para Windows)
        node_commands = ["node", "node.exe"]
        node_found = False
        for cmd in node_commands:
            try:
                node_version = subprocess.check_output(
                    [cmd, "--version"], text=True, shell=True
                ).strip()
                print(f"✅ Node.js {node_version} encontrado")
                node_found = True
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        if not node_found:
            print("❌ Node.js no encontrado. Instálalo desde: https://nodejs.org/")
            return False

        # Verificar npm (con diferentes comandos para Windows)
        npm_commands = ["npm", "npm.cmd"]
        npm_found = False
        for cmd in npm_commands:
            try:
                npm_version = subprocess.check_output(
                    [cmd, "--version"], text=True, shell=True
                ).strip()
                print(f"✅ npm {npm_version} encontrado")
                npm_found = True
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        if not npm_found:
            print("❌ npm no encontrado")
            return False

        return True

    def install_api_dependencies(self):
        """Instalar dependencias de la API usando conda"""
        print("📦 Instalando dependencias de FastAPI en entorno conda...")

        api_requirements = Path(__file__).parent / "src" / "api" / "requirements.txt"

        if not api_requirements.exists():
            print(f"❌ No se encontró {api_requirements}")
            return False

        try:
            # Usar conda run para ejecutar en el entorno chess_trainer
            subprocess.check_call(
                [
                    "conda",
                    "run",
                    "-n",
                    "chess_trainer",
                    "pip",
                    "install",
                    "-r",
                    str(api_requirements),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
            )
            print("✅ Dependencias de FastAPI instaladas en conda")
            return True
        except subprocess.CalledProcessError:
            print("❌ Error instalando dependencias de FastAPI")
            return False

    def install_frontend_dependencies(self):
        """Instalar dependencias del frontend"""
        print("📦 Instalando dependencias de React...")

        frontend_dir = Path(__file__).parent / "src" / "frontend"

        if not frontend_dir.exists():
            print(f"❌ Directorio del frontend no encontrado")
            return False

        try:
            original_dir = os.getcwd()
            os.chdir(frontend_dir)

            # Usar npm.cmd en Windows para mayor compatibilidad
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            subprocess.check_call(
                [npm_cmd, "install"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
            )
            print("✅ Dependencias de React instaladas")

            os.chdir(original_dir)
            return True
        except subprocess.CalledProcessError:
            print("❌ Error instalando dependencias de React")
            return False

    def start_api_service(self):
        """Iniciar servicio de FastAPI usando conda"""
        print("🚀 Iniciando FastAPI en puerto 8000 con conda...")

        api_dir = Path(__file__).parent / "src" / "api"

        try:
            original_dir = os.getcwd()
            os.chdir(api_dir)

            # Usar conda run para ejecutar uvicorn en el entorno chess_trainer
            self.api_process = subprocess.Popen(
                [
                    "conda",
                    "run",
                    "-n",
                    "chess_trainer",
                    "uvicorn",
                    "main:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                    "--reload",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
            )

            os.chdir(original_dir)
            print("✅ FastAPI iniciado con conda")
            return True
        except Exception as e:
            print(f"❌ Error iniciando FastAPI: {e}")
            return False

    def start_frontend_service(self):
        """Iniciar servicio de React"""
        print("⚛️ Iniciando React en puerto 5173...")

        frontend_dir = Path(__file__).parent / "src" / "frontend"

        try:
            original_dir = os.getcwd()
            os.chdir(frontend_dir)

            # Usar npm.cmd en Windows para mayor compatibilidad
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            self.frontend_process = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
            )

            os.chdir(original_dir)
            print("✅ React iniciado")
            return True
        except Exception as e:
            print(f"❌ Error iniciando React: {e}")
            return False

    def wait_for_services(self):
        """Esperar a que los servicios estén listos"""
        print("⏳ Esperando que los servicios estén listos...")
        time.sleep(10)  # Dar tiempo suficiente para que inicien

    def open_application(self):
        """Abrir la aplicación en el navegador"""
        print("🌐 Abriendo Chess Trainer en el navegador...")
        try:
            webbrowser.open("http://localhost:5173")
            print("✅ Aplicación abierta")
        except Exception:
            print("⚠️ Abre manualmente: http://localhost:5173")

    def show_application_info(self):
        """Mostrar información de la aplicación"""
        print("\n🎯 CHESS TRAINER - ARQUITECTURA REACT + FASTAPI")
        print("=" * 55)
        print("📊 ESTADO DE SERVICIOS:")
        print("   ⚛️ Frontend React:  http://localhost:5173")
        print("   🚀 Backend FastAPI: http://localhost:8000 (conda: chess_trainer)")
        print("   📖 API Docs:        http://localhost:8000/docs")

        print("\n🎮 FUNCIONALIDADES IMPLEMENTADAS:")
        print("   ✅ Arquitectura React 19 + FastAPI + PostgreSQL")
        print("   ✅ Sistema de autenticación JWT con roles")
        print("   ✅ Tablero de ajedrez interactivo con navegación")
        print("   ✅ Navegador de partidas con filtros avanzados")
        print("   ✅ Sistema ML con MLflow para predicciones")
        print("   ✅ Pipeline completo de análisis de partidas")
        print("   ✅ API REST con documentación automática")
        print("   ✅ Sistema de logging y análisis de eventos")

        print("\n👥 USUARIOS DE PRUEBA:")
        print("   🔑 admin/admin123     → Acceso completo al sistema")
        print("   📊 analista/analista123 → Análisis ML + navegación")
        print("   👤 usuario/usuario123   → Navegación y análisis básico")

        print("\n🎯 FUNCIONALIDADES PRINCIPALES:")
        print("   🏠 Dashboard principal con navegación")
        print("   ♟️  Tablero interactivo con análisis Stockfish")
        print("   🎮 Navegador de partidas con paginación")
        print("   📊 Sistema ML con 6 fases de análisis")
        print("   📈 Seguimiento de experimentos con MLflow")
        print("   🗃️  Base de datos PostgreSQL integrada")

        print("\n🚀 DESARROLLO ACTUAL:")
        print("   📱 Frontend: React 19 + TypeScript + Vite + Material-UI")
        print("   🔥 Backend: FastAPI + PostgreSQL + MLflow + Stockfish")
        print("   🧠 ML: scikit-learn + chess.js + python-chess")
        print("   🐳 Deploy: Docker + Docker Compose + Conda")

        print("\n⌨️ CONTROLES:")
        print("   Ctrl+C para detener todos los servicios")
        print("=" * 55)

    def monitor_services(self):
        """Monitorear los servicios en ejecución"""
        while self.running:
            try:
                # Verificar si los procesos están vivos
                if self.api_process and self.api_process.poll() is not None:
                    print("⚠️ El servicio de FastAPI se detuvo inesperadamente")
                    break

                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("⚠️ El servicio de React se detuvo inesperadamente")
                    break

                time.sleep(5)  # Verificar cada 5 segundos

            except KeyboardInterrupt:
                break

    def stop_services(self):
        """Detener todos los servicios"""
        print("🛑 Deteniendo servicios...")

        self.running = False

        if self.frontend_process:
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
                print("✅ React detenido")
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
                print("🔥 React forzado a cerrar")

        if self.api_process:
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
                print("✅ FastAPI detenido")
            except subprocess.TimeoutExpired:
                self.api_process.kill()
                print("🔥 FastAPI forzado a cerrar")

        print("🏁 Todos los servicios detenidos")

    def run(self):
        """Ejecutar la aplicación completa"""
        print("🎯 CHESS TRAINER - SISTEMA COMPLETO REACT + FASTAPI + ML")
        print("=" * 60)

        # Configurar manejador de señales
        self.setup_signal_handler()

        # Verificar dependencias
        if not self.check_dependencies():
            return False

        # Instalar dependencias
        if not self.install_api_dependencies():
            return False

        if not self.install_frontend_dependencies():
            return False

        # Iniciar servicios
        if not self.start_api_service():
            return False

        if not self.start_frontend_service():
            return False

        # Esperar que estén listos
        self.wait_for_services()

        # Abrir aplicación
        self.open_application()

        # Mostrar información
        self.show_application_info()

        try:
            # Monitorear servicios
            self.monitor_services()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_services()

        return True


def main():
    """Función principal"""
    launcher = ChessTrainerLauncher()
    success = launcher.run()

    if success:
        print("\n🎉 Chess Trainer ejecutado exitosamente!")
    else:
        print("\n❌ Error ejecutando Chess Trainer")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
