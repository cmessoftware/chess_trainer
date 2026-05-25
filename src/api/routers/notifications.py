"""
Router para manejo de notificaciones del sistema
Integra con el servicio de notificaciones existente
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from services.notification_service import get_notification_service, NotificationService

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# Modelos de datos
class NotificationCreate(BaseModel):
    title: str
    message: str
    type: Optional[str] = "info"  # info, success, warning, error, report_ready
    metadata: Optional[Dict] = None


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    type: str
    read: bool
    created_at: datetime
    metadata: Optional[Dict] = None


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 20,
    user_id: str = "system",  # En producción, obtener del JWT
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Obtener notificaciones del usuario
    """
    try:
        notifications = await notification_service.get_user_notifications(
            user_id=user_id, unread_only=unread_only, limit=limit
        )

        return [
            NotificationResponse(
                id=n["id"],
                user_id=n["user_id"],
                title=n["title"],
                message=n["message"],
                type=n["type"],
                read=n["read"],
                created_at=datetime.fromisoformat(n["created_at"]),
                metadata=n.get("metadata"),
            )
            for n in notifications
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread/count")
async def get_unread_count(
    user_id: str = "system",  # En producción, obtener del JWT
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Obtener conteo de notificaciones no leídas
    """
    try:
        count = await notification_service.get_unread_count(user_id)
        return {"unread_count": count}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
async def create_notification(
    notification: NotificationCreate,
    user_id: str = "system",  # En producción, obtener del JWT
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Crear nueva notificación
    """
    try:
        notification_id = await notification_service.create_notification(
            user_id=user_id,
            title=notification.title,
            message=notification.message,
            type=notification.type,
            metadata=notification.metadata,
        )

        return {
            "success": True,
            "notification_id": notification_id,
            "message": "Notificación creada exitosamente",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user_id: str = "system",  # En producción, obtener del JWT
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Marcar notificación como leída
    """
    try:
        success = await notification_service.mark_as_read(user_id, notification_id)

        if success:
            return {"success": True, "message": "Notificación marcada como leída"}
        else:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/read-all")
async def mark_all_as_read(
    user_id: str = "system",  # En producción, obtener del JWT
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Marcar todas las notificaciones como leídas
    """
    try:
        count = await notification_service.mark_all_as_read(user_id)

        return {
            "success": True,
            "marked_count": count,
            "message": f"{count} notificaciones marcadas como leídas",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    user_id: str = "system",  # En producción, obtener del JWT
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Eliminar notificación
    """
    try:
        success = await notification_service.delete_notification(
            user_id, notification_id
        )

        if success:
            return {"success": True, "message": "Notificación eliminada"}
        else:
            raise HTTPException(status_code=404, detail="Notificación no encontrada")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test")
async def create_test_notification(
    user_id: str = "system",
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Crear notificación de prueba (solo para desarrollo)
    """
    try:
        notification_id = await notification_service.create_notification(
            user_id=user_id,
            title="Notificación de Prueba",
            message="Esta es una notificación de prueba del sistema.",
            type="info",
            metadata={"test": True, "timestamp": datetime.now().isoformat()},
        )

        return {
            "success": True,
            "notification_id": notification_id,
            "message": "Notificación de prueba creada",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report-ready")
async def notify_report_ready(
    player_name: str,
    job_id: str,
    report_type: str = "análisis completo",
    user_id: str = "system",
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Crear notificación específica para reporte listo
    """
    try:
        notification_id = await notification_service.create_report_ready_notification(
            user_id=user_id,
            player_name=player_name,
            job_id=job_id,
            report_type=report_type,
        )

        return {
            "success": True,
            "notification_id": notification_id,
            "message": f"Notificación de reporte listo para {player_name}",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
async def cleanup_old_notifications(
    days: int = 30,
    notification_service: NotificationService = Depends(get_notification_service),
):
    """
    Limpiar notificaciones antiguas
    """
    try:
        deleted_count = await notification_service.cleanup_old_notifications(days)

        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Eliminadas {deleted_count} notificaciones antiguas (>{days} días)",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
