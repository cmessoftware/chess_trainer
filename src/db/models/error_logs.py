# db/models/error_logs.py
from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from db.database import Base
from db.session import get_schema


class ErrorLog(Base):
    """
    Modelo para registro centralizado de errores del sistema.
    
    Permite trazabilidad de errores durante extracciones, procesamiento,
    y otras operaciones críticas.
    """
    __tablename__ = "error_logs"
    __table_args__ = {"schema": get_schema()}

    # Identificadores
    id = Column(String, primary_key=True)  # UUID
    user_id = Column(String, nullable=True, index=True)  # Usuario que triggereó la operación
    
    # Clasificación
    severity = Column(String, nullable=False)  # critical, error, warning, info
    category = Column(String, nullable=False)  # feature_extraction, import, database, auth, etc.
    
    # Contenido del error
    error_type = Column(String, nullable=False)  # Exception class name
    error_message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    
    # Contexto de ejecución
    meta_data = Column(JSON, nullable=True)  # job_id, batch_id, file, function, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Estado de resolución (para tracking futuro)
    resolved = Column(String, default="open", nullable=False)  # open, investigating, resolved, wont_fix
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)

    def __repr__(self):
        return f"<ErrorLog(id={self.id}, severity={self.severity}, category={self.category})>"
