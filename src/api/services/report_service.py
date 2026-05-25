"""
Servicio para generación y manejo de reportes de jugadores
Integra con los scripts genéricos del sistema
"""

from typing import Dict, List, Optional, Tuple
import os
import json
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path

class ReportService:
    def __init__(self):
        self.reports_base_dir = Path("reports")
        self.api_reports_dir = self.reports_base_dir / "api_generated"
        self.scripts_dir = Path("src/scripts")
        
        # Crear directorios si no existen
        self.api_reports_dir.mkdir(parents=True, exist_ok=True)
    
    async def validate_player_exists(self, player_name: str) -> Dict:
        """
        Validar que un jugador existe en la base de datos
        
        Args:
            player_name: Nombre del jugador a verificar
        
        Returns:
            Dict con información del jugador
        """
        try:
            check_script = self.scripts_dir / "check_player_data.py"
            
            if not check_script.exists():
                return {
                    "success": False,
                    "error": f"Script de verificación no encontrado: {check_script}",
                    "exists": False
                }
            
            # Ejecutar script de verificación
            result = subprocess.run(
                ["python", str(check_script), player_name, "--json"],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                # Buscar línea JSON en la salida
                output_lines = result.stdout.strip().split('\n')
                for line in output_lines:
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        try:
                            player_data = json.loads(line)
                            return {
                                "success": True,
                                "exists": player_data.get("exists", False),
                                "games_count": player_data.get("games_count", 0),
                                "player_data": player_data
                            }
                        except json.JSONDecodeError:
                            continue
                
                # Si no encontró JSON, asumir que no existe
                return {
                    "success": True,
                    "exists": False,
                    "games_count": 0,
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": f"Error ejecutando verificación: {result.stderr}",
                    "exists": False,
                    "returncode": result.returncode
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error en validación: {str(e)}",
                "exists": False
            }
    
    async def import_player_pgns(
        self, 
        player_name: str, 
        pgn_files: List[str],
        source: str = "uploaded"
    ) -> Dict:
        """
        Importar archivos PGN para un jugador
        
        Args:
            player_name: Nombre del jugador
            pgn_files: Lista de rutas de archivos PGN
            source: Fuente de los archivos (uploaded, external, etc.)
        
        Returns:
            Dict con resultado de la importación
        """
        try:
            import_script = self.scripts_dir / "import_player_pgns.py"
            
            if not import_script.exists():
                return {
                    "success": False,
                    "error": f"Script de importación no encontrado: {import_script}",
                    "games_imported": 0
                }
            
            # Verificar que todos los archivos existen
            missing_files = [f for f in pgn_files if not os.path.exists(f)]
            if missing_files:
                return {
                    "success": False,
                    "error": f"Archivos PGN no encontrados: {missing_files}",
                    "games_imported": 0
                }
            
            # Construir comando de importación
            cmd = [
                "python", str(import_script), 
                player_name,
                "--source", source,
                "--files"
            ] + pgn_files
            
            # Ejecutar importación
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                # Parsear salida para obtener estadísticas
                games_imported = self._extract_games_count(result.stdout)
                
                return {
                    "success": True,
                    "games_imported": games_imported,
                    "output": result.stdout,
                    "files_processed": len(pgn_files)
                }
            else:
                return {
                    "success": False,
                    "error": f"Error en importación: {result.stderr}",
                    "games_imported": 0,
                    "output": result.stdout
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error importando PGNs: {str(e)}",
                "games_imported": 0
            }
    
    async def generate_player_analysis(
        self,
        player_name: str,
        min_games: int = 50,
        include_tactical: bool = True,
        output_format: str = "markdown"
    ) -> Dict:
        """
        Generar análisis completo de un jugador
        
        Args:
            player_name: Nombre del jugador
            min_games: Mínimo número de partidas
            include_tactical: Incluir análisis táctico
            output_format: Formato de salida (markdown, pdf)
        
        Returns:
            Dict con resultado del análisis
        """
        try:
            analyze_script = self.scripts_dir / "analyze_player.py"
            
            if not analyze_script.exists():
                return {
                    "success": False,
                    "error": f"Script de análisis no encontrado: {analyze_script}",
                    "report_path": None
                }
            
            # Construir comando
            cmd = [
                "python", str(analyze_script),
                player_name,
                "--min-games", str(min_games),
                "--output-dir", str(self.api_reports_dir)
            ]
            
            if include_tactical:
                cmd.append("--include-tactical")
            
            # Ejecutar análisis
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                # Buscar archivo de reporte generado
                report_files = self._find_report_files(player_name)
                
                if report_files:
                    report_path = report_files[0]  # Más reciente
                    
                    # Convertir a PDF si es necesario
                    if output_format == "pdf":
                        pdf_path = await self._convert_to_pdf(report_path)
                        if pdf_path:
                            report_path = pdf_path
                    
                    return {
                        "success": True,
                        "report_path": report_path,
                        "output": result.stdout,
                        "format": output_format
                    }
                else:
                    return {
                        "success": False,
                        "error": "No se encontró archivo de reporte generado",
                        "output": result.stdout,
                        "report_path": None
                    }
            else:
                return {
                    "success": False,
                    "error": f"Error en análisis: {result.stderr}",
                    "output": result.stdout,
                    "report_path": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generando análisis: {str(e)}",
                "report_path": None
            }
    
    async def generate_survivorship_analysis(self, player_name: str) -> Dict:
        """
        Generar análisis de Survivorship Bias
        
        Args:
            player_name: Nombre del jugador
        
        Returns:
            Dict con resultado del análisis
        """
        try:
            survivorship_script = self.scripts_dir / "analyze_survivorship.py"
            
            if not survivorship_script.exists():
                return {
                    "success": False,
                    "error": f"Script de survivorship no encontrado: {survivorship_script}",
                    "report_path": None
                }
            
            # Ejecutar análisis de survivorship
            result = subprocess.run(
                ["python", str(survivorship_script), player_name],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                # Buscar archivo de reporte survivorship
                survivorship_files = self._find_survivorship_files(player_name)
                
                return {
                    "success": True,
                    "report_path": survivorship_files[0] if survivorship_files else None,
                    "output": result.stdout,
                    "analysis_completed": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Error en análisis survivorship: {result.stderr}",
                    "output": result.stdout,
                    "report_path": None
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error en survivorship: {str(e)}",
                "report_path": None
            }
    
    async def _convert_to_pdf(self, markdown_path: str) -> Optional[str]:
        """
        Convertir archivo Markdown a PDF
        
        Args:
            markdown_path: Ruta del archivo Markdown
        
        Returns:
            Ruta del archivo PDF si es exitoso
        """
        try:
            pdf_script = self.scripts_dir / "convert_md_to_pdf.py"
            
            if not pdf_script.exists():
                return None
            
            result = subprocess.run(
                ["python", str(pdf_script), markdown_path],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result.returncode == 0:
                # Buscar archivo PDF generado
                pdf_path = Path(markdown_path).with_suffix('.pdf')
                if pdf_path.exists():
                    return str(pdf_path)
            
            return None
            
        except Exception as e:
            print(f"Error convirtiendo a PDF: {e}")
            return None
    
    def _extract_games_count(self, output: str) -> int:
        """Extraer número de partidas importadas de la salida"""
        try:
            # Buscar patrones comunes en la salida
            lines = output.split('\n')
            for line in lines:
                line_lower = line.lower()
                if 'importadas' in line_lower or 'imported' in line_lower:
                    # Buscar números en la línea
                    import re
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        return int(numbers[-1])  # Último número encontrado
            
            return 0
        except:
            return 0
    
    def _find_report_files(self, player_name: str) -> List[str]:
        """Encontrar archivos de reporte para un jugador"""
        report_patterns = [
            f"*{player_name.lower()}*analysis*.md",
            f"*{player_name.lower()}*reporte*.md",
            f"{player_name.lower()}_*.md"
        ]
        
        found_files = []
        
        # Buscar en directorio de reportes API
        for pattern in report_patterns:
            found_files.extend(self.api_reports_dir.glob(pattern))
        
        # Buscar también en directorio base de reportes
        for pattern in report_patterns:
            found_files.extend(self.reports_base_dir.glob(pattern))
        
        # Ordenar por fecha de modificación (más reciente primero)
        found_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return [str(f) for f in found_files]
    
    def _find_survivorship_files(self, player_name: str) -> List[str]:
        """Encontrar archivos de análisis survivorship"""
        survivorship_patterns = [
            f"*{player_name.lower()}*survivorship*.md",
            f"*{player_name.lower()}*bias*.md"
        ]
        
        found_files = []
        
        for pattern in survivorship_patterns:
            found_files.extend(self.api_reports_dir.glob(pattern))
            found_files.extend(self.reports_base_dir.glob(pattern))
        
        # Ordenar por fecha de modificación
        found_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        return [str(f) for f in found_files]
    
    def get_recent_reports(self, limit: int = 10) -> List[Dict]:
        """
        Obtener reportes recientes generados
        
        Args:
            limit: Número máximo de reportes
        
        Returns:
            Lista de reportes con metadata
        """
        report_files = []
        
        # Buscar en directorio API
        for report_file in self.api_reports_dir.glob("*.md"):
            stat = report_file.stat()
            report_files.append({
                "path": str(report_file),
                "name": report_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime),
                "modified": datetime.fromtimestamp(stat.st_mtime),
                "type": "analysis" if "analysis" in report_file.name else "report"
            })
        
        # Ordenar por fecha de modificación
        report_files.sort(key=lambda x: x["modified"], reverse=True)
        
        return report_files[:limit]
    
    def cleanup_old_reports(self, days: int = 30) -> int:
        """
        Limpiar reportes antiguos
        
        Args:
            days: Días de antigüedad para eliminar
        
        Returns:
            Número de archivos eliminados
        """
        cutoff_timestamp = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for report_file in self.api_reports_dir.glob("*"):
            if report_file.is_file():
                if report_file.stat().st_mtime < cutoff_timestamp:
                    try:
                        report_file.unlink()
                        deleted_count += 1
                    except OSError:
                        pass  # Ignora errores de permisos
        
        return deleted_count

# Instancia global del servicio
_report_service = None

def get_report_service() -> ReportService:
    """Obtener instancia global del servicio de reportes"""
    global _report_service
    if _report_service is None:
        _report_service = ReportService()
    return _report_service