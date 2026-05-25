"""
Servicio para manejo de notificaciones del sistema
Integra con el sistema existente de notificaciones
"""

from typing import List, Dict, Optional
from datetime import datetime
import uuid
import json

class NotificationService:
    def __init__(self):
        # En producción, esto debería usar una base de datos real
        # Por ahora mantenemos compatibilidad con el sistema existente
        self.notifications_store = {}
    
    async def create_notification(
        self,
        user_id: str,
        title: str,
        message: str,
        type: str = "info",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Crear nueva notificación
        
        Args:
            user_id: ID del usuario destinatario
            title: Título de la notificación
            message: Mensaje de la notificación
            type: Tipo (info, success, warning, error, report_ready)
            metadata: Datos adicionales
        
        Returns:
            ID de la notificación creada
        """
        notification_id = str(uuid.uuid4())
        
        notification = {
            "id": notification_id,
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type,
            "read": False,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        if user_id not in self.notifications_store:
            self.notifications_store[user_id] = []
        
        self.notifications_store[user_id].append(notification)
        
        # Mantener solo las últimas 50 notificaciones por usuario
        if len(self.notifications_store[user_id]) > 50:
            self.notifications_store[user_id] = self.notifications_store[user_id][-50:]
        
        return notification_id
    
    async def get_user_notifications(
        self, 
        user_id: str, 
        unread_only: bool = False,
        limit: int = 20
    ) -> List[Dict]:
        """
        Obtener notificaciones de un usuario
        
        Args:
            user_id: ID del usuario
            unread_only: Solo notificaciones no leídas
            limit: Máximo número de notificaciones
        
        Returns:
            Lista de notificaciones
        """
        if user_id not in self.notifications_store:
            return []
        
        notifications = self.notifications_store[user_id]
        
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        # Ordenar por fecha de creación (más recientes primero)
        notifications.sort(key=lambda x: x["created_at"], reverse=True)
        
        return notifications[:limit]
    
    async def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """
        Marcar notificación como leída
        
        Args:
            user_id: ID del usuario
            notification_id: ID de la notificación
        
        Returns:
            True si se marcó exitosamente
        """
        if user_id not in self.notifications_store:
            return False
        
        for notification in self.notifications_store[user_id]:
            if notification["id"] == notification_id:
                notification["read"] = True
                return True
        
        return False
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Marcar todas las notificaciones como leídas
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Número de notificaciones marcadas
        """
        if user_id not in self.notifications_store:
            return 0
        
        count = 0
        for notification in self.notifications_store[user_id]:
            if not notification["read"]:
                notification["read"] = True
                count += 1
        
        return count
    
    async def get_unread_count(self, user_id: str) -> int:
        """
        Obtener conteo de notificaciones no leídas
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Número de notificaciones no leídas
        """
        if user_id not in self.notifications_store:
            return 0
        
        return len([n for n in self.notifications_store[user_id] if not n["read"]])
    
    async def delete_notification(self, user_id: str, notification_id: str) -> bool:
        """
        Eliminar notificación
        
        Args:
            user_id: ID del usuario
            notification_id: ID de la notificación
        
        Returns:
            True si se eliminó exitosamente
        """
        if user_id not in self.notifications_store:
            return False
        
        original_length = len(self.notifications_store[user_id])
        self.notifications_store[user_id] = [
            n for n in self.notifications_store[user_id] 
            if n["id"] != notification_id
        ]
        
        return len(self.notifications_store[user_id]) < original_length
    
    async def create_report_ready_notification(
        self, 
        user_id: str, 
        player_name: str, 
        job_id: str,
        report_type: str = "análisis completo"
    ) -> str:
        """
        Crear notificación específica para reporte listo
        
        Args:
            user_id: ID del usuario
            player_name: Nombre del jugador analizado
            job_id: ID del job completado
            report_type: Tipo de reporte generado
        
        Returns:
            ID de la notificación creada
        """
        title = f"Reporte de {player_name} completado"
        message = f"El {report_type} para el jugador {player_name} está listo para descargar."
        
        metadata = {
            "job_id": job_id,
            "player_name": player_name,
            "report_type": report_type,
            "action_url": f"/api/reports/download/{job_id}",
            "action_text": "Descargar reporte"
        }
        
        return await self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            type="report_ready",
            metadata=metadata
        )
    
    async def create_report_failed_notification(
        self, 
        user_id: str, 
        player_name: str, 
        job_id: str,
        error_message: str
    ) -> str:
        """
        Crear notificación para reporte fallido
        
        Args:
            user_id: ID del usuario
            player_name: Nombre del jugador
            job_id: ID del job fallido
            error_message: Mensaje de error
        
        Returns:
            ID de la notificación creada
        """
        title = f"Error generando reporte de {player_name}"
        message = f"No se pudo completar el análisis: {error_message}"
        
        metadata = {
            "job_id": job_id,
            "player_name": player_name,
            "error_message": error_message,
            "action_url": f"/reports/retry/{job_id}",
            "action_text": "Reintentar"
        }
        
        return await self.create_notification(
            user_id=user_id,
            title=title,
            message=message,
            type="error",
            metadata=metadata
        )
    
    async def cleanup_old_notifications(self, days: int = 30) -> int:
        """
        Limpiar notificaciones antiguas
        
        Args:
            days: Días de antigüedad para eliminar
        
        Returns:
            Número de notificaciones eliminadas
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for user_id in list(self.notifications_store.keys()):
            original_length = len(self.notifications_store[user_id])
            
            self.notifications_store[user_id] = [
                n for n in self.notifications_store[user_id]
                if datetime.fromisoformat(n["created_at"]).timestamp() > cutoff_date
            ]
            
            deleted_count += original_length - len(self.notifications_store[user_id])
            
            # Eliminar entrada si no hay notificaciones
            if not self.notifications_store[user_id]:
                del self.notifications_store[user_id]
        
        return deleted_count

# Instancia global del servicio (singleton)
_notification_service = None

def get_notification_service() -> NotificationService:
    """Obtener instancia global del servicio de notificaciones"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service