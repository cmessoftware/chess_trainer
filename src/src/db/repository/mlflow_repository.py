"""
MLflow Repository para integrar con PostgreSQL
Siguiendo el patrón de diseño repository para acceso a datos
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from db.database import Base, engine

logger = logging.getLogger(__name__)

class MLflowRepository:
    """Repositorio para almacenar metadatos de MLflow en PostgreSQL"""
    
    def __init__(self):
        """Inicializa el repositorio y la conexión a la base de datos"""
        self.engine = engine
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def get_connection_string(self):
        """Retorna la cadena de conexión a PostgreSQL para MLflow"""
        # Recuperar desde variables de entorno o usar valores por defecto de Docker
        db_user = os.environ.get("POSTGRES_USER", "chess")
        db_password = os.environ.get("POSTGRES_PASSWORD", "chess_pass")
        db_host = os.environ.get("POSTGRES_HOST", "postgres")
        db_port = os.environ.get("POSTGRES_PORT", "5432")
        db_name = os.environ.get("POSTGRES_DB", "chess_trainer_db")
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def test_connection(self):
        """Prueba la conexión a la base de datos"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                logger.info(f"PostgreSQL connection test successful: {result.fetchone()}")
                return True
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            return False
    
    def initialize_mlflow_tables(self):
        """Inicializa las tablas necesarias para MLflow si no existen"""
        # MLflow creará sus propias tablas automáticamente cuando se use
        # Este método está para futuras extensiones personalizadas
        logger.info("MLflow database tables will be initialized automatically")
        return True

# Singleton para acceso global
mlflow_repo = MLflowRepository()
