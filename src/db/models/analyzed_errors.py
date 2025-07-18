from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base
from db.session import get_schema


class Analyzed_errors(Base):
    __tablename__ = 'analyzed_errors'
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, primary_key=True)
    date_analyzed = Column(String)
