from sqlalchemy import Column, Integer, String, Boolean
from .database import Base

#Ejemplo de modelo de cliente para una base de datos SQLAlchemy
class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    activo = Column(Boolean, default=True)
