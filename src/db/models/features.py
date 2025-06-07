# db/models/features.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from db.database import Base
from db.session import get_schema


class Features(Base):
    __tablename__ = 'features'
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, ForeignKey(
        f"{get_schema()}.games.game_id"), primary_key=True)
    move_number = Column(Integer, primary_key=True)
    player_color = Column(String, primary_key=True)  # 'white' o 'black'

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
    has_castling_rights = Column(Integer)
    move_number_global = Column(Integer)

    is_repetition = Column(Integer)
    is_low_mobility = Column(Integer)
    is_center_controlled = Column(Integer)
    is_pawn_endgame = Column(Integer)

    # Flexible: puede contener ["pin", "fork"] o estructuras complejas
    tags = Column(JSON)
    score_diff = Column(Float)

    # Opcionales para evitar JOINs constantes con `games`
    site = Column(String)
    event = Column(String)
    date = Column(String)
    white_player = Column(String)
    black_player = Column(String)
    result = Column(String)
