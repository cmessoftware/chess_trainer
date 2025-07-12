from src.db.database import SessionLocal, engine, Base
from src.db import models, crud

# Crear tablas si no existen
Base.metadata.create_all(bind=engine)

# Probar la conexión
db = SessionLocal()
nuevo = crud.crear_cliente(db, nombre="Sergio", email="sergio@ejemplo.com")
print("✅ Cliente creado:", nuevo.nombre)
db.close()
