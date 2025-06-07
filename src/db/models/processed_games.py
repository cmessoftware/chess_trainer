from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from sqlalchemy.orm import declarative_base

from db.session import get_schema

Base = declarative_base()


class Processed_games(Base):
    __tablename__ = 'processed_games'
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, primary_key=True)
