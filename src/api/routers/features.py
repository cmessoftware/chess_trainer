"""
Router para procesamiento de features
Integra con el script generate_features_with_tactics.py existente
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import uuid
import subprocess
import threading
import traceback
from pathlib import Path
from datetime import datetime

# Importar utilidades existentes
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

# Importar database y models
from api.database import get_db
from db.models.notifications import Notification
from db.models.error_logs import ErrorLog

router = APIRouter(prefix="/api/features", tags=["features"])

# Helper function para asegurar serialización JSON correcta
import json
def ensure_json_serializable(data):
    """Asegurar que los datos sean JSON serializable - versión robusta"""
    if data is None:
        return None
    
    print(f"🔍 SERIALIZE DEBUG: Processing data type: {type(data)}")
    print(f"🔍 SERIALIZE DEBUG: Data content: {str(data)[:200]}...")
    
    try:
        # Si es un dict, procesar cada valor recursivamente
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                # Convertir cualquier objeto no serializable a string
                if hasattr(value, '__dict__'):
                    result[key] = str(value)
                elif isinstance(value, (list, tuple)):
                    result[key] = [str(item) if hasattr(item, '__dict__') else item for item in value]
                else:
                    result[key] = value
            
            # Verificar que sea serializable
            json.dumps(result)
            print(f"✅ SERIALIZE SUCCESS: Dict converted successfully")
            return result
        else:
            # Para otros tipos, convertir a string si es necesario
            result = str(data) if hasattr(data, '__dict__') else data
            json.dumps(result)
            print(f"✅ SERIALIZE SUCCESS: Data converted successfully")
            return result
            
    except Exception as e:
        print(f"❌ SERIALIZE ERROR: {e}")
        print(f"❌ SERIALIZE ERROR Data: {str(data)[:100]}...")
        # Fallback: convertir todo a string
        return str(data)

# Scripts existentes
GENERATE_FEATURES_SCRIPT = (
    Path(__file__).parent.parent.parent
    / "scripts"
    / "generate_features_with_tactics.py"
)


# Modelos Pydantic para request bodies
class FeatureExtractionRequest(BaseModel):
    batch_id: Optional[str] = None
    source: Optional[str] = None
    since_minutes: Optional[int] = None
    max_games: int = 1000
    workers: int = 4


# Estado de jobs (en memoria para tracking temporal)
feature_jobs = {}


@router.post("/extract")
async def start_feature_extraction(
    http_request: Request,
    extraction_request: FeatureExtractionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Iniciar extracción de features usando generate_features_with_tactics.py

    Args:
        http_request: FastAPI Request para obtener usuario
        extraction_request: Parámetros de extracción
        db: Sesión de base de datos

    Returns:
        Job ID para monitorear el progreso
    """
    # Obtener user_id del JWT
    user = getattr(http_request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    # Validación: Requiere batch_id o since_minutes
    if extraction_request.batch_id is None and extraction_request.since_minutes is None:
        raise HTTPException(
            status_code=400,
            detail="Debe proporcionar 'batch_id' o 'since_minutes' para procesar partidas específicas",
        )

    try:
        # Generar ID para el job
        job_id = str(uuid.uuid4())

        # Crear registro del job
        feature_jobs[job_id] = {
            "id": job_id,
            "batch_id": extraction_request.batch_id,
            "source": extraction_request.source,
            "since_minutes": extraction_request.since_minutes,
            "max_games": extraction_request.max_games,
            "workers": extraction_request.workers,
            "status": "queued",
            "started_at": datetime.now().isoformat(),
            "processed_games": 0,
            "total_games": 0,
            "progress": 0,
            "error": None,
        }

        # Crear notificación inicial en BD
        notification_id = str(uuid.uuid4())
        filter_desc = (
            f"batch {extraction_request.batch_id}"
            if extraction_request.batch_id
            else f"últimos {extraction_request.since_minutes} min"
        )
        
        notification = Notification(
            id=notification_id,
            user_id=user_id,
            type="processing",
            status="processing",
            title="Extracción de Features Iniciada",
            message=f"Procesando {filter_desc} - {extraction_request.source or 'todas las fuentes'}",
            read=False,
            dismissed=False,
            meta_data=ensure_json_serializable({
                "job_id": job_id,
                "batch_id": extraction_request.batch_id,
                "source": extraction_request.source,
                "max_games": extraction_request.max_games,
            })
        )
        db.add(notification)
        db.commit()

        # Iniciar procesamiento en background
        background_tasks.add_task(
            process_feature_extraction,
            job_id,
            notification_id,
            user_id,
            extraction_request.batch_id,
            extraction_request.source,
            extraction_request.since_minutes,
            extraction_request.max_games,
            extraction_request.workers,
        )

        return JSONResponse(
            {
                "jobId": job_id,
                "notificationId": notification_id,
                "status": "queued",
                "message": "Extracción de features iniciada en segundo plano",
                "batchId": extraction_request.batch_id,
                "source": extraction_request.source,
                "sinceMinutes": extraction_request.since_minutes,
                "maxGames": extraction_request.max_games,
                "workers": extraction_request.workers,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}")
async def get_feature_extraction_status(job_id: str):
    """
    Obtener estado de un job de extracción de features
    """
    if job_id not in feature_jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    return JSONResponse(feature_jobs[job_id])


@router.get("/jobs")
async def list_feature_jobs():
    """
    Listar todos los jobs de extracción de features
    """
    return JSONResponse(list(feature_jobs.values()))


@router.get("/progress")
async def get_feature_extraction_progress():
    """
    Obtener progreso general de extracción de features
    """
    active_jobs = [
        job
        for job in feature_jobs.values()
        if job["status"] in ["running", "processing"]
    ]
    completed_jobs = [
        job for job in feature_jobs.values() if job["status"] == "completed"
    ]
    failed_jobs = [job for job in feature_jobs.values() if job["status"] == "failed"]

    if active_jobs:
        # Si hay jobs activos, retornar el progreso del más reciente
        latest_job = max(active_jobs, key=lambda x: x["started_at"])
        return JSONResponse(
            {
                "is_processing": True,
                "progress": latest_job.get("progress", 0),
                "status": latest_job["status"],
                "job_id": latest_job["id"],
                "current_step": latest_job.get("current_step", "Processing..."),
                "total_jobs": len(feature_jobs),
                "active_jobs": len(active_jobs),
                "completed_jobs": len(completed_jobs),
                "failed_jobs": len(failed_jobs),
            }
        )
    elif completed_jobs:
        # Si no hay activos pero sí completados, mostrar el último completado
        latest_completed = max(
            completed_jobs, key=lambda x: x.get("completed_at", x["started_at"])
        )
        return JSONResponse(
            {
                "is_processing": False,
                "progress": 100,
                "status": "completed",
                "job_id": latest_completed["id"],
                "current_step": "Extraction completed successfully",
                "total_jobs": len(feature_jobs),
                "active_jobs": len(active_jobs),
                "completed_jobs": len(completed_jobs),
                "failed_jobs": len(failed_jobs),
                "last_completed": latest_completed.get("completed_at", "N/A"),
            }
        )
    else:
        # No hay jobs o solo hay fallidos
        return JSONResponse(
            {
                "is_processing": False,
                "progress": 0,
                "status": "idle",
                "job_id": None,
                "current_step": "No feature extraction in progress",
                "total_jobs": len(feature_jobs),
                "active_jobs": len(active_jobs),
                "completed_jobs": len(completed_jobs),
                "failed_jobs": len(failed_jobs),
            }
        )


def _run_feature_extraction_sync(
    job_id: str,
    notification_id: str,
    user_id: str,
    batch_id: Optional[str],
    source: Optional[str],
    since_minutes: Optional[int],
    max_games: int,
    workers: int,
):
    """
    Ejecutar extracción de features de forma síncrona en thread separado
    (Workaround para Windows donde asyncio.create_subprocess_exec no funciona con uvicorn --reload)
    """
    from api.database import SessionLocal  # Import local para evitar issues con threads
    db = SessionLocal()
    
    try:
        # Actualizar estado a processing
        feature_jobs[job_id]["status"] = "processing"

        # Construir comando usando sys.executable para usar el Python actual
        cmd = [
            sys.executable,
            str(GENERATE_FEATURES_SCRIPT),
            "--max-games",
            str(max_games),
            "--workers",
            str(workers),
        ]

        if batch_id:
            cmd.extend(["--batch-id", batch_id])
        elif since_minutes:
            cmd.extend(["--since-minutes", str(since_minutes)])

        if source:
            cmd.extend(["--source", source])

        # Log del comando para debug
        print(f"🚀 Ejecutando: {' '.join(cmd)}")

        # Ejecutar script usando subprocess.run (compatible con Windows)
        start_time = datetime.now()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(GENERATE_FEATURES_SCRIPT.parent),
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Log de output para debug
        stdout_text = result.stdout if result.stdout else ""
        stderr_text = result.stderr if result.stderr else ""

        if stdout_text:
            print(f"📝 STDOUT: {stdout_text[:1000]}")
        if stderr_text:
            print(f"❌ STDERR: {stderr_text[:1000]}")

        print(f"✅ Return code: {result.returncode}")

        # Parsear stdout para obtener número real de partidas procesadas
        games_processed = None
        if stdout_text:
            # Buscar patrones como "Procesadas X partidas" o "X games processed"
            import re
            patterns = [
                r'Procesadas?\s+(\d+)\s+partidas?',
                r'(\d+)\s+games?\s+processed',
                r'Total:\s+(\d+)',
                r'Features\s+generadas:\s+(\d+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, stdout_text, re.IGNORECASE)
                if match:
                    games_processed = int(match.group(1))
                    print(f"🎯 Detectadas {games_processed} partidas procesadas")
                    break

        if result.returncode == 0:
            # Éxito
            update_data = {
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "duration_seconds": duration,
                "progress": 100,
            }
            
            # Agregar games_processed si se detectó
            if games_processed is not None:
                update_data["games_processed"] = games_processed
            
            feature_jobs[job_id].update(update_data)

            # Mensaje para notificación
            if games_processed:
                games_msg = f"Se procesaron {games_processed} partidas exitosamente"
            else:
                games_msg = f"Extracción completada en {duration:.1f}s (límite: {max_games} partidas)"

            # Actualizar notificación en BD
            notification = db.query(Notification).filter_by(id=notification_id).first()
            if notification:
                notification.type = "success"
                notification.status = "completed"
                notification.title = "Extracción de Features Completada"
                notification.message = games_msg
                notification.updated_at = datetime.now()
                notification.meta_data = ensure_json_serializable({
                    "job_id": job_id,
                    "source": source,
                    "max_games": max_games,
                    "games_processed": games_processed,
                    "duration": f"{duration:.1f}s",
                })
                db.commit()

        else:
            # Error
            error_msg = (
                stderr_text
                if stderr_text
                else (
                    stdout_text
                    if stdout_text
                    else f"Código de salida: {result.returncode}"
                )
            )
            print(f"💥 PROCESO FALLÓ: {error_msg[:500]}")

            feature_jobs[job_id].update(
                {
                    "status": "failed",
                    "completed_at": datetime.now().isoformat(),
                    "duration_seconds": duration,
                    "error": error_msg[:1000],
                }
            )

            # Crear error log en BD
            error_log_id = str(uuid.uuid4())
            error_log = ErrorLog(
                id=error_log_id,
                user_id=user_id,
                severity="error",
                category="feature_extraction",
                error_type="SubprocessError",
                error_message=error_msg[:1000],
                stack_trace=stderr_text[:5000] if stderr_text else None,
                meta_data=ensure_json_serializable({
                    "job_id": job_id,
                    "batch_id": batch_id,
                    "source": source,
                    "return_code": result.returncode,
                })
            )
            db.add(error_log)

            # Actualizar notificación en BD
            notification = db.query(Notification).filter_by(id=notification_id).first()
            if notification:
                notification.type = "error"
                notification.status = "failed"
                notification.title = "Error en Extracción de Features"
                notification.message = f"El proceso falló con código {result.returncode}"
                notification.updated_at = datetime.now()
                notification.error_log_id = error_log_id
                notification.meta_data = ensure_json_serializable({
                    "job_id": job_id,
                    "error": error_msg[:500],
                    "error_log_id": error_log_id,
                })
            
            db.commit()

    except Exception as e:
        # Error inesperado
        error_trace = traceback.format_exc()
        print(f"💥 EXCEPCIÓN: {error_trace}")

        feature_jobs[job_id].update(
            {
                "status": "failed",
                "completed_at": datetime.now().isoformat(),
                "error": f"{str(e)}\n{error_trace}",
            }
        )

        # Crear error log en BD
        error_log_id = str(uuid.uuid4())
        error_log = ErrorLog(
            id=error_log_id,
            user_id=user_id,
            severity="critical",
            category="feature_extraction",
            error_type=type(e).__name__,
            error_message=str(e),
            stack_trace=error_trace[:5000],
            meta_data=ensure_json_serializable({
                "job_id": job_id,
                "batch_id": batch_id,
                "source": source,
            })
        )
        db.add(error_log)

        # Actualizar notificación en BD
        try:
            notification = db.query(Notification).filter_by(id=notification_id).first()
            if notification:
                notification.type = "error"
                notification.status = "failed"
                notification.title = "Error en Extracción de Features"
                notification.message = f"Error inesperado: {str(e)}"
                notification.updated_at = datetime.now()
                notification.error_log_id = error_log_id
                notification.meta_data = ensure_json_serializable({
                    "job_id": job_id,
                    "error": str(e),
                    "error_log_id": error_log_id,
                })
            db.commit()
        except Exception as commit_error:
            print(f"💥 Error al actualizar notificación: {commit_error}")
            db.rollback()
    
    finally:
        db.close()


async def process_feature_extraction(
    job_id: str,
    notification_id: str,
    user_id: str,
    batch_id: Optional[str],
    source: Optional[str],
    since_minutes: Optional[int],
    max_games: int,
    workers: int,
):
    """
    Wrapper async que ejecuta el procesamiento en un thread separado
    (Workaround para Windows donde asyncio.create_subprocess_exec no funciona con uvicorn --reload)
    """
    thread = threading.Thread(
        target=_run_feature_extraction_sync,
        args=(
            job_id,
            notification_id,
            user_id,
            batch_id,
            source,
            since_minutes,
            max_games,
            workers,
        ),
    )
    thread.start()


# Endpoints de notificaciones (usando BD, filtradas por usuario)
@router.get("/notifications")
async def get_notifications(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Obtener todas las notificaciones del usuario actual
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    notifications = db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    
    # Convertir a diccionarios usando método to_dict()
    result = [n.to_dict() for n in notifications]
    
    return JSONResponse(result)


@router.get("/notifications/unread")
async def get_unread_notifications(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Obtener notificaciones no leídas del usuario actual
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    notifications = db.query(Notification).filter_by(
        user_id=user_id,
        read=False
    ).order_by(Notification.created_at.desc()).all()
    
    # Convertir a diccionarios
    result = [
        {
            "id": n.id,
            "type": n.type,
            "status": n.status,
            "title": n.title,
            "message": n.message,
            "read": n.read,
            "dismissed": n.dismissed,
            "timestamp": n.created_at.isoformat(),
            "metadata": n.meta_data,
            "error_log_id": n.error_log_id,
        }
        for n in notifications
    ]
    
    return JSONResponse(result)


@router.put("/notifications/{notification_id}/read")
async def mark_notification_as_read(
    request: Request,
    notification_id: str,
    db: Session = Depends(get_db)
):
    """
    Marcar notificación como leída (solo del usuario actual)
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    notification = db.query(Notification).filter_by(
        id=notification_id,
        user_id=user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    notification.read = True
    notification.read_at = datetime.now()
    db.commit()
    
    return JSONResponse({"success": True})


@router.put("/notifications/read-all")
async def mark_all_notifications_as_read(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Marcar todas las notificaciones como leídas (solo del usuario actual)
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    notifications = db.query(Notification).filter_by(
        user_id=user_id,
        read=False
    ).all()
    
    for notification in notifications:
        notification.read = True
        notification.read_at = datetime.now()
    
    db.commit()
    return JSONResponse({"success": True, "count": len(notifications)})


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    request: Request,
    notification_id: str,
    db: Session = Depends(get_db)
):
    """
    Eliminar una notificación (solo del usuario actual)
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    notification = db.query(Notification).filter_by(
        id=notification_id,
        user_id=user_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    db.delete(notification)
    db.commit()
    return JSONResponse({"success": True})


@router.delete("/notifications/clear-all")
async def clear_all_notifications(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Limpiar todas las notificaciones (solo del usuario actual)
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    count = db.query(Notification).filter_by(user_id=user_id).delete()
    db.commit()
    
    return JSONResponse({"success": True, "count": count})


# ========== Error Logs Endpoints ==========

@router.get("/error-logs")
async def get_error_logs(
    request: Request,
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
    severity: Optional[str] = None,
    category: Optional[str] = None
):
    """
    Obtener error logs del usuario actual con paginación y filtros
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    query = db.query(ErrorLog).filter_by(user_id=user_id)
    
    # Aplicar filtros
    if severity:
        query = query.filter_by(severity=severity)
    if category:
        query = query.filter_by(category=category)
    
    # Count total
    total = query.count()
    
    # Aplicar paginación y ordenar
    errors = query.order_by(ErrorLog.created_at.desc()).limit(limit).offset(offset).all()
    
    # Convertir a diccionarios
    result = [
        {
            "id": e.id,
            "severity": e.severity,
            "category": e.category,
            "error_type": e.error_type,
            "error_message": e.error_message,
            "stack_trace": e.stack_trace,
            "context": e.meta_data,
            "created_at": e.created_at.isoformat(),
            "resolved": e.resolved,
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
            "resolution_notes": e.resolution_notes,
        }
        for e in errors
    ]
    
    return JSONResponse({"errors": result, "total": total, "limit": limit, "offset": offset})


@router.get("/error-logs/{error_id}")
async def get_error_log_detail(
    request: Request,
    error_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtener detalle de un error log específico
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    error = db.query(ErrorLog).filter_by(id=error_id, user_id=user_id).first()
    
    if not error:
        raise HTTPException(status_code=404, detail="Error log no encontrado")
    
    return JSONResponse({
        "id": error.id,
        "user_id": error.user_id,
        "severity": error.severity,
        "category": error.category,
        "error_type": error.error_type,
        "error_message": error.error_message,
        "stack_trace": error.stack_trace,
        "context": error.meta_data,
        "created_at": error.created_at.isoformat(),
        "resolved": error.resolved,
        "resolved_at": error.resolved_at.isoformat() if error.resolved_at else None,
        "resolution_notes": error.resolution_notes,
    })


@router.put("/error-logs/{error_id}/resolve")
async def resolve_error_log(
    request: Request,
    error_id: str,
    db: Session = Depends(get_db),
    resolution_notes: Optional[str] = None
):
    """
    Marcar error log como resuelto (solo admins o owner)
    """
    # Obtener user_id del JWT
    user = getattr(request.state, "user", {})
    user_id = str(user.get("user_id", "anonymous"))  # Convert to string for database
    
    error = db.query(ErrorLog).filter_by(id=error_id, user_id=user_id).first()
    
    if not error:
        raise HTTPException(status_code=404, detail="Error log no encontrado")
    
    error.resolved = "resolved"
    error.resolved_at = datetime.now()
    if resolution_notes:
        error.resolution_notes = resolution_notes
    
    db.commit()
    
    return JSONResponse({"success": True})
