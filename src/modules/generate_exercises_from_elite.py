from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class ProcessedGame(Base):
    __tablename__ = 'processed_features'
    game_hash = Column(String, primary_key=True)
    date_processed = Column(DateTime(timezone=True), server_default=func.now())


# Ejemplo de creación de la tabla:
engine = create_engine('postgresql://usuario:contraseña@localhost:5432/tu_db')
Base.metadata.create_all(engine)
