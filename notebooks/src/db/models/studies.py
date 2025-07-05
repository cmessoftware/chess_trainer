from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base
from db.session import get_schema


class Studies(Base):
    __tablename__ = 'studies'
    __table_args__ = {"schema": get_schema()}

    study_id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(String)
    tags = Column(String)
    source = Column(String)
    created_at = Column(String)
