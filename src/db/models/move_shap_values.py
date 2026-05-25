# db/models/move_shap_values.py
"""
Modelo para almacenar valores SHAP por jugada individual.

Permite explicabilidad move-level: para cada jugada de una partida analizada,
almacena los valores SHAP de cada feature, facilitando:
- Explicación detallada de por qué una jugada fue clasificada como error
- Comparación de impacto de features entre jugadas
- Dashboard interactivo de análisis move-by-move
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Index, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import Base
from db.session import get_schema


class MoveShapValue(Base):
    """
    Valores SHAP individuales por jugada y feature.

    Cada registro representa la contribución de una feature específica
    a la predicción ML para una jugada concreta, permitiendo explicar
    en detalle por qué el modelo clasificó la jugada como error.
    """

    __tablename__ = "move_shap_values"
    __table_args__ = (
        Index("idx_move_shap_analysis", "analysis_id"),
        Index("idx_move_shap_move_number", "move_number"),
        Index("idx_move_shap_feature", "feature_name"),
        Index("idx_move_shap_analysis_move", "analysis_id", "move_number"),
        {"schema": get_schema()},
    )

    # Identificador
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Relación con análisis (FK a analysis_results)
    analysis_id = Column(
        Integer, nullable=False, index=True, comment="FK a analysis_results.id"
    )

    # Identificación de la jugada dentro de la partida
    move_number = Column(
        Integer,
        nullable=False,
        index=True,
        comment="Número de jugada en la partida (1-indexed)",
    )

    # Feature explicada
    feature_name = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Nombre de la feature (e.g., 'material_balance', 'self_mobility')",
    )

    # Valor SHAP
    shap_value = Column(
        Float,
        nullable=False,
        comment="Contribución de la feature a la predicción (puede ser +/-)",
    )

    # Valor base de la feature (para contexto adicional)
    feature_value = Column(
        Float,
        nullable=True,
        comment="Valor original de la feature en esta jugada (antes de SHAP)",
    )

    # Error predicho por el modelo ML
    error_label = Column(
        String(50),
        nullable=True,
        index=True,
        comment="Error predicho por ML (blunder/mistake/inaccuracy/good)",
    )

    # Contexto del movimiento (para análisis LLM y reportes)
    move_san = Column(
        String(20),
        nullable=True,
        comment="Movimiento en notación algebraica (e.g., 'Nf3', 'e4', 'O-O')",
    )

    move_uci = Column(
        String(10),
        nullable=True,
        comment="Movimiento en notación UCI (e.g., 'e2e4', 'e7e8q')",
    )

    fen = Column(
        String(100),
        nullable=True,
        comment="Posición FEN antes del movimiento",
    )

    player_color = Column(
        String(10),
        nullable=True,
        comment="Color del jugador que hizo el movimiento ('white' o 'black')",
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def to_dict(self):
        """Convertir a diccionario JSON-serializable para API"""
        return {
            "id": self.id,
            "analysis_id": self.analysis_id,
            "move_number": self.move_number,
            "feature_name": self.feature_name,
            "shap_value": float(self.shap_value) if self.shap_value else None,
            "feature_value": float(self.feature_value) if self.feature_value else None,
            "error_label": self.error_label,
            "move_san": self.move_san,  # Notación del movimiento
            "move_uci": self.move_uci,  # UCI notation
            "fen": self.fen,  # Posición FEN
            "player_color": self.player_color,  # Color del jugador ('white'/'black')
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        move_info = f", move='{self.move_san}'" if self.move_san else ""
        return (
            f"<MoveShapValue("
            f"id={self.id}, "
            f"analysis_id={self.analysis_id}, "
            f"move_number={self.move_number}{move_info}, "
            f"feature='{self.feature_name}', "
            f"shap={self.shap_value:.4f}"
            f")>"
        )
