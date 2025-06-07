from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from sqlalchemy.ext.declarative import declarative_base

from db.session import get_schema

Base = declarative_base()


class Tactical_exercises(Base):
    __tablename__ = 'tactical_exercises'
    __table_args__ = {"schema": get_schema()}

    id = Column(String, primary_key=True)
    fen = Column(String, nullable=False)
    move = Column(String, nullable=False)
    uci = Column(String, nullable=False)
    tags = Column(String, nullable=False)
    source_game_id = Column(String)
