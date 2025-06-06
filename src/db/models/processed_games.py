from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Processed_games(Base):
    __tablename__ = 'processed_games'

    game_id = Column(String, primary_key=True)
