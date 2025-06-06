from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base

class Analyzed_errors(Base):
    __tablename__ = 'analyzed_errors'

    game_id = Column(String, primary_key=True)
    date_analyzed = Column(String)
