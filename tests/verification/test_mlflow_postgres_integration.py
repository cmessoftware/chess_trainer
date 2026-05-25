"""
Prueba de integración completa de MLflow con PostgreSQL
Este script valida todas las funcionalidades del sistema MLflow integrado.
"""
import os
import sys
import logging
from pathlib import Path
import mlflow
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Añadir path de src
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importar utilidades específicas del proyecto
from src.db.repository.mlflow_repository import mlflow_repo
from src.ml.mlflow_utils import ChessMLflowTracker

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_mlflow_postgres_connection():
    """Prueba la conexión a PostgreSQL para MLflow"""
    logger.info("Probando conexión a PostgreSQL...")
    success = mlflow_repo.test_connection()
    
    if success:
        logger.info("✅ Conexión a PostgreSQL exitosa")
    else:
        logger.error("❌ Error conectando a PostgreSQL")
        return False
    
    return True

def test_mlflow_tracking():
    """Prueba el tracking de MLflow con PostgreSQL"""
    logger.info("Configurando MLflow Tracker...")
    
    # Utilizar el tracker específico del proyecto
    tracker = ChessMLflowTracker()
    
    # Verificar que se pueden crear experimentos
    experiments = tracker.create_chess_experiments()
    if not experiments:
        logger.error("❌ No se pudieron crear los experimentos")
        return False
    
    logger.info(f"✅ Se crearon/verificaron {len(experiments)} experimentos")
    return True

def test_mlflow_experiment_run():
    """Ejecuta un experimento de prueba con MLflow"""
    logger.info("Ejecutando experimento de prueba...")
    
    # Crear datos sintéticos
    X = np.random.rand(100, 5)
    y = np.random.randint(0, 3, 100)  # Clasificación con 3 clases
    
    # Dividir en train/test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Crear un modelo
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    
    # Crear DataFrame para el tracking
    df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(X.shape[1])])
    df["target"] = y
    
    # Iniciar experimento
    experiment_name = "chess_error_prediction"
    mlflow.set_experiment(experiment_name)
    
    # Realizar tracking
    with mlflow.start_run(run_name="test_integration") as run:
        # Entrenar modelo
        model.fit(X_train, y_train)
        
        # Evaluar
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Log de parámetros y métricas
        mlflow.log_param("n_estimators", model.n_estimators)
        mlflow.log_param("random_state", 42)
        mlflow.log_param("test_size", 0.2)
        
        mlflow.log_metric("accuracy", accuracy)
        
        # Log del modelo
        mlflow.sklearn.log_model(model, "random_forest_model")
        
        # Obtener run_id
        run_id = run.info.run_id
    
    logger.info(f"✅ Experimento completado. Run ID: {run_id}, Accuracy: {accuracy:.4f}")
    return True

def test_mlflow_model_registry():
    """Prueba el registro de modelos en MLflow"""
    logger.info("Probando registro de modelos...")
    
    # Crear datos sintéticos
    X = np.random.rand(100, 5)
    y = np.random.randint(0, 3, 100)
    
    # Crear modelo
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    # Registrar modelo
    with mlflow.start_run(run_name="model_registry_test") as run:
        mlflow.sklearn.log_model(
            model, 
            "random_forest_model",
            registered_model_name="chess_error_classifier"
        )
        run_id = run.info.run_id
    
    logger.info(f"✅ Modelo registrado correctamente. Run ID: {run_id}")
    return True

def run_integration_tests():
    """Ejecuta todas las pruebas de integración"""
    tests = [
        ("Conexión PostgreSQL", test_mlflow_postgres_connection),
        ("MLflow Tracking", test_mlflow_tracking),
        ("Experimento MLflow", test_mlflow_experiment_run),
        ("Registro de Modelos", test_mlflow_model_registry)
    ]
    
    results = []
    
    logger.info("=" * 60)
    logger.info("INICIANDO PRUEBAS DE INTEGRACIÓN MLFLOW CON POSTGRESQL")
    logger.info("=" * 60)
    
    for name, test_func in tests:
        logger.info(f"\n▶️ Ejecutando prueba: {name}")
        try:
            success = test_func()
            results.append((name, success))
            if success:
                logger.info(f"✅ Prueba '{name}' exitosa")
            else:
                logger.error(f"❌ Prueba '{name}' fallida")
        except Exception as e:
            logger.error(f"❌ Error en prueba '{name}': {e}")
            results.append((name, False))
    
    # Mostrar resumen
    logger.info("\n" + "=" * 60)
    logger.info("RESUMEN DE PRUEBAS")
    logger.info("=" * 60)
    
    all_success = True
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {name}")
        if not success:
            all_success = False
    
    if all_success:
        logger.info("\n✅ TODAS LAS PRUEBAS PASARON CORRECTAMENTE")
        logger.info("La integración de MLflow con PostgreSQL está funcionando correctamente")
    else:
        logger.error("\n❌ ALGUNAS PRUEBAS FALLARON")
        logger.error("Revisa los errores anteriores para solucionar los problemas")
    
    return all_success

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
