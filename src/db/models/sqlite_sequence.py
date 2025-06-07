from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base
from db.session import get_schema


class Sqlite_sequence(Base):
    __tablename__ = 'sqlite_sequence'
    __table_args__ = {"schema": get_schema()}
