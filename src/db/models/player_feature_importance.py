# db/models/player_feature_importance.py
"""
Modelo para almacenar importancia agregada de features por jugador.

Este modelo permite analizar qué features impactan más las predicciones ML
a nivel longitudinal para cada jugador, facilitando:
- Dashboard global de feature importance
- Comparaciones entre jugadores
- Evolución temporal de impacto de features
- Base para módulo conversacional futuro (CTCE)
"""
from sqlalchemy import Column, String, Float, Integer, Date, DateTime, Index
from sqlalchemy.sql import func
from db.database import Base
from db.session import get_schema


class PlayerFeatureImportance(Base):
    """
    Importancia SHAP agregada por feature y jugador.

    Almacena valores SHAP promediados para cada feature, permitiendo identificar
    qué aspectos del juego (material, movilidad, táctica, etc.) tienen mayor
    impacto en los errores de cada jugador específico.
    """

    __tablename__ = "player_feature_importance"
    __table_args__ = (
        Index("idx_pfi_username", "username"),
        Index("idx_pfi_feature", "feature_name"),
        Index("idx_pfi_period", "period_start", "period_end"),
        {"schema": get_schema()},
    )

    # Identificador
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Identificación del jugador
    username = Column(String(100), nullable=False, index=True)

    # Feature analizada
    feature_name = Column(String(100), nullable=False, index=True)

    # Valores SHAP agregados
    mean_shap_value = Column(
        Float,
        nullable=False,
        comment="SHAP promedio (puede ser negativo - reduce error probability)",
    )
    mean_abs_shap_value = Column(
        Float,
        nullable=False,
        comment="SHAP absoluto promedio (magnitud de impacto sin dirección)",
    )

    # Metadatos estadísticos
    total_samples = Column(
        Integer,
        nullable=False,
        comment="Cantidad de jugadas/partidas analizadas para este agregado",
    )

    # Período de análisis (para análisis longitudinales)
    period_start = Column(Date, nullable=True, index=True)
    period_end = Column(Date, nullable=True, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self):
        """Convertir a diccionario JSON-serializable para API"""
        return {
            "id": self.id,
            "username": self.username,
            "feature_name": self.feature_name,
            "mean_shap_value": (
                float(self.mean_shap_value) if self.mean_shap_value else None
            ),
            "mean_abs_shap_value": (
                float(self.mean_abs_shap_value) if self.mean_abs_shap_value else None
            ),
            "total_samples": self.total_samples,
            "period_start": (
                self.period_start.isoformat() if self.period_start else None
            ),
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return (
            f"<PlayerFeatureImportance("
            f"id={self.id}, "
            f"username='{self.username}', "
            f"feature='{self.feature_name}', "
            f"mean_abs_shap={self.mean_abs_shap_value:.4f}"
            f")>"
        )
