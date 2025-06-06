from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Games(Base):
    __tablename__ = 'games'

    game_id = Column(String, primary_key=True)
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
    tags = Column(String)
