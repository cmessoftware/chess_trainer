# db/models/notifications.py
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from db.database import Base
from db.session import get_schema


class Notification(Base):
    """
    Modelo para notificaciones por usuario.
    
    Permite tracking de eventos del sistema (extracciones, errores, warnings)
    asociados a un usuario específico.
    """
    __tablename__ = "notifications"
    __table_args__ = {"schema": get_schema()}

    # Identificadores
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, nullable=False, index=True)  # Usuario propietario
    
    # Contenido
    type = Column(String, nullable=False)  # success, error, warning, info, processing
    status = Column(String, nullable=False)  # queued, processing, completed, failed
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    
    # Estado
    read = Column(Boolean, default=False, nullable=False)
    dismissed = Column(Boolean, default=False, nullable=False)
    
    # Metadata (JSON flexible para contexto adicional)
    meta_data = Column(JSON, nullable=True)  # job_id, batch_id, error_log_id, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Enlace opcional a error log
    error_log_id = Column(String, nullable=True, index=True)

    def to_dict(self):
        """Convertir notificación a diccionario JSON-serializable"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "status": self.status,
            "title": self.title,
            "message": self.message,
            "read": self.read,
            "dismissed": self.dismissed,
            "metadata": self.meta_data if self.meta_data is not None else {},
            "timestamp": self.created_at.isoformat() if self.created_at else None,
            "error_log_id": self.error_log_id,
        }

    def __repr__(self):
        return f"<Notification(id={self.id}, user={self.user_id}, type={self.type}, read={self.read})>"

