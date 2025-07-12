from sqlalchemy.orm import Session
from . import models


#Ejemplo de CRUD para manejar clientes en una base de datos SQLAlchemy
def get_clientes(db: Session):
    return db.query(models.Cliente).all()

def get_cliente_por_id(db: Session, cliente_id: int):
    return db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()

def crear_cliente(db: Session, nombre: str, email: str):
    nuevo = models.Cliente(nombre=nombre, email=email)
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo
