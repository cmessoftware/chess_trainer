from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import declarative_base

from db.session import get_schema

Base = declarative_base()


class Processed_features(Base):
    __tablename__ = 'processed_features'
    __table_args__ = {"schema": get_schema()}

    game_id = Column(String, primary_key=True)
    date_processed = Column(DateTime, nullable=False)
