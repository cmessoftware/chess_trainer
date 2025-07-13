# /app/src/db/models/chapter.py
from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(String, index=True)
    title = Column(String)
    pgn = Column(String)
    tags = Column(JSON, nullable=True)
