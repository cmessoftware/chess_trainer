"""
Script para inicializar las tablas de MLflow en PostgreSQL usando alembic.
"""
import os
import sys
import logging
from pathlib import Path
import alembic.config
import sqlalchemy as sa
from sqlalchemy import inspect

# Añadir path de src
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.repository.mlflow_repository import mlflow_repo

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_mlflow_tables():
    """Verifica si las tablas de MLflow ya existen en la base de datos"""
    connection_string = mlflow_repo.get_connection_string()
    engine = sa.create_engine(connection_string)
    inspector = inspect(engine)
    
    # Tablas principales de MLflow
    mlflow_tables = [
        "experiments", 
        "runs", 
        "tags", 
        "params", 
        "metrics"
    ]
    
    existing_tables = inspector.get_table_names()
    missing_tables = [table for table in mlflow_tables if table not in existing_tables]
    
    if missing_tables:
        logger.info(f"Faltan tablas de MLflow: {missing_tables}")
        return False
    else:
        logger.info("Todas las tablas de MLflow existen")
        return True

def initialize_mlflow_db():
    """Inicializa la base de datos de MLflow"""
    # MLflow creará sus tablas automáticamente la primera vez que se use
    # Este script es para verificar y asegurar que todo esté configurado correctamente
    
    # Primero verificamos la conexión
    if not mlflow_repo.test_connection():
        logger.error("No se pudo conectar a PostgreSQL")
        return False
    
    # Verificar si las tablas ya existen
    tables_exist = check_mlflow_tables()
    
    if tables_exist:
        logger.info("Las tablas de MLflow ya están configuradas en PostgreSQL")
        return True
    
    # Si no existen, informamos que se crearán automáticamente
    logger.info("Las tablas de MLflow se crearán automáticamente al iniciar el servidor MLflow")
    logger.info("Asegúrate de que el servicio mlflow esté configurado con el backend de PostgreSQL")
    
    return True

if __name__ == "__main__":
    if initialize_mlflow_db():
        logger.info("✅ Verificación de base de datos MLflow completada")
    else:
        logger.error("❌ Error en la verificación de base de datos MLflow")
        sys.exit(1)
