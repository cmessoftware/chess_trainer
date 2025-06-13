# db/models/games.py
from sqlalchemy import Column, String
from db.database import Base
from db.session import get_schema


class Games(Base):
    __tablename__ = "games"
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, primary_key=True)
    pgn = Column(String)
    site = Column(String)
    event = Column(String)
    date = Column(String)
    white_player = Column(String)
    white_elo = Column(String)  # Nuevo: Elo del jugador blanco
    black_player = Column(String)
    black_elo = Column(String)  # Nuevo
    result = Column(String)
    eco = Column(String)              # Nuevo: código ECO
    opening = Column(String)          # Nuevo: descripción apertura
