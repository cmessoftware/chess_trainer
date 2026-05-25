from sqlalchemy import Column, Integer, String, Float, Boolean, TIMESTAMP, text
from db.database import Base
from db.session import get_schema


class GameAnalytics(Base):
    """
    Game Analytics model for aggregated game-level metrics.

    Structure: One record per game with comprehensive analysis.
    Primary key: id (auto-increment)
    Unique key: game_id

    This table contains aggregated statistics and metrics derived from
    move-by-move analysis, suitable for ML training and game evaluation.
    """

    __tablename__ = "game_analytics"
    __table_args__ = {"schema": get_schema()}

    # Primary key and basic identification
    id = Column(Integer, primary_key=True)
    game_id = Column(String(255), nullable=False, unique=True)
    source = Column(String(100), nullable=True)

    # Game metadata (redundant with games table but useful for analytics)
    white_elo = Column(Integer, nullable=True)
    black_elo = Column(Integer, nullable=True)
    time_control = Column(String(50), nullable=True)
    opening_name = Column(String(200), nullable=True)
    opening_eco = Column(String(10), nullable=True)
    game_result = Column(String(20), nullable=True)
    total_moves = Column(Integer, nullable=True)
    avg_move_time = Column(Float, nullable=True)

    # Move quality metrics per player
    blunders_white = Column(Integer, default=0, nullable=True)
    blunders_black = Column(Integer, default=0, nullable=True)
    mistakes_white = Column(Integer, default=0, nullable=True)
    mistakes_black = Column(Integer, default=0, nullable=True)
    inaccuracies_white = Column(Integer, default=0, nullable=True)
    inaccuracies_black = Column(Integer, default=0, nullable=True)
    brilliant_moves_white = Column(Integer, default=0, nullable=True)
    brilliant_moves_black = Column(Integer, default=0, nullable=True)
    good_moves_white = Column(Integer, default=0, nullable=True)
    good_moves_black = Column(Integer, default=0, nullable=True)
    book_moves_white = Column(Integer, default=0, nullable=True)
    book_moves_black = Column(Integer, default=0, nullable=True)
    best_moves_white = Column(Integer, default=0, nullable=True)
    best_moves_black = Column(Integer, default=0, nullable=True)

    # Accuracy and evaluation metrics
    accuracy_white = Column(Float, nullable=True)
    accuracy_black = Column(Float, nullable=True)
    avg_centipawn_loss_white = Column(Float, nullable=True)
    avg_centipawn_loss_black = Column(Float, nullable=True)

    # Time pressure and special moves
    time_pressure_moves_white = Column(Integer, default=0, nullable=True)
    time_pressure_moves_black = Column(Integer, default=0, nullable=True)
    castle_kingside_white = Column(Boolean, default=False, nullable=True)
    castle_queenside_white = Column(Boolean, default=False, nullable=True)
    castle_kingside_black = Column(Boolean, default=False, nullable=True)
    castle_queenside_black = Column(Boolean, default=False, nullable=True)
    en_passant_captures = Column(Integer, default=0, nullable=True)
    promotions_white = Column(Integer, default=0, nullable=True)
    promotions_black = Column(Integer, default=0, nullable=True)

    # Combat metrics
    checks_given_white = Column(Integer, default=0, nullable=True)
    checks_given_black = Column(Integer, default=0, nullable=True)
    pieces_captured_white = Column(Integer, default=0, nullable=True)
    pieces_captured_black = Column(Integer, default=0, nullable=True)
    material_advantage_white = Column(Float, default=0, nullable=True)
    material_advantage_black = Column(Float, default=0, nullable=True)

    # Position evaluation and tactics
    position_evaluation_final = Column(Float, nullable=True)
    tactical_motifs_count = Column(Integer, default=0, nullable=True)
    endgame_type = Column(String(50), nullable=True)

    # Strategic metrics
    pawn_structure_score_white = Column(Float, default=0, nullable=True)
    pawn_structure_score_black = Column(Float, default=0, nullable=True)
    king_safety_white = Column(Float, default=0, nullable=True)
    king_safety_black = Column(Float, default=0, nullable=True)
    piece_activity_white = Column(Float, default=0, nullable=True)
    piece_activity_black = Column(Float, default=0, nullable=True)
    center_control_white = Column(Float, default=0, nullable=True)
    center_control_black = Column(Float, default=0, nullable=True)
    development_speed_white = Column(Float, default=0, nullable=True)
    development_speed_black = Column(Float, default=0, nullable=True)
    space_advantage_white = Column(Float, default=0, nullable=True)
    space_advantage_black = Column(Float, default=0, nullable=True)

    # Metadata
    created_at = Column(
        TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), nullable=True
    )

    def get_player_quality_comparison(self):
        """Compare quality metrics between players"""
        return {
            "blunder_diff": (self.blunders_white or 0) - (self.blunders_black or 0),
            "mistake_diff": (self.mistakes_white or 0) - (self.mistakes_black or 0),
            "accuracy_diff": (self.accuracy_white or 0) - (self.accuracy_black or 0),
            "centipawn_loss_diff": (self.avg_centipawn_loss_white or 0)
            - (self.avg_centipawn_loss_black or 0),
        }

    def get_game_complexity_score(self):
        """Calculate game complexity based on tactical and strategic factors"""
        base_score = 0

        # Tactical complexity
        if self.tactical_motifs_count:
            base_score += self.tactical_motifs_count * 2

        # Move quality complexity
        total_errors = (
            (self.blunders_white or 0)
            + (self.blunders_black or 0)
            + (self.mistakes_white or 0)
            + (self.mistakes_black or 0)
        )
        base_score += total_errors

        # Special moves complexity
        special_moves = (
            (self.en_passant_captures or 0)
            + (self.promotions_white or 0)
            + (self.promotions_black or 0)
        )
        base_score += special_moves * 3

        # Game length factor
        if self.total_moves:
            if self.total_moves > 50:
                base_score += 10  # Long games are more complex

        return min(base_score, 100)  # Cap at 100

    def get_game_balance_score(self):
        """Calculate how balanced the game was"""
        if not self.accuracy_white or not self.accuracy_black:
            return None

        accuracy_diff = abs(self.accuracy_white - self.accuracy_black)

        # More balanced = lower difference
        balance_score = max(0, 100 - (accuracy_diff * 2))
        return balance_score

    def is_high_quality_game(self):
        """Determine if this is a high-quality game for training"""
        if not self.accuracy_white or not self.accuracy_black:
            return False

        # High quality criteria
        min_accuracy = min(self.accuracy_white, self.accuracy_black)
        avg_errors = (
            (self.blunders_white or 0)
            + (self.blunders_black or 0)
            + (self.mistakes_white or 0)
            + (self.mistakes_black or 0)
        ) / 2

        return (
            min_accuracy >= 75  # Both players reasonably accurate
            and avg_errors <= 3  # Not too many errors per player
            and (self.total_moves or 0) >= 20  # Reasonable game length
        )
