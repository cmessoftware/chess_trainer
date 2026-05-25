"""
Router para generar reportes personalizados de jugadores
Integra con los scripts genéricos y maneja procesamientos asíncronos
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional, List
import uuid
import subprocess
import os
import json
from datetime import datetime

# from ..services.notification_service import get_notification_service  # Temporarily disabled

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Modelos de datos
class PlayerReportRequest(BaseModel):
    player_name: str
    min_games: Optional[int] = 50
    include_survivorship: Optional[bool] = True
    include_streak_analysis: Optional[bool] = True  # Análisis de rachas de errores
    include_pgn_games: Optional[bool] = True  # Incluir PGNs de partidas con rachas
    generate_pdf: Optional[bool] = True  # Generar PDF automáticamente
    output_format: Optional[str] = "markdown"  # markdown, pdf
    notification_email: Optional[str] = None

class ReportJobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    player_name: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    report_path: Optional[str] = None
    pdf_report_path: Optional[str] = None
    streak_analysis_path: Optional[str] = None
    pgn_games_path: Optional[str] = None
    error_message: Optional[str] = None
    progress_percentage: Optional[int] = 0
    current_step: Optional[str] = None
    analysis_summary: Optional[dict] = None

class FileUploadReportRequest(BaseModel):
    player_name: str
    pgn_files: List[str]  # Paths to uploaded PGN files
    source: Optional[str] = "uploaded"
    min_games: Optional[int] = 20
    include_survivorship: Optional[bool] = True

# Estado de jobs en memoria (en producción usar Redis/database)
active_jobs = {}

@router.post("/generate", response_model=dict)
async def generate_player_report(
    request: PlayerReportRequest,
    background_tasks: BackgroundTasks
):
    """
    Generar reporte personalizado para un jugador existente en la BD
    """
    try:
        # Generar job ID único
        job_id = str(uuid.uuid4())
        
        # Verificar que el jugador existe en BD usando script genérico
        verification_result = await verify_player_exists(request.player_name)
        
        if not verification_result["exists"]:
            raise HTTPException(
                status_code=404, 
                detail=f"Jugador '{request.player_name}' no encontrado en la base de datos. "
                       f"Importa sus PGNs primero o usa el endpoint /generate-from-upload"
            )
        
        # Crear registro del job
        job_status = ReportJobStatus(
            job_id=job_id,
            status="pending",
            player_name=request.player_name,
            created_at=datetime.now(),
            progress_percentage=0
        )
        
        active_jobs[job_id] = job_status.dict()
        
        # Lanzar tarea en background
        background_tasks.add_task(
            process_existing_player_report,
            job_id,
            request
        )
        
        return {
            "job_id": job_id,
            "status": "pending", 
            "message": f"Generación de reporte para '{request.player_name}' iniciada",
            "estimated_time_minutes": estimate_processing_time(verification_result.get("games_count", 0))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-from-upload", response_model=dict)
async def generate_report_from_upload(
    request: FileUploadReportRequest,
    background_tasks: BackgroundTasks
):
    """
    Generar reporte a partir de PGNs subidos recientemente
    """
    try:
        # Generar job ID único
        job_id = str(uuid.uuid4())
        
        # Verificar que los archivos PGN existen
        for pgn_file in request.pgn_files:
            if not os.path.exists(pgn_file):
                raise HTTPException(
                    status_code=400,
                    detail=f"Archivo PGN no encontrado: {pgn_file}"
                )
        
        # Crear registro del job
        job_status = ReportJobStatus(
            job_id=job_id,
            status="pending", 
            player_name=request.player_name,
            created_at=datetime.now(),
            progress_percentage=0
        )
        
        active_jobs[job_id] = job_status.dict()
        
        # Lanzar tarea en background
        background_tasks.add_task(
            process_upload_player_report,
            job_id,
            request
        )
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": f"Importación y análisis de '{request.player_name}' iniciados",
            "files_to_process": len(request.pgn_files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=ReportJobStatus)
async def get_job_status(job_id: str):
    """
    Obtener estado de un job de generación de reporte
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    return ReportJobStatus(**active_jobs[job_id])

@router.get("/download/{job_id}")
async def download_report(job_id: str):
    """
    Descargar reporte generado
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    job_status = active_jobs[job_id]
    
    if job_status["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Reporte no está listo. Estado actual: {job_status['status']}"
        )
    
    report_path = job_status.get("report_path")
    if not report_path or not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Archivo de reporte no encontrado")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=report_path,
        filename=f"{job_status['player_name']}_reporte.md",
        media_type="text/markdown"
    )

@router.get("/list")
async def list_recent_reports():
    """
    Listar reportes recientes generados
    """
    # Filtrar jobs de últimos 7 días y ordenar por fecha
    recent_jobs = []
    for job_id, job_data in active_jobs.items():
        created_at = datetime.fromisoformat(job_data["created_at"])
        if (datetime.now() - created_at).days <= 7:
            recent_jobs.append({
                "job_id": job_id,
                **job_data
            })
    
    # Ordenar por fecha de creación (más recientes primero)
    recent_jobs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {"reports": recent_jobs}

# Funciones auxiliares
async def verify_player_exists(player_name: str) -> dict:
    """Verificar si un jugador existe usando script genérico"""
    try:
        script_path = "src/scripts/check_player_data.py"
        result = subprocess.run(
            ["python", script_path, player_name],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
            env={**os.environ, "PYTHONPATH": f"{os.getcwd()}/src"}
        )
        
        if result.returncode == 0:
            # Parse output del script
            output = result.stdout.strip()
            
            # Extraer información del output
            games_count = 0
            features_count = 0
            
            for line in output.split('\n'):
                if 'Juegos totales:' in line:
                    try:
                        games_count = int(line.split(':')[1].strip())
                    except ValueError:
                        pass
                elif 'Features disponibles:' in line:
                    try:
                        features_count = int(line.split(':')[1].strip())
                    except ValueError:
                        pass
            
            # Considerar que existe si tiene al menos 1 juego
            exists = games_count > 0
            
            return {
                "exists": exists,
                "games_count": games_count,
                "features_count": features_count,
                "ready_for_analysis": exists and features_count > 0
            }
        
        return {"exists": False, "games_count": 0, "features_count": 0, "ready_for_analysis": False}
        
    except Exception as e:
        print(f"Error verificando jugador: {e}")
        return {"exists": False, "games_count": 0, "features_count": 0, "ready_for_analysis": False}

def estimate_processing_time(games_count: int) -> int:
    """Estimar tiempo de procesamiento en minutos"""
    if games_count < 100:
        return 1
    elif games_count < 1000:
        return 3
    elif games_count < 3000:
        return 8
    else:
        return 15

async def process_existing_player_report(job_id: str, request: PlayerReportRequest):
    """
    Procesar reporte para jugador existente en BD
    """
    try:
        # Actualizar estado
        active_jobs[job_id]["status"] = "processing"
        active_jobs[job_id]["progress_percentage"] = 10
        
        # Paso 1: Análisis básico usando script genérico
        await update_job_progress(job_id, 15, "Generando análisis básico...")
        
        script_path = "src/scripts/analyze_player.py"
        result = subprocess.run(
            [
                "python", script_path, request.player_name,
                "--min-games", str(request.min_games),
                "--output-dir", "reports/api_generated"
            ],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            raise Exception(f"Error en análisis básico: {result.stderr}")
            
        # Paso 1.5: Análisis detallado de rachas de errores
        streak_analysis_path = None
        pgn_games_path = None
        
        if request.include_streak_analysis:
            await update_job_progress(job_id, 35, "Analizando rachas de errores...")
            
            # Ejecutar análisis de rachas detallado
            streak_script = "src/scripts/analyze_detailed_streaks.py"
            streak_result = subprocess.run(
                ["python", streak_script, request.player_name],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if streak_result.returncode == 0:
                # Buscar archivo de rachas generado
                streak_files = find_streak_analysis_files(request.player_name)
                if streak_files:
                    streak_analysis_path = streak_files[0]
                    
            # Extraer PGNs de partidas si está habilitado
            if request.include_pgn_games:
                await update_job_progress(job_id, 45, "Extrayendo PGNs de partidas con rachas...")
                
                pgn_script = "src/scripts/extract_game_pgns.py"
                pgn_result = subprocess.run(
                    ["python", pgn_script, "all"],
                    capture_output=True,
                    text=True,
                    cwd=os.getcwd()
                )
                
                if pgn_result.returncode == 0:
                    pgn_files = find_pgn_analysis_files(request.player_name)
                    if pgn_files:
                        pgn_games_path = pgn_files[0]
        
        # Paso 2: Survivorship Bias si está habilitado
        survivorship_report = None
        if request.include_survivorship:
            await update_job_progress(job_id, 65, "Analizando patrones de supervivencia...")
            
            survivorship_script = "src/scripts/analyze_survivorship.py" 
            survivorship_result = subprocess.run(
                ["python", survivorship_script, request.player_name],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if survivorship_result.returncode == 0:
                survivorship_report = "Análisis de supervivencia completado"
        
        # Paso 3: Localizar archivo de reporte generado
        await update_job_progress(job_id, 75, "Finalizando reporte...")
        
        report_files = find_latest_report_file(request.player_name)
        if not report_files:
            raise Exception("No se pudo encontrar el archivo de reporte generado")
        
        # Paso 4: Generar reporte consolidado con análisis de rachas
        final_report_path = report_files[0]
        if streak_analysis_path or pgn_games_path:
            await update_job_progress(job_id, 85, "Consolidando análisis de rachas...")
            final_report_path = await create_consolidated_report(
                request.player_name, 
                report_files[0], 
                streak_analysis_path, 
                pgn_games_path
            )
        
        # Paso 5: Generar PDF automáticamente si está habilitado
        pdf_report_path = None
        if request.generate_pdf or request.output_format == "pdf":
            await update_job_progress(job_id, 90, "Generando PDF...")
            
            pdf_report_path = await generate_pdf_report(final_report_path)
            
            # Si solo se pidió PDF, usar ese como reporte principal
            if request.output_format == "pdf" and pdf_report_path:
                final_report_path = pdf_report_path
        
        # Paso 6: Generar resumen de análisis
        analysis_summary = await generate_analysis_summary(
            request.player_name, streak_analysis_path, survivorship_report
        )
        
        # Completar job con todos los archivos generados
        await complete_job_enhanced(
            job_id, 
            final_report_path, 
            pdf_report_path,
            streak_analysis_path,
            pgn_games_path,
            analysis_summary,
            survivorship_report
        )
        
        # Enviar notificación
        await send_report_notification(job_id, request.player_name, f"Reporte de {request.player_name} está listo")
        
    except Exception as e:
        await fail_job(job_id, str(e))

async def process_upload_player_report(job_id: str, request: FileUploadReportRequest):
    """
    Procesar reporte para jugador desde PGNs subidos
    """
    try:
        # Actualizar estado
        active_jobs[job_id]["status"] = "processing"
        active_jobs[job_id]["progress_percentage"] = 5
        
        # Paso 1: Importar PGNs usando script genérico
        await update_job_progress(job_id, 20, "Importando partidas...")
        
        import_script = "src/scripts/import_player_pgns.py"
        result = subprocess.run(
            [
                "python", import_script, request.player_name,
                "--source", request.source,
                "--files"] + request.pgn_files,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode != 0:
            raise Exception(f"Error importando PGNs: {result.stderr}")
        
        # Paso 2: Verificar que se importaron suficientes partidas
        await update_job_progress(job_id, 40, "Verificando datos importados...")
        
        verification = await verify_player_exists(request.player_name)
        if not verification["exists"] or verification["games_count"] < request.min_games:
            raise Exception(
                f"Insuficientes partidas importadas. " 
                f"Requeridas: {request.min_games}, Importadas: {verification.get('games_count', 0)}"
            )
        
        # Paso 3: Continuar con análisis normal
        await update_job_progress(job_id, 60, "Generando análisis...")
        
        # Convertir a PlayerReportRequest para reutilizar lógica
        analysis_request = PlayerReportRequest(
            player_name=request.player_name,
            min_games=request.min_games,
            include_survivorship=request.include_survivorship,
            output_format="markdown"
        )
        
        # Ejecutar proceso de análisis existente
        await process_existing_player_report(job_id, analysis_request)
        
    except Exception as e:
        await fail_job(job_id, str(e))

async def update_job_progress(job_id: str, percentage: int, message: str):
    """Actualizar progreso del job"""
    if job_id in active_jobs:
        active_jobs[job_id]["progress_percentage"] = percentage
        active_jobs[job_id]["current_step"] = message
        print(f"Job {job_id}: {percentage}% - {message}")

async def complete_job_enhanced(
    job_id: str, 
    report_path: str, 
    pdf_report_path: str = None,
    streak_analysis_path: str = None,
    pgn_games_path: str = None,
    analysis_summary: dict = None,
    additional_info: str = None
):
    """Completar job con información extendida"""
    if job_id in active_jobs:
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["progress_percentage"] = 100
        active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        active_jobs[job_id]["report_path"] = report_path
        
        if pdf_report_path:
            active_jobs[job_id]["pdf_report_path"] = pdf_report_path
        if streak_analysis_path:
            active_jobs[job_id]["streak_analysis_path"] = streak_analysis_path
        if pgn_games_path:
            active_jobs[job_id]["pgn_games_path"] = pgn_games_path
        if analysis_summary:
            active_jobs[job_id]["analysis_summary"] = analysis_summary
        if additional_info:
            active_jobs[job_id]["additional_info"] = additional_info

async def fail_job(job_id: str, error_message: str):
    """Marcar job como fallido"""
    if job_id in active_jobs:
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error_message"] = error_message
        active_jobs[job_id]["completed_at"] = datetime.now().isoformat()

def find_latest_report_file(player_name: str) -> List[str]:
    """Encontrar archivos de reporte más recientes para un jugador"""
    report_dirs = ["reports", "reports/api_generated"]
    matching_files = []
    
    for report_dir in report_dirs:
        if os.path.exists(report_dir):
            for filename in os.listdir(report_dir):
                if (player_name.lower() in filename.lower() and 
                    filename.endswith('.md') and
                    'analysis' in filename):
                    full_path = os.path.join(report_dir, filename)
                    matching_files.append((full_path, os.path.getmtime(full_path)))
    
    # Ordenar por fecha de modificación (más reciente primero)
    matching_files.sort(key=lambda x: x[1], reverse=True)
    
    return [path for path, _ in matching_files]

def find_streak_analysis_files(player_name: str) -> List[str]:
    """Encontrar archivos de análisis de rachas para un jugador"""
    report_dirs = ["reports", "reports/api_generated"]
    matching_files = []
    
    for report_dir in report_dirs:
        if os.path.exists(report_dir):
            for filename in os.listdir(report_dir):
                if (player_name.lower() in filename.lower() and 
                    ('streak' in filename.lower() or 'racha' in filename.lower()) and
                    filename.endswith('.md')):
                    full_path = os.path.join(report_dir, filename)
                    matching_files.append((full_path, os.path.getmtime(full_path)))
    
    matching_files.sort(key=lambda x: x[1], reverse=True)
    return [path for path, _ in matching_files]

def find_pgn_analysis_files(player_name: str) -> List[str]:
    """Encontrar archivos PGN de análisis para un jugador"""
    report_dirs = ["reports", "reports/api_generated"]
    matching_files = []
    
    for report_dir in report_dirs:
        if os.path.exists(report_dir):
            for filename in os.listdir(report_dir):
                if (player_name.lower() in filename.lower() and 
                    'pgn' in filename.lower() and
                    filename.endswith('.md')):
                    full_path = os.path.join(report_dir, filename)
                    matching_files.append((full_path, os.path.getmtime(full_path)))
    
    matching_files.sort(key=lambda x: x[1], reverse=True)
    return [path for path, _ in matching_files]

async def generate_pdf_report(markdown_path: str) -> str:
    """Generar PDF a partir de archivo markdown"""
    try:
        pdf_script = "src/scripts/convert_md_to_pdf.py"
        result = subprocess.run(
            ["python", pdf_script, markdown_path],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            # Buscar archivo PDF generado
            pdf_path = markdown_path.replace('.md', '.pdf')
            if os.path.exists(pdf_path):
                return pdf_path
        return None
        
    except Exception as e:
        print(f"Error generando PDF: {e}")
        return None

async def create_consolidated_report(
    player_name: str, 
    base_report_path: str, 
    streak_analysis_path: str = None, 
    pgn_games_path: str = None
) -> str:
    """Crear reporte consolidado combinando análisis básico y de rachas"""
    try:
        # Leer reporte base
        with open(base_report_path, 'r', encoding='utf-8') as f:
            base_content = f.read()
        
        consolidated_content = base_content
        
        # Agregar análisis de rachas si existe
        if streak_analysis_path and os.path.exists(streak_analysis_path):
            with open(streak_analysis_path, 'r', encoding='utf-8') as f:
                streak_content = f.read()
            
            consolidated_content += "\n\n" + "="*80 + "\n"
            consolidated_content += "## 🔥 ANÁLISIS DETALLADO DE RACHAS DE ERRORES\n"
            consolidated_content += "="*80 + "\n\n"
            consolidated_content += streak_content
        
        # Agregar PGNs si existen
        if pgn_games_path and os.path.exists(pgn_games_path):
            with open(pgn_games_path, 'r', encoding='utf-8') as f:
                pgn_content = f.read()
            
            consolidated_content += "\n\n" + "="*80 + "\n"
            consolidated_content += "## 🎮 PARTIDAS CON RACHAS DE ERRORES (PGNs)\n"
            consolidated_content += "="*80 + "\n\n"
            consolidated_content += pgn_content
        
        # Guardar reporte consolidado
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        consolidated_path = f"reports/api_generated/{player_name}_reporte_completo_{timestamp}.md"
        
        os.makedirs("reports/api_generated", exist_ok=True)
        
        with open(consolidated_path, 'w', encoding='utf-8') as f:
            f.write(consolidated_content)
        
        return consolidated_path
        
    except Exception as e:
        print(f"Error creando reporte consolidado: {e}")
        return base_report_path

async def generate_analysis_summary(
    player_name: str, 
    streak_analysis_path: str = None, 
    survivorship_report: str = None
) -> dict:
    """Generar resumen del análisis para mostrar en UI"""
    summary = {
        "player_name": player_name,
        "timestamp": datetime.now().isoformat(),
        "analyses_completed": []
    }
    
    # Análisis básico siempre se completa
    summary["analyses_completed"].append("basic_analysis")
    
    # Verificar si se completó análisis de rachas
    if streak_analysis_path and os.path.exists(streak_analysis_path):
        summary["analyses_completed"].append("streak_analysis")
        
        # Extraer métricas clave del análisis de rachas
        try:
            with open(streak_analysis_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar métricas en el contenido
            import re
            
            # Extraer racha máxima
            max_streak_match = re.search(r'Racha máxima: (\d+)', content)
            if max_streak_match:
                summary["max_error_streak"] = int(max_streak_match.group(1))
            
            # Extraer total de rachas
            total_streaks_match = re.search(r'Total de rachas: (\d+)', content)
            if total_streaks_match:
                summary["total_streaks"] = int(total_streaks_match.group(1))
                
        except Exception as e:
            print(f"Error extrayendo métricas de rachas: {e}")
    
    # Verificar survivorship bias
    if survivorship_report:
        summary["analyses_completed"].append("survivorship_analysis")
    
    return summary

@router.get("/download/{job_id}/pdf")
async def download_pdf_report(job_id: str):
    """
    Descargar reporte en formato PDF
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    job_status = active_jobs[job_id]
    
    if job_status["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Reporte no está listo. Estado actual: {job_status['status']}"
        )
    
    pdf_path = job_status.get("pdf_report_path")
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Archivo PDF no encontrado")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=pdf_path,
        filename=f"{job_status['player_name']}_reporte.pdf",
        media_type="application/pdf"
    )

@router.get("/download/{job_id}/streak-analysis")
async def download_streak_analysis(job_id: str):
    """
    Descargar análisis detallado de rachas
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    job_status = active_jobs[job_id]
    
    if job_status["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Reporte no está listo. Estado actual: {job_status['status']}"
        )
    
    streak_path = job_status.get("streak_analysis_path")
    if not streak_path or not os.path.exists(streak_path):
        raise HTTPException(status_code=404, detail="Análisis de rachas no encontrado")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=streak_path,
        filename=f"{job_status['player_name']}_analisis_rachas.md",
        media_type="text/markdown"
    )

@router.get("/download/{job_id}/pgn-games")
async def download_pgn_games(job_id: str):
    """
    Descargar PGNs de partidas con rachas
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    
    job_status = active_jobs[job_id]
    
    if job_status["status"] != "completed":
        raise HTTPException(
            status_code=400, 
            detail=f"Reporte no está listo. Estado actual: {job_status['status']}"
        )
    
    pgn_path = job_status.get("pgn_games_path")
    if not pgn_path or not os.path.exists(pgn_path):
        raise HTTPException(status_code=404, detail="PGNs de partidas no encontrados")
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=pgn_path,
        filename=f"{job_status['player_name']}_partidas_rachas.md",
        media_type="text/markdown"
    )

async def send_report_notification(job_id: str, player_name: str, message: str):
    """
    Enviar notificación usando servicio existente
    """
    try:
        # Temporarily disabled - notification service not available
        print(f"📧 NOTIFICATION: {message} for job {job_id}")
        # notification_service = get_notification_service()
        # await notification_service.create_notification(
        #     user_id="system",  # O el ID del usuario autenticado
        #     title=f"Reporte de {player_name} Completado",
        #     message=message,
        #     type="report_ready",
        #     metadata={
        #         "job_id": job_id,
        #         "player_name": player_name,
        #         "report_url": f"/reports/view/{job_id}",
        #         "download_urls": {
        #             "markdown": f"/api/reports/download/{job_id}",
        #             "pdf": f"/api/reports/download/{job_id}/pdf",
        #             "streak_analysis": f"/api/reports/download/{job_id}/streak-analysis",
        #             "pgn_games": f"/api/reports/download/{job_id}/pgn-games"
        #         }
        #     }
        # )
    except Exception as e:
        print(f"Error enviando notificación: {e}")