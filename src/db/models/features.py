from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base

class Features(Base):
    __tablename__ = 'features'

    game_id = Column(String, primary_key=True)
    move_number = Column(Integer)
    fen = Column(String)
    move_san = Column(String)
    move_uci = Column(String)
    material_balance = Column(Float)
    material_total = Column(Float)
    num_pieces = Column(Integer)
    branching_factor = Column(Integer)
    self_mobility = Column(Integer)
    opponent_mobility = Column(Integer)
    phase = Column(String)
    player_color = Column(String)
    has_castling_rights = Column(Integer)
    move_number_global = Column(Integer)
    is_repetition = Column(Integer)
    is_low_mobility = Column(Integer)
    is_center_controlled = Column(Integer)
    is_pawn_endgame = Column(Integer)
    tags = Column(String)
    score_diff = Column(Float)
