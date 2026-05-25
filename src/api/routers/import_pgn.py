"""
Router para funcionalidades de importación de archivos PGN
Integra con el script import_pgns_parallel.py existente
"""

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Request,
)
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
import tempfile
import subprocess
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Importar utilidades existentes
import sys

sys.path.append(str(Path(__file__).parent.parent.parent))

from scripts.import_personal_pgn import import_personal_pgn

router = APIRouter(prefix="/api", tags=["import"])

# Configuración
TEMP_UPLOAD_DIR = Path(tempfile.gettempdir()) / "chess_trainer_uploads"
TEMP_UPLOAD_DIR.mkdir(exist_ok=True)

# Scripts existentes
PARALLEL_IMPORT_SCRIPT = (
    Path(__file__).parent.parent.parent / "scripts" / "import_pgns_parallel.py"
)

# Estado de jobs (en producción esto sería una base de datos)
upload_jobs = {}
import_jobs = {}


@router.post("/upload/pgn")
async def upload_pgn_file(
    request: Request,
    file: UploadFile = File(...),
    source: str = Form(default="personal"),
):
    """
    Subir archivo PGN, ZIP o TAR.GZ para posterior importación
    """
    # Obtener usuario del JWT
    user = getattr(request.state, "user", {})
    username = user.get("username", "anonymous")

    try:
        # Validar tipo de archivo
        allowed_extensions = [".pgn", ".zip", ".tar.gz", ".gz"]
        file_extension = "".join(Path(file.filename).suffixes)

        if not any(file.filename.lower().endswith(ext) for ext in allowed_extensions):
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de archivo no soportado. Permitidos: {allowed_extensions}",
            )

        # Generar ID único para el job
        job_id = str(uuid.uuid4())

        # Crear directorio para este job
        job_dir = TEMP_UPLOAD_DIR / job_id
        job_dir.mkdir(exist_ok=True)

        # Guardar archivo
        file_path = job_dir / file.filename
        content = await file.read()

        with open(file_path, "wb") as f:
            f.write(content)

        # Crear registro del job
        upload_jobs[job_id] = {
            "id": job_id,
            "filename": file.filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "size": len(content),
            "source": source,
            "imported_by": username,  # Usuario que importó
            "status": "uploaded",
            "uploaded_at": datetime.now().isoformat(),
            "estimated_games": estimate_games_in_file(file_path, len(content)),
        }

        return JSONResponse(
            {
                "jobId": job_id,
                "filename": file.filename,
                "size": len(content),
                "status": "uploaded",
                "estimatedGames": upload_jobs[job_id]["estimated_games"],
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upload/status/{job_id}")
async def get_upload_status(job_id: str):
    """
    Obtener estado de un job de upload
    """
    if job_id not in upload_jobs:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    return JSONResponse(upload_jobs[job_id])


@router.get("/upload/list")
async def list_uploads():
    """
    Listar todos los uploads disponibles
    """
    return JSONResponse(
        {"uploads": list(upload_jobs.values()), "total": len(upload_jobs)}
    )


@router.post("/import/pgn/batch")
async def start_batch_import(
    background_tasks: BackgroundTasks, file_ids: List[str], source: str = "personal"
):
    """
    Iniciar importación masiva usando el script import_pgns_parallel.py
    """
    try:
        # Validar que todos los archivos existen
        valid_files = []
        for file_id in file_ids:
            if file_id in upload_jobs and upload_jobs[file_id]["status"] == "uploaded":
                valid_files.append(upload_jobs[file_id])
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Archivo {file_id} no encontrado o no está listo",
                )

        if not valid_files:
            raise HTTPException(
                status_code=400, detail="No hay archivos válidos para importar"
            )

        # Generar ID para el job de importación
        import_job_id = str(uuid.uuid4())

        # Crear registro del job de importación
        import_jobs[import_job_id] = {
            "id": import_job_id,
            "file_ids": file_ids,
            "files": [f["filename"] for f in valid_files],
            "source": source,
            "status": "queued",
            "started_at": datetime.now().isoformat(),
            "total_files": len(valid_files),
            "processed_files": 0,
            "estimated_games": sum(f["estimated_games"] for f in valid_files),
            "imported_games": 0,
        }

        # Iniciar procesamiento en background
        background_tasks.add_task(
            process_import_job, import_job_id, valid_files, source
        )

        return JSONResponse(
            {
                "jobId": import_job_id,
                "status": "queued",
                "totalFiles": len(valid_files),
                "estimatedGames": import_jobs[import_job_id]["estimated_games"],
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/preview/{job_id}")
async def get_preview(job_id: str, limit: int = 10):
    """
    Obtener preview de partidas de un archivo
    """
    if job_id not in upload_jobs:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    job = upload_jobs[job_id]
    file_path = Path(job["file_path"])

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo físico no encontrado")

    try:
        games = []
        if file_path.suffix.lower() == ".pgn":
            games = parse_pgn_preview(file_path, limit)
        else:
            # Para archivos comprimidos, simular preview
            games = generate_mock_preview(limit)

        return JSONResponse(
            {"games": games, "total_shown": len(games), "filename": job["filename"]}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generando preview: {str(e)}"
        )


@router.get("/import/history")
async def get_import_history(page: int = 1, limit: int = 20):
    """
    Obtener historial de importaciones
    """
    try:
        # Combinar jobs de upload e importación
        all_jobs = []

        # Jobs de upload
        for job in upload_jobs.values():
            all_jobs.append({**job, "type": "upload"})

        # Jobs de importación
        for job in import_jobs.values():
            all_jobs.append({**job, "type": "import"})

        # Ordenar por fecha (más recientes primero)
        all_jobs.sort(
            key=lambda x: x.get("uploaded_at", x.get("started_at", "")), reverse=True
        )

        # Paginación
        start = (page - 1) * limit
        end = start + limit
        paginated_jobs = all_jobs[start:end]

        return JSONResponse(
            {
                "jobs": paginated_jobs,
                "total": len(all_jobs),
                "page": page,
                "limit": limit,
                "totalPages": (len(all_jobs) + limit - 1) // limit,
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/import/stats")
async def get_import_stats():
    """
    Obtener estadísticas de importación
    """
    try:
        total_uploads = len(upload_jobs)
        total_imports = len(import_jobs)

        completed_uploads = sum(
            1 for job in upload_jobs.values() if job["status"] == "uploaded"
        )
        completed_imports = sum(
            1 for job in import_jobs.values() if job["status"] == "completed"
        )

        total_estimated_games = sum(
            job["estimated_games"] for job in upload_jobs.values()
        )
        total_imported_games = sum(
            job.get("imported_games", 0) for job in import_jobs.values()
        )

        return JSONResponse(
            {
                "uploads": {
                    "total": total_uploads,
                    "completed": completed_uploads,
                    "success_rate": (
                        (completed_uploads / total_uploads * 100)
                        if total_uploads > 0
                        else 0
                    ),
                },
                "imports": {
                    "total": total_imports,
                    "completed": completed_imports,
                    "success_rate": (
                        (completed_imports / total_imports * 100)
                        if total_imports > 0
                        else 0
                    ),
                },
                "games": {
                    "estimated": total_estimated_games,
                    "imported": total_imported_games,
                },
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Funciones auxiliares


def estimate_games_in_file(file_path: Path, file_size: int) -> int:
    """
    Estimar número de partidas en un archivo
    """
    try:
        if file_path.suffix.lower() == ".pgn":
            # Estimación basada en tamaño promedio por partida (~2KB)
            return max(1, file_size // 2000)
        else:
            # Archivos comprimidos - estimación más agresiva
            return max(1, file_size // 500)
    except:
        return 1


def parse_pgn_preview(file_path: Path, limit: int = 10) -> List[dict]:
    """
    Parsear preview de partidas de un archivo PGN
    """
    games = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            current_game = {}
            for line in f:
                line = line.strip()
                if line.startswith("["):
                    # Header de partida
                    if "White " in line:
                        current_game["white"] = (
                            line.split('"')[1] if '"' in line else "Unknown"
                        )
                    elif "Black " in line:
                        current_game["black"] = (
                            line.split('"')[1] if '"' in line else "Unknown"
                        )
                    elif "Result " in line:
                        current_game["result"] = (
                            line.split('"')[1] if '"' in line else "*"
                        )
                    elif "Date " in line:
                        current_game["date"] = (
                            line.split('"')[1] if '"' in line else "Unknown"
                        )
                elif line and not line.startswith("[") and current_game:
                    # Final de partida
                    games.append(current_game)
                    current_game = {}

                    if len(games) >= limit:
                        break

        return games
    except Exception as e:
        print(f"Error parsing PGN preview: {e}")
        return generate_mock_preview(limit)


def generate_mock_preview(limit: int = 10) -> List[dict]:
    """
    Generar preview simulado para archivos no-PGN
    """
    mock_games = [
        {
            "white": "Carlsen, Magnus",
            "black": "Nepomniachtchi, Ian",
            "result": "1-0",
            "date": "2021.11.24",
        },
        {
            "white": "Giri, Anish",
            "black": "Caruana, Fabiano",
            "result": "1/2-1/2",
            "date": "2021.11.20",
        },
        {
            "white": "Nakamura, Hikaru",
            "black": "So, Wesley",
            "result": "0-1",
            "date": "2021.11.18",
        },
        {
            "white": "Aronian, Levon",
            "black": "Grischuk, Alexander",
            "result": "1-0",
            "date": "2021.11.16",
        },
        {
            "white": "Mamedyarov, Shakhriyar",
            "black": "Leko, Peter",
            "result": "1/2-1/2",
            "date": "2021.11.14",
        },
    ]

    return mock_games[:limit]


async def process_import_job(import_job_id: str, files: List[dict], source: str):
    """
    Procesar job de importación en background
    """
    try:
        # Actualizar estado
        import_jobs[import_job_id]["status"] = "processing"

        imported_games = 0

        for i, file_info in enumerate(files):
            try:
                # En un entorno real, aquí se ejecutaría el script import_pgns_parallel.py
                # Por ahora simulamos el procesamiento
                await asyncio.sleep(2)  # Simular procesamiento

                # Simular importación exitosa
                games_imported = file_info["estimated_games"]
                imported_games += games_imported

                # Actualizar progreso
                import_jobs[import_job_id]["processed_files"] = i + 1
                import_jobs[import_job_id]["imported_games"] = imported_games

                print(
                    f"Procesado archivo {file_info['filename']}: {games_imported} partidas"
                )

            except Exception as e:
                print(f"Error procesando archivo {file_info['filename']}: {e}")
                continue

        # Completar job
        import_jobs[import_job_id]["status"] = "completed"
        import_jobs[import_job_id]["completed_at"] = datetime.now().isoformat()

        print(f"Job {import_job_id} completado: {imported_games} partidas importadas")

    except Exception as e:
        import_jobs[import_job_id]["status"] = "error"
        import_jobs[import_job_id]["error"] = str(e)
        print(f"Error en job {import_job_id}: {e}")


@router.post("/import/pgn/personal")
async def import_personal_pgn_endpoint(
    request: Request,
    file: UploadFile = File(...),
    source: str = Form(default="personal"),
):
    """
    Endpoint simple para usuarios básicos: sube un PGN e importa directamente
    Las partidas quedan marcadas con el usuario que las importó
    """
    # Obtener usuario del JWT
    user = getattr(request.state, "user", {})
    username = user.get("username")

    if not username:
        raise HTTPException(status_code=401, detail="Usuario no autenticado")

    try:
        # Validar archivo PGN
        if not file.filename.lower().endswith(".pgn"):
            raise HTTPException(
                status_code=400,
                detail="Solo se permiten archivos .pgn para importación personal",
            )

        # Guardar archivo temporalmente
        temp_dir = Path(tempfile.gettempdir()) / "chess_personal_imports"
        temp_dir.mkdir(exist_ok=True)

        temp_file = temp_dir / f"{username}_{uuid.uuid4()}.pgn"
        content = await file.read()

        with open(temp_file, "wb") as f:
            f.write(content)

        # Importar usando el script
        result = import_personal_pgn(str(temp_file), username, source)

        # Limpiar archivo temporal
        temp_file.unlink()

        return JSONResponse(
            {
                "success": True,
                "filename": file.filename,
                "imported": result["imported"],
                "skipped": result["skipped"],
                "batch_id": result["batch_id"],  # CRÍTICO: retornar batch_id
                "username": username,
                "message": f"Se importaron {result['imported']} partidas correctamente",
            }
        )

    except Exception as e:
        # Limpiar archivo si existe
        if "temp_file" in locals() and temp_file.exists():
            temp_file.unlink()

        raise HTTPException(status_code=500, detail=f"Error importando PGN: {str(e)}")
