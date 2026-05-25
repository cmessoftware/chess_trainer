"""
Script de prueba para el Sistema de Reportes Personalizados Asíncronos
Verifica la integración completa entre backend y frontend
"""

import requests
import time
import json
import os
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8000"
TEST_PLAYER = "test_user_report_system"
TEST_FILES_DIR = "test_data"

class ReportsSystemTester:
    def __init__(self):
        self.api_base = API_BASE_URL
        self.session = requests.Session()
        self.current_job_id = None
        
    def log(self, message, level="INFO"):
        """Log con timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_api_health(self):
        """Verificar que la API esté funcionando"""
        self.log("🏥 Verificando salud de la API...")
        
        try:
            response = self.session.get(f"{self.api_base}/health")
            if response.status_code == 200:
                self.log("✅ API funcionando correctamente")
                return True
            else:
                self.log(f"❌ API respondió con código {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Error conectando con API: {e}", "ERROR")
            return False
    
    def test_notifications_api(self):
        """Probar API de notificaciones"""
        self.log("🔔 Probando API de notificaciones...")
        
        try:
            # Crear notificación de prueba
            response = self.session.post(f"{self.api_base}/api/notifications/test")
            
            if response.status_code == 200:
                self.log("✅ Notificación de prueba creada")
                
                # Obtener notificaciones
                response = self.session.get(f"{self.api_base}/api/notifications/")
                if response.status_code == 200:
                    notifications = response.json()
                    self.log(f"✅ Obtenidas {len(notifications)} notificaciones")
                    return True
                    
            self.log("❌ Error en API de notificaciones", "ERROR")
            return False
            
        except Exception as e:
            self.log(f"❌ Error probando notificaciones: {e}", "ERROR")
            return False
    
    def test_player_verification(self):
        """Probar verificación de jugador"""
        self.log(f"👤 Verificando jugador '{TEST_PLAYER}'...")
        
        try:
            # Usar endpoint de chess para verificar jugador
            response = self.session.get(f"{self.api_base}/chess/player/{TEST_PLAYER}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                games_count = stats.get("games_count", 0)
                self.log(f"✅ Jugador encontrado con {games_count} partidas")
                return {"exists": True, "games": games_count}
            elif response.status_code == 404:
                self.log("⚠️ Jugador no encontrado en BD", "WARN")
                return {"exists": False, "games": 0}
            else:
                self.log(f"❌ Error verificando jugador: {response.status_code}", "ERROR")
                return {"exists": False, "games": 0}
                
        except Exception as e:
            self.log(f"❌ Error verificando jugador: {e}", "ERROR")
            return {"exists": False, "games": 0}
    
    def test_report_generation_existing(self):
        """Probar generación de reporte para jugador existente"""
        self.log("📊 Probando generación de reporte (jugador existente)...")
        
        # Verificar si el jugador existe
        player_info = self.test_player_verification()
        
        if not player_info["exists"]:
            self.log("⚠️ Saltando test - jugador no existe en BD", "WARN")
            return False
        
        try:
            # Generar reporte
            request_data = {
                "player_name": TEST_PLAYER,
                "min_games": 10,  # Mínimo bajo para testing
                "include_survivorship": True,
                "output_format": "markdown"
            }
            
            response = self.session.post(
                f"{self.api_base}/api/reports/generate",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.current_job_id = data["job_id"]
                estimated_minutes = data.get("estimated_time_minutes", 1)
                
                self.log(f"✅ Job creado: {self.current_job_id}")
                self.log(f"⏱️ Tiempo estimado: {estimated_minutes} minutos")
                
                return self.poll_job_status()
                
            else:
                error_detail = response.json().get("detail", "Error desconocido")
                self.log(f"❌ Error generando reporte: {error_detail}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error en test de generación: {e}", "ERROR")
            return False
    
    def test_report_generation_upload(self):
        """Probar generación de reporte desde upload"""
        self.log("📤 Probando generación de reporte (desde upload)...")
        
        # Buscar archivos PGN de prueba
        test_pgn_files = self.find_test_pgn_files()
        
        if not test_pgn_files:
            self.log("⚠️ No se encontraron archivos PGN de prueba", "WARN")
            return False
        
        try:
            request_data = {
                "player_name": f"{TEST_PLAYER}_upload",
                "pgn_files": test_pgn_files[:2],  # Máximo 2 archivos para testing
                "source": "test_upload",
                "min_games": 5,
                "include_survivorship": True
            }
            
            response = self.session.post(
                f"{self.api_base}/api/reports/generate-from-upload",
                json=request_data
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data["job_id"]
                files_to_process = data.get("files_to_process", 0)
                
                self.log(f"✅ Job de upload creado: {job_id}")
                self.log(f"📁 Archivos a procesar: {files_to_process}")
                
                return self.poll_job_status(job_id)
                
            else:
                error_detail = response.json().get("detail", "Error desconocido")
                self.log(f"❌ Error en upload: {error_detail}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error en test de upload: {e}", "ERROR")
            return False
    
    def poll_job_status(self, job_id=None):
        """Polling del estado del job"""
        if not job_id:
            job_id = self.current_job_id
            
        if not job_id:
            self.log("❌ No hay job ID para hacer polling", "ERROR")
            return False
        
        self.log(f"🔄 Iniciando polling para job {job_id}...")
        max_iterations = 60  # 5 minutos máximo con polling cada 5 segundos
        
        for i in range(max_iterations):
            try:
                response = self.session.get(f"{self.api_base}/api/reports/status/{job_id}")
                
                if response.status_code == 200:
                    status = response.json()
                    job_status = status["status"]
                    progress = status.get("progress_percentage", 0)
                    
                    if job_status == "pending":
                        self.log(f"⏳ Job pendiente... ({progress}%)")
                    elif job_status == "processing":
                        self.log(f"🔄 Procesando... ({progress}%)")
                    elif job_status == "completed":
                        self.log(f"✅ Job completado! ({progress}%)")
                        report_path = status.get("report_path")
                        if report_path:
                            self.log(f"📄 Reporte disponible en: {report_path}")
                        return self.test_report_download(job_id)
                    elif job_status == "failed":
                        error_message = status.get("error_message", "Error desconocido")
                        self.log(f"❌ Job falló: {error_message}", "ERROR")
                        return False
                    
                    time.sleep(5)  # Esperar 5 segundos antes del siguiente poll
                    
                else:
                    self.log(f"❌ Error obteniendo estado: {response.status_code}", "ERROR")
                    return False
                    
            except Exception as e:
                self.log(f"❌ Error en polling: {e}", "ERROR")
                return False
        
        self.log("⏰ Timeout esperando completar job", "WARN")
        return False
    
    def test_report_download(self, job_id):
        """Probar descarga de reporte"""
        self.log(f"💾 Probando descarga de reporte {job_id}...")
        
        try:
            response = self.session.get(f"{self.api_base}/api/reports/download/{job_id}")
            
            if response.status_code == 200:
                # Verificar que es un archivo válido
                content_length = len(response.content)
                content_type = response.headers.get("content-type", "")
                
                if content_length > 0:
                    self.log(f"✅ Reporte descargado: {content_length} bytes")
                    self.log(f"📋 Content-Type: {content_type}")
                    
                    # Guardar archivo de prueba
                    test_filename = f"test_report_{job_id[:8]}.md"
                    with open(test_filename, 'wb') as f:
                        f.write(response.content)
                    self.log(f"💾 Guardado como: {test_filename}")
                    
                    return True
                else:
                    self.log("❌ Archivo vacío descargado", "ERROR")
                    return False
                    
            else:
                error_detail = response.json().get("detail", "Error desconocido")
                self.log(f"❌ Error descargando: {error_detail}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error en descarga: {e}", "ERROR")
            return False
    
    def test_recent_reports_list(self):
        """Probar listado de reportes recientes"""
        self.log("📋 Probando listado de reportes recientes...")
        
        try:
            response = self.session.get(f"{self.api_base}/api/reports/list")
            
            if response.status_code == 200:
                data = response.json()
                reports = data.get("reports", [])
                
                self.log(f"✅ Obtenidos {len(reports)} reportes recientes")
                
                for report in reports[:3]:  # Mostrar solo los primeros 3
                    player = report.get("player_name", "N/A")
                    status = report.get("status", "N/A")
                    created = report.get("created_at", "N/A")
                    self.log(f"  📊 {player} - {status} - {created}")
                
                return True
            else:
                self.log(f"❌ Error obteniendo lista: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Error en listado: {e}", "ERROR")
            return False
    
    def find_test_pgn_files(self):
        """Buscar archivos PGN de prueba"""
        possible_directories = [
            "test_data",
            "data/games/personal",
            "data/games/test", 
            "src/test_data"
        ]
        
        pgn_files = []
        
        for directory in possible_directories:
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if file.endswith('.pgn'):
                        full_path = os.path.join(directory, file)
                        if os.path.getsize(full_path) > 100:  # Al menos 100 bytes
                            pgn_files.append(full_path)
                            if len(pgn_files) >= 3:  # Máximo 3 archivos para testing
                                break
                
                if pgn_files:
                    break
        
        return pgn_files
    
    def run_complete_test_suite(self):
        """Ejecutar suite completo de pruebas"""
        self.log("🚀 Iniciando suite completo de pruebas del Sistema de Reportes Personalizados")
        self.log("=" * 80)
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("Notifications API", self.test_notifications_api),
            ("Player Verification", lambda: self.test_player_verification()["exists"]),
            ("Recent Reports List", self.test_recent_reports_list),
            ("Report Generation (Existing)", self.test_report_generation_existing),
            # ("Report Generation (Upload)", self.test_report_generation_upload),  # Comentado por requerir archivos PGN
        ]
        
        results = []
        
        for test_name, test_func in tests:
            self.log("")
            self.log(f"🧪 Ejecutando: {test_name}")
            self.log("-" * 50)
            
            try:
                result = test_func()
                results.append((test_name, result))
                
                if result:
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                self.log(f"💥 {test_name}: ERROR - {e}", "ERROR")
                results.append((test_name, False))
        
        # Resumen final
        self.log("")
        self.log("📊 RESUMEN DE RESULTADOS")
        self.log("=" * 80)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{status} - {test_name}")
        
        self.log("")
        self.log(f"🎯 TOTAL: {passed}/{total} pruebas pasaron")
        
        if passed == total:
            self.log("🎉 ¡Todos los tests pasaron! El sistema está funcionando correctamente.")
        else:
            self.log(f"⚠️ {total - passed} tests fallaron. Revisar logs arriba.", "WARN")
        
        return passed == total

def main():
    """Función principal"""
    print("🎯 Chess Trainer - Test del Sistema de Reportes Personalizados")
    print("=" * 80)
    
    tester = ReportsSystemTester()
    success = tester.run_complete_test_suite()
    
    if success:
        print("\n🎉 ¡Suite de pruebas completado exitosamente!")
        exit(0)
    else:
        print("\n❌ Algunas pruebas fallaron. Ver logs para detalles.")
        exit(1)

if __name__ == "__main__":
    main()