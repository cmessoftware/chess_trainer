from sqlalchemy import Column, Integer, String, Float, JSON, Boolean
from db.database import Base
from db.session import get_schema


class Features(Base):
    """
    Features model for move-by-move chess analysis.

    Structure: One record per analyzed move with detailed characteristics.
    Primary key: (game_id, move_number, player_color)

    This model stores granular move-level data for detailed analysis,
    machine learning feature extraction, and position evaluation.
    """

    __tablename__ = "features"
    __table_args__ = {"schema": get_schema()}

    # Composite primary key for move-level analysis
    game_id = Column(String, primary_key=True)
    move_number = Column(Integer, primary_key=True)
    player_color = Column(Integer, primary_key=True)

    # Move-specific data
    fen = Column(String, nullable=True)
    move_san = Column(String, nullable=True)
    move_uci = Column(String, nullable=True)
    error_label = Column(String, nullable=True)

    # Position characteristics
    material_balance = Column(Float, nullable=True)
    material_total = Column(Float, nullable=True)
    num_pieces = Column(Integer, nullable=True)
    branching_factor = Column(Integer, nullable=True)
    self_mobility = Column(Integer, nullable=True)
    opponent_mobility = Column(Integer, nullable=True)

    # Game phase and strategic factors
    phase = Column(String, nullable=True)
    has_castling_rights = Column(Integer, nullable=True)
    move_number_global = Column(Integer, nullable=True)
    is_repetition = Column(Integer, nullable=True)
    is_low_mobility = Column(Integer, nullable=True)
    is_center_controlled = Column(Integer, nullable=True)
    is_pawn_endgame = Column(Integer, nullable=True)

    # Evaluation and metadata
    tags = Column(JSON, nullable=True)
    score_diff = Column(Float, nullable=True)

    # Basic game info (for convenience, though redundant with games table)
    site = Column(String, nullable=True)
    event = Column(String, nullable=True)
    date = Column(String, nullable=True)
    white_player = Column(String, nullable=True)
    black_player = Column(String, nullable=True)
    result = Column(String, nullable=True)

    # Move metadata
    num_moves = Column(Integer, nullable=True)
    is_stockfish_test = Column(Boolean, nullable=False, default=False)

    def get_position_features(self):
        """Get position-specific features for ML"""
        return {
            "material_balance": self.material_balance,
            "material_total": self.material_total,
            "num_pieces": self.num_pieces,
            "branching_factor": self.branching_factor,
            "self_mobility": self.self_mobility,
            "opponent_mobility": self.opponent_mobility,
        }

    def get_strategic_features(self):
        """Get strategic features for analysis"""
        return {
            "phase": self.phase,
            "has_castling_rights": self.has_castling_rights,
            "is_repetition": self.is_repetition,
            "is_low_mobility": self.is_low_mobility,
            "is_center_controlled": self.is_center_controlled,
            "is_pawn_endgame": self.is_pawn_endgame,
        }

    def is_critical_position(self):
        """Determine if this is a critical position worth studying"""
        return (
            self.error_label is not None  # Position with identified errors
            or (
                self.score_diff and abs(self.score_diff) > 100
            )  # Significant evaluation change
            or (self.branching_factor and self.branching_factor > 30)  # High complexity
        )
