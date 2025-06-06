from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base

class Tactical_exercises(Base):
    __tablename__ = 'tactical_exercises'

    id = Column(String, primary_key=True)
    fen = Column(String, nullable=False)
    move = Column(String, nullable=False)
    uci = Column(String, nullable=False)
    tags = Column(String, nullable=False)
    source_game_id = Column(String)
