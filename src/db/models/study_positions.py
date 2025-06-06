from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base

class Study_positions(Base):
    __tablename__ = 'study_positions'

    id = Column(Integer, primary_key=True)
    study_id = Column(String)
    fen = Column(String)
    comment = Column(String)
    is_critical = Column(Integer)
