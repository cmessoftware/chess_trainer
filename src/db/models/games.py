# db/models/games.py

from sqlalchemy import Column, String, Integer
from db.database import Base
from db.session import get_schema


class Games(Base):
    __tablename__ = 'games'
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, primary_key=True)  # ⬆️ Clave primaria obligatoria
    white_player = Column(String)
    black_player = Column(String)
    white_elo = Column(Integer)
    black_elo = Column(Integer)
    result = Column(String)
    event = Column(String)
    site = Column(String)
    date = Column(String)
    eco = Column(String)
    opening = Column(String)
    pgn = Column(String)
