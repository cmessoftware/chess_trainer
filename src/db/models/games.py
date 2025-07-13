# db/models/games.py
from sqlalchemy import Column, String
from db.database import Base
from db.session import get_schema


class Games(Base):
    __tablename__ = "games"
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, primary_key=True)
    pgn = Column(String)
    source = Column(String)
    white_player = Column(String)
    black_player = Column(String)
    white_elo = Column(String)
    black_elo = Column(String)
    result = Column(String)
    time_control = Column(String)
    opening = Column(String)
    eco = Column(String)
    date_played = Column(String)
    created_at = Column(String)
