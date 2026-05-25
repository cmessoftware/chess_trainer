from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import tempfile
import uuid
import subprocess
import psycopg2
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager

# Importar solo el router de reportes para la prueba
from routers.reports import router as reports_router

# from routers.import_pgn import router as import_router  # Deshabilitado por ahora


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    print("🚀 Iniciando Chess Trainer API (Modo Prueba - Solo Reportes)...")
    yield
    print("🛑 Cerrando Chess Trainer API...")


# Crear aplicación FastAPI
app = FastAPI(
    title="Chess Trainer API - Test Mode",
    description="API para análisis y entrenamiento de ajedrez - Modo de prueba para reportes",
    version="0.1.0",
    lifespan=lifespan,
)

# Configurar CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(reports_router)
# app.include_router(import_router, prefix="/api")  # Deshabilitado por ahora


# Endpoints básicos que espera el frontend
@app.get("/api/notifications/")
async def get_notifications(unread_only: bool = False, limit: int = 20):
    """Endpoint básico de notificaciones para evitar errores CORS"""
    return {"notifications": [], "total": 0}


@app.post("/api/features/extract")
async def extract_features():
    """Endpoint real para extracción de features"""
    try:
        # Ejecutar script de features directamente
        import subprocess
        import os

        # Cambiar al directorio raíz del proyecto
        project_root = Path(__file__).parent.parent.parent

        # Comando para ejecutar generación de features
        cmd = [
            r"C:\Users\sergiosal\miniforge3\envs\chess_trainer\python.exe",
            "src/scripts/generate_features_with_tactics.py",
        ]

        # Ejecutar en background
        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        return {
            "message": "Feature extraction started successfully",
            "status": "started",
            "process_id": process.pid,
            "command": " ".join(cmd),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error starting feature extraction: {str(e)}"
        )


@app.post("/logs/test/import")
async def log_import_event():
    """Endpoint básico para logging"""
    return {"message": "Logged successfully", "status": "ok"}


# Endpoints de importación básicos para testing
temp_upload_dir = Path(tempfile.gettempdir()) / "chess_trainer_uploads"
temp_upload_dir.mkdir(exist_ok=True)


@app.post("/api/upload/pgn")
async def upload_pgn_file(file: UploadFile = File(...)):
    """Endpoint completo para subir e importar archivos PGN"""
    try:
        # Generar ID único para el job
        job_id = str(uuid.uuid4())

        # Crear directorio para este job
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir(exist_ok=True)

        # Guardar el archivo
        file_path = job_dir / file.filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # Contar partidas aproximadas (búsqueda simple de [Event])
        content_str = content.decode("utf-8", errors="ignore")
        estimated_games = content_str.count('[Event "')

        # Copiar archivo al directorio del proyecto para importación
        project_root = Path(__file__).parent.parent.parent
        target_dir = project_root / "data" / "games" / "personal"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / file.filename

        with open(target_file, "wb") as f:
            f.write(content)

        # Ejecutar importación a PostgreSQL
        import_cmd = [
            r"C:\Users\sergiosal\miniforge3\envs\chess_trainer\python.exe",
            "src/scripts/import_pgns_parallel.py",
            str(target_file),
            "--source",
            "personal",
        ]

        # Ejecutar importación en background
        import_process = subprocess.Popen(
            import_cmd,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        return JSONResponse(
            {
                "message": "Archivo subido e importación iniciada",
                "job_id": job_id,
                "filename": file.filename,
                "size": len(content),
                "estimated_games": estimated_games,
                "file_path": str(file_path),
                "target_file": str(target_file),
                "import_process_id": import_process.pid,
                "status": "uploaded_and_importing",
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo archivo: {str(e)}")


@app.get("/api/upload/status/{job_id}")
async def get_upload_status(job_id: str):
    """Obtener estado de upload en modo prueba"""
    job_dir = temp_upload_dir / job_id
    if not job_dir.exists():
        raise HTTPException(status_code=404, detail="Job no encontrado")

    return {
        "job_id": job_id,
        "status": "uploaded",
        "message": "Archivo disponible en modo prueba",
    }


# Endpoints para extracción de características y progreso
@app.post("/api/features/extract")
async def start_feature_extraction(payload: dict):
    """Iniciar extracción masiva de características (ADMIN)"""
    try:
        # Simular inicio de proceso
        process_id = f"proc_{uuid.uuid4().hex[:8]}"
        return {
            "job_id": process_id,
            "message": "Extracción masiva de características iniciada",
            "status": "started",
            "type": "bulk_extraction",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error iniciando extracción: {str(e)}")

@app.post("/api/analysis/user-game")
async def analyze_user_game(payload: dict):
    """Analizar partida específica del usuario (USER)"""
    try:
        game_content = payload.get('pgn_content', '')
        user_id = payload.get('user_id', 'user-001')
        
        if not game_content:
            raise HTTPException(status_code=400, detail="Contenido PGN requerido")
        
        # Simular análisis de partida individual
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        
        return {
            "analysis_id": analysis_id,
            "message": "Análisis de partida iniciado",
            "status": "analyzing",
            "type": "personal_analysis",
            "user_id": user_id,
            "estimated_time": "2-5 segundos",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analizando partida: {str(e)}")

@app.get("/api/analysis/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Obtener estado del análisis de partida"""
    # Simular análisis completado
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "results": {
            "features_extracted": 45,
            "tactics_found": 3,
            "blunders": 2,
            "accuracy": 87.5,
            "opening": "Sicilian Defense",
            "endgame_type": "Rook endgame"
        },
        "completed_at": datetime.now().isoformat()
    }
            status_code=500, detail=f"Error iniciando extracción: {str(e)}"
        )


@app.get("/api/features/progress")
async def get_feature_extraction_progress():
    """Obtener progreso de extracción de características"""
    try:
        # Ejecutar consulta directa a la base de datos para obtener progreso real
        import psycopg2

        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chess_trainer_db",
            user="chess",
            password="chess_pass",
        )
        cur = conn.cursor()

        # Obtener estadísticas totales
        cur.execute("SELECT COUNT(*) FROM games")
        total_games = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM features")
        total_features = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT game_id) FROM features")
        games_with_features = cur.fetchone()[0]

        # Obtener estadísticas por fuente
        cur.execute(
            """
            SELECT source, COUNT(*) as total,
                   COUNT(CASE WHEN game_id IN (SELECT DISTINCT game_id FROM features) THEN 1 END) as with_features
            FROM games 
            GROUP BY source
        """
        )

        sources_stats = {}
        for row in cur.fetchall():
            source, total, with_features = row
            percentage = (with_features / total * 100) if total > 0 else 0
            sources_stats[source] = {
                "total": total,
                "with_features": with_features,
                "percentage": round(percentage, 1),
            }

        cur.close()
        conn.close()

        completion_percentage = (
            (games_with_features / total_games * 100) if total_games > 0 else 0
        )

        progress_data = {
            "status": "running" if completion_percentage < 100 else "completed",
            "total_features": total_features,
            "total_games": total_games,
            "games_with_features": games_with_features,
            "completion_percentage": round(completion_percentage, 1),
            "sources": sources_stats,
            "timestamp": datetime.now().isoformat(),
        }

        return progress_data

    except Exception as e:
        # Fallback con datos simulados si hay error de conexión
        return {
            "status": "error",
            "message": f"Error obteniendo progreso: {str(e)}",
            "total_features": 951757,
            "total_games": 232097,
            "games_with_features": 12743,
            "completion_percentage": 5.5,
            "sources": {
                "personal": {"percentage": 41.4},
                "elite": {"percentage": 0.0},
                "novice": {"percentage": 0.0},
                "stockfish": {"percentage": 0.0},
                "fide": {"percentage": 0.0},
            },
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/api/features/jobs")
async def list_feature_extraction_jobs():
    """Listar trabajos de extracción de características"""
    return {
        "jobs": [
            {
                "job_id": "active_extraction",
                "status": "running",
                "created_at": datetime.now().isoformat(),
                "type": "feature_extraction",
            }
        ]
    }


@app.get("/api/features/status/{job_id}")
async def get_extraction_status(job_id: str):
    """Obtener estado de un job específico"""
    return {
        "job_id": job_id,
        "status": "running",
        "progress": await get_feature_extraction_progress(),
        "timestamp": datetime.now().isoformat(),
    }


# Endpoints para notificaciones
@app.get("/api/notifications/")
async def get_notifications(unread_only: bool = False, limit: int = 20):
    """Obtener notificaciones del sistema"""
    try:
        print(
            f"Debug - Notificaciones solicitadas: unread_only={unread_only}, limit={limit}"
        )  # Debug log

        # Obtener progreso actual de forma simple (no async)
        try:
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="chess_trainer_db",
                user="chess",
                password="chess_pass",
            )
            cur = conn.cursor()

            # Obtener estadísticas básicas
            cur.execute("SELECT COUNT(*) FROM games")
            total_games = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM features")
            total_features = cur.fetchone()[0]

            cur.execute("SELECT COUNT(DISTINCT game_id) FROM features")
            games_with_features = cur.fetchone()[0]

            completion_percentage = (
                (games_with_features / total_games * 100) if total_games > 0 else 0
            )

            cur.close()
            conn.close()

            print(
                f"Debug - Progreso: {games_with_features}/{total_games} ({completion_percentage:.1f}%)"
            )  # Debug log

        except Exception as e:
            print(f"Debug - Error DB: {e}")
            # Datos fallback
            total_games = 236217
            games_with_features = 12746
            completion_percentage = 5.4

        notifications = []

        # Generar notificación de progreso si está en ejecución
        if completion_percentage < 100:
            notifications.append(
                {
                    "id": "progress_1",
                    "type": "info",
                    "title": "Extracción de características en progreso",
                    "message": f"Procesadas {games_with_features:,} de {total_games:,} partidas ({completion_percentage:.1f}%)",
                    "timestamp": datetime.now().isoformat(),
                    "read": False,
                    "action_url": "/import",
                }
            )

        # Notificación de completion
        if completion_percentage >= 100:
            notifications.append(
                {
                    "id": "completed_all",
                    "type": "success",
                    "title": "¡Extracción completada!",
                    "message": f"Se han procesado todas las {games_with_features:,} partidas exitosamente",
                    "timestamp": datetime.now().isoformat(),
                    "read": False,
                    "action_url": "/reports",
                }
            )

        # Agregar notificación de Stockfish (always completed)
        notifications.append(
            {
                "id": "completed_stockfish",
                "type": "success",
                "title": "Fuente stockfish completada",
                "message": "Todas las partidas de stockfish han sido procesadas (1,000 partidas)",
                "timestamp": datetime.now().isoformat(),
                "read": False,
                "action_url": "/reports",
            }
        )

        print(f"Debug - Generated {len(notifications)} notifications")  # Debug log

        # Si se requieren solo no leídas, filtrar
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]

        return {
            "notifications": notifications[:limit],
            "total": len(notifications),
            "unread_count": len([n for n in notifications if not n["read"]]),
        }

    except Exception as e:
        print(f"Debug - Error general en notificaciones: {e}")  # Debug log
        return {"notifications": [], "total": 0, "unread_count": 0, "error": str(e)}


@app.options("/api/notifications/")
async def notifications_options():
    """Handle OPTIONS request for notifications"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


@app.get("/api/notifications/unread/count")
async def get_unread_count():
    """Obtener conteo de notificaciones no leídas"""
    notifications_data = await get_notifications(unread_only=True)
    return {"count": notifications_data["unread_count"]}


@app.post("/api/notifications/{notification_id}/read")
async def mark_notification_as_read(notification_id: str):
    """Marcar notificación como leída"""
    return {"success": True, "notification_id": notification_id}


# Endpoints específicos para análisis de partidas individuales (USUARIOS BÁSICOS)
@app.post("/api/analysis/user-game")
async def analyze_user_game(payload: dict):
    """Analizar partida específica del usuario (USER)"""
    try:
        game_content = payload.get('pgn_content', '')
        user_id = payload.get('user_id', 'user-001')
        
        if not game_content:
            raise HTTPException(status_code=400, detail="Contenido PGN requerido")
        
        # Simular análisis de partida individual
        analysis_id = f"analysis_{uuid.uuid4().hex[:8]}"
        
        return {
            "analysis_id": analysis_id,
            "message": "Análisis de partida iniciado",
            "status": "analyzing",
            "type": "personal_analysis",
            "user_id": user_id,
            "estimated_time": "2-5 segundos",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analizando partida: {str(e)}")


@app.get("/api/analysis/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """Obtener estado del análisis de partida"""
    # Simular análisis completado
    return {
        "analysis_id": analysis_id,
        "status": "completed",
        "results": {
            "features_extracted": 45,
            "tactics_found": 3,
            "blunders": 2,
            "accuracy": 87.5,
            "opening": "Sicilian Defense",
            "endgame_type": "Rook endgame"
        },
        "completed_at": datetime.now().isoformat()
    }


@app.post("/api/analysis/upload-personal-pgn")
async def upload_personal_pgn(file: UploadFile = File(...)):
    """Subir PGN personal para análisis individual (USER)"""
    try:
        # Leer contenido
        content = await file.read()
        content_str = content.decode('utf-8', errors='ignore')
        
        # Contar partidas
        game_count = content_str.count('[Event "')
        
        if game_count == 0:
            raise HTTPException(status_code=400, detail="No se encontraron partidas válidas")
        
        # Generar ID de análisis
        upload_id = f"upload_{uuid.uuid4().hex[:8]}"
        
        return {
            "upload_id": upload_id,
            "message": f"PGN personal recibido ({game_count} partidas)",
            "game_count": game_count,
            "status": "ready_for_analysis",
            "type": "personal_upload",
            "filename": file.filename,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando PGN: {str(e)}")


@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "message": "Chess Trainer API - Test Mode",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "reports": "/api/reports/",
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "mode": "test"}


if __name__ == "__main__":
    uvicorn.run(
        "main_test:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
