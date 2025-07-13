"""
Utilidad para inicializar y gestionar MLflow con PostgreSQL
"""
import os
import sys
import logging
from pathlib import Path

# Añadir el path de src para importaciones
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.repository.mlflow_repository import mlflow_repo

def setup_mlflow_backend():
    """Configura MLflow para usar PostgreSQL como backend"""
    # Verifica la conexión a la base de datos
    if not mlflow_repo.test_connection():
        logging.error("No se pudo conectar a PostgreSQL para MLflow")
        return False
    
    # Obtiene la cadena de conexión para MLflow
    db_uri = mlflow_repo.get_connection_string()
    
    # Configura las variables de entorno para MLflow
    os.environ["MLFLOW_TRACKING_URI"] = db_uri
    
    # Define ubicación de artefactos
    artifact_location = os.environ.get("MLFLOW_ARTIFACT_ROOT", "/mlflow/mlruns")
    os.environ["MLFLOW_ARTIFACT_ROOT"] = artifact_location
    
    logging.info(f"MLflow configurado con PostgreSQL: {db_uri}")
    logging.info(f"MLflow artifacts: {artifact_location}")
    
    return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Si se ejecuta como script, configura MLflow
    if setup_mlflow_backend():
        logging.info("✅ MLflow configurado correctamente con PostgreSQL")
    else:
        logging.error("❌ Error configurando MLflow con PostgreSQL")
        sys.exit(1)
