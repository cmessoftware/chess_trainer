from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Text,
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    ARRAY,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    roles = Column(ARRAY(String(50)), nullable=False, default=[])
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    last_login = Column(DateTime, nullable=True)
    profile_data = Column(JSON, nullable=True)

    # Relationships
    sessions = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_jti = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="sessions")


class Games(Base):
    __tablename__ = "games"

    game_id = Column(String, primary_key=True)
    pgn = Column(Text)
    site = Column(String)
    event = Column(String)
    date = Column(String)
    white_player = Column(String)
    white_elo = Column(String)
    black_player = Column(String)
    black_elo = Column(String)
    result = Column(String)
    eco = Column(String)
    opening = Column(String)
    source = Column(String)
    imported_by = Column(String, index=True)  # Usuario que importó la partida


class Features(Base):
    __tablename__ = "features"

    game_id = Column(String, primary_key=True)
    move_number = Column(Integer, primary_key=True)
    player_color = Column(Integer, primary_key=True)

    fen = Column(String)
    move_san = Column(String)
    move_uci = Column(String)
    error_label = Column(String)
    material_balance = Column(Float)
    material_total = Column(Float)
    num_pieces = Column(Integer)
    branching_factor = Column(Integer)
    self_mobility = Column(Integer)
    opponent_mobility = Column(Integer)
    phase = Column(String)
    has_castling_rights = Column(Integer)
    move_number_global = Column(Integer)
    is_repetition = Column(Integer)
    is_low_mobility = Column(Integer)
    is_center_controlled = Column(Integer)
    is_pawn_endgame = Column(Integer)
    tags = Column(JSON)
    score_diff = Column(Float)
    num_moves = Column(Integer)
    is_stockfish_test = Column(Boolean, default=False)


class TacticalExercises(Base):
    __tablename__ = "tactical_exercises"

    id = Column(String, primary_key=True)
    fen = Column(String, nullable=False)
    move = Column(String, nullable=False)
    uci = Column(String, nullable=False)
    tags = Column(String, nullable=False)
    source_game_id = Column(String)
