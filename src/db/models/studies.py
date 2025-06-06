from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base

class Studies(Base):
    __tablename__ = 'studies'

    study_id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(String)
    tags = Column(String)
    source = Column(String)
    created_at = Column(String)
