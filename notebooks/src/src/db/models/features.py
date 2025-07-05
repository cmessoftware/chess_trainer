from sqlalchemy import Column, Integer, String, Float, JSON, Boolean
from db.database import Base
from db.session import get_schema


class Features(Base):
    __tablename__ = 'features'
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, primary_key=True)
    move_number = Column(Integer, primary_key=True)
    player_color = Column(Integer, primary_key=True)

    fen = Column(String, nullable=True)
    move_san = Column(String, nullable=True)
    move_uci = Column(String, nullable=True)
    error_label = Column(String, nullable=True)
    material_balance = Column(Float, nullable=True)
    material_total = Column(Float, nullable=True)
    num_pieces = Column(Integer, nullable=True)
    branching_factor = Column(Integer, nullable=True)
    self_mobility = Column(Integer, nullable=True)
    opponent_mobility = Column(Integer, nullable=True)
    phase = Column(String, nullable=True)
    has_castling_rights = Column(Integer, nullable=True)
    move_number_global = Column(Integer, nullable=True)
    is_repetition = Column(Integer, nullable=True)
    is_low_mobility = Column(Integer, nullable=True)
    is_center_controlled = Column(Integer, nullable=True)
    is_pawn_endgame = Column(Integer, nullable=True)

    tags = Column(JSON, nullable=True)
    score_diff = Column(Float, nullable=True)

    site = Column(String, nullable=True)
    event = Column(String, nullable=True)
    date = Column(String, nullable=True)
    #TODO: Eliminar white_player y black_player (redundantes, ya están en games)
    white_player = Column(String, nullable=True)
    black_player = Column(String, nullable=True)
    result = Column(String, nullable=True)

    num_moves = Column(Integer, nullable=True)
    is_stockfish_test = Column(Boolean, nullable=False, default=False)
