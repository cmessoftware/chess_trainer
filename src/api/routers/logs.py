from fastapi import APIRouter, HTTPException, Request, Query, Body
from models.schemas import (
    LogEvent,
    LogEventResponse,
    LogsListRequest,
    LogsListResponse,
)
from services.log_service import LogService
from typing import Optional
import logging
from datetime import datetime

router = APIRouter()

# Instancia del servicio de logging
log_service = LogService()


@router.post("/chess", response_model=LogEventResponse)
async def log_chess_event(request: Request, event: LogEvent = Body(...)):
    """
    Registrar evento del tablero de ajedrez
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})

    try:
        # Agregar información del usuario al evento
        event.user_id = user.get("username", "anonymous")

        # Registrar el evento
        log_entry = await log_service.log_event(
            module=event.module,
            action=event.action,
            user_id=event.user_id,
            data=event.data,
        )

        logging.info(
            f"Evento registrado: {event.module}.{event.action} por {event.user_id}"
        )

        return LogEventResponse(
            log_id=log_entry["id"],
            module=log_entry["module"],
            action=log_entry["action"],
            user_id=log_entry["user_id"],
            data=log_entry["data"],
            timestamp=log_entry["timestamp"],
        )

    except Exception as e:
        logging.error(f"Error registrando evento: {e}")
        raise HTTPException(status_code=500, detail="Error registrando evento")


@router.get("/chess", response_model=LogsListResponse)
async def get_chess_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
):
    """
    Obtener logs del módulo de ajedrez (solo para admin)
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})

    # Verificar permisos de administrador
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403, detail="Solo administradores pueden ver logs"
        )

    try:
        logs_data = await log_service.get_logs(
            module="chess", action=action, user_id=user_id, limit=limit, offset=offset
        )

        return LogsListResponse(**logs_data)

    except Exception as e:
        logging.error(f"Error obteniendo logs: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo logs")


@router.get("/", response_model=LogsListResponse)
async def get_all_logs(
    request: Request,
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Obtener todos los logs del sistema (solo para admin)
    """
    # Usuario simulado cuando no hay middleware JWT
    user = getattr(request.state, "user", {"username": "test_user", "role": "admin"})

    # Verificar permisos de administrador
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=403, detail="Solo administradores pueden ver logs"
        )

    try:
        logs_data = await log_service.get_logs(
            module=module, action=action, user_id=user_id, limit=limit, offset=offset
        )

        return LogsListResponse(**logs_data)

    except Exception as e:
        logging.error(f"Error obteniendo logs: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo logs")


# =======================================
# ENDPOINTS TEMPORALES PARA TESTING SIN AUTH
# =======================================


@router.post("/test/chess", response_model=LogEventResponse)
async def log_chess_event_no_auth(event: LogEvent = Body(...)):
    """
    Endpoint temporal para testing - Registrar evento sin autenticación
    """
    logging.info(f"[TEST] Registrando evento sin autenticación")

    try:
        event.user_id = event.user_id or "test_user"

        log_entry = await log_service.log_event(
            module=event.module,
            action=event.action,
            user_id=event.user_id,
            data=event.data,
        )

        return LogEventResponse(
            log_id=log_entry["id"],
            module=log_entry["module"],
            action=log_entry["action"],
            user_id=log_entry["user_id"],
            data=log_entry["data"],
            timestamp=log_entry["timestamp"],
        )

    except Exception as e:
        logging.error(f"Error registrando evento: {e}")
        raise HTTPException(status_code=500, detail="Error registrando evento")


@router.get("/test/chess", response_model=LogsListResponse)
async def get_chess_logs_no_auth(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
):
    """
    Endpoint temporal para testing - Obtener logs sin autenticación
    """
    logging.info(f"[TEST] Obteniendo logs sin autenticación")

    try:
        logs_data = await log_service.get_logs(
            module="chess", action=action, user_id=user_id, limit=limit, offset=offset
        )

        return LogsListResponse(**logs_data)

    except Exception as e:
        logging.error(f"Error obteniendo logs: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo logs")
