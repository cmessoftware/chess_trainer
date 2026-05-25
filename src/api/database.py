import os
import dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Cargar variables de entorno
dotenv.load_dotenv()

# URL de la base de datos PostgreSQL
DATABASE_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db")

# Crear motor de base de datos
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Dependency para obtener sesión de base de datos
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()