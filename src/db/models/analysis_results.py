# db/models/analysis_results.py
"""
Modelo para almacenar resultados de análisis ML por partida.

Permite persistir predicciones y métricas para evitar recálculos costosos
y facilitar tracking histórico de análisis por jugador.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Index
from sqlalchemy.sql import func
from db.database import Base
from db.session import get_schema


class AnalysisResult(Base):
    """
    Resultados de análisis ML para una partida específica.

    Almacena:
    - Predicción de nivel de error general
    - Confianza del modelo
    - Distribución de errores por tipo (blunder/mistake/inaccuracy)
    - Metadata para evitar re-procesamiento
    """

    __tablename__ = "analysis_results"
    __table_args__ = (
        Index("idx_analysis_username", "username"),
        Index("idx_analysis_game_id", "game_id"),
        Index("idx_analysis_date", "analyzed_at"),
        Index("idx_analysis_user_date", "username", "analyzed_at"),
        {"schema": get_schema()},
    )

    # Identificador
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relación con partida
    game_id = Column(String, nullable=False, index=True)

    # Usuario analizado (puede diferir de imported_by si es análisis de oponente)
    username = Column(String(100), nullable=False, index=True)

    # Resultado del análisis
    error_level = Column(
        String(50),
        nullable=False,
        comment="Nivel global: blunder_prone, mistake_prone, accurate, excellent",
    )

    prediction_confidence = Column(
        Float,
        nullable=True,
        comment="Confianza del modelo en la predicción (0.0 - 1.0)",
    )

    # Métricas de la partida analizada
    total_moves = Column(
        Integer, nullable=True, comment="Total de jugadas analizadas en la partida"
    )

    blunder_count = Column(
        Integer, nullable=True, comment="Cantidad de blunders detectados"
    )

    mistake_count = Column(
        Integer, nullable=True, comment="Cantidad de mistakes detectados"
    )

    inaccuracy_count = Column(
        Integer, nullable=True, comment="Cantidad de inaccuracies detectadas"
    )

    good_move_count = Column(
        Integer, nullable=True, comment="Cantidad de jugadas buenas/excelentes"
    )

    # Métricas adicionales
    average_centipawn_loss = Column(
        Float, nullable=True, comment="Pérdida promedio en centipawns por jugada"
    )

    accuracy_percentage = Column(
        Float, nullable=True, comment="Porcentaje de precisión general (0-100)"
    )

    # Timestamps
    analyzed_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """Convertir a diccionario JSON-serializable para API"""
        return {
            "id": self.id,
            "game_id": self.game_id,
            "username": self.username,
            "error_level": self.error_level,
            "prediction_confidence": (
                float(self.prediction_confidence)
                if self.prediction_confidence
                else None
            ),
            "total_moves": self.total_moves,
            "blunder_count": self.blunder_count,
            "mistake_count": self.mistake_count,
            "inaccuracy_count": self.inaccuracy_count,
            "good_move_count": self.good_move_count,
            "average_centipawn_loss": (
                float(self.average_centipawn_loss)
                if self.average_centipawn_loss
                else None
            ),
            "accuracy_percentage": (
                float(self.accuracy_percentage) if self.accuracy_percentage else None
            ),
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (
            f"<AnalysisResult("
            f"id={self.id}, "
            f"game_id='{self.game_id}', "
            f"username='{self.username}', "
            f"error_level='{self.error_level}', "
            f"confidence={self.prediction_confidence:.2f if self.prediction_confidence else 0.0}"
            f")>"
        )
