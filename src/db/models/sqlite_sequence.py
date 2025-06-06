from sqlalchemy import Column, Integer, String, Float, DateTime, LargeBinary
from db.database import Base

class Sqlite_sequence(Base):
    __tablename__ = 'sqlite_sequence'


