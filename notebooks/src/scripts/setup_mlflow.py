#!/usr/bin/env python3
"""
Script de configuración inicial de MLflow para chess_trainer.
Crea experimentos predefinidos y verifica la conexión.
"""

import sys
sys.path.append('/chess_trainer/src')

import logging
from ml.mlflow_utils import ChessMLflowTracker

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def setup_chess_mlflow():
    """
    Configuración inicial de MLflow para chess_trainer.
    Crea experimentos y verifica conectividad.
    """
    print("🚀 Configurando MLflow para Chess Trainer...")
    print("=" * 50)
    
    try:
        # Inicializar tracker
        print("📡 Conectando a MLflow...")
        tracker = ChessMLflowTracker()
        
        # Crear experimentos
        print("🧪 Creando experimentos...")
        experiments = tracker.create_chess_experiments()
        
        if experiments:
            print(f"✅ {len(experiments)} experimentos configurados:")
            for name, exp_id in experiments:
                print(f"   - {name} (ID: {exp_id})")
        
        # Verificar conexión
        print("\n🔍 Verificando configuración...")
        try:
            client = tracker.client
            all_experiments = client.search_experiments()
            chess_experiments = [exp for exp in all_experiments if 'chess_' in exp.name]
            
            print(f"✅ {len(chess_experiments)} experimentos de ajedrez encontrados")
            print("✅ Conexión a MLflow verificada")
            
        except Exception as e:
            print(f"⚠️ Error verificando configuración: {e}")
        
        print("\n🎯 Próximos pasos:")
        print("1. Abrir MLflow UI: http://localhost:5000")
        print("2. Ejecutar primer entrenamiento: python src/ml/train_error_model.py")
        print("3. Revisar experimentos en la UI")
        
        print("\n✅ MLflow configurado correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error configurando MLflow: {e}")
        logger.error(f"Setup failed: {e}")
        return False

def verify_mlflow_setup():
    """
    Verificar que MLflow esté funcionando correctamente.
    """
    print("\n🔧 Verificando setup de MLflow...")
    
    try:
        tracker = ChessMLflowTracker()
        
        # Test básico de conectividad
        experiments = tracker.client.search_experiments()
        print(f"✅ Conectividad OK - {len(experiments)} experimentos encontrados")
        
        # Verificar experimentos de chess
        chess_exp_names = [
            "chess_error_prediction",
            "chess_accuracy_prediction", 
            "chess_phase_classification"
        ]
        
        missing_experiments = []
        for exp_name in chess_exp_names:
            try:
                exp = tracker.client.get_experiment_by_name(exp_name)
                if exp:
                    print(f"✅ {exp_name} - OK")
                else:
                    missing_experiments.append(exp_name)
            except Exception:
                missing_experiments.append(exp_name)
        
        if missing_experiments:
            print(f"⚠️ Experimentos faltantes: {missing_experiments}")
            print("💡 Ejecuta setup_chess_mlflow() para crearlos")
        else:
            print("✅ Todos los experimentos de chess están configurados")
        
        return len(missing_experiments) == 0
        
    except Exception as e:
        print(f"❌ Error en verificación: {e}")
        return False

def test_mlflow_logging():
    """
    Test rápido de logging en MLflow.
    """
    print("\n🧪 Test de logging...")
    
    try:
        import mlflow
        ChessMLflowTracker()  # Solo para verificar conectividad
        
        # Test run básico
        mlflow.set_experiment("chess_error_prediction")
        
        with mlflow.start_run(run_name="test_setup"):
            # Log parámetros de prueba
            mlflow.log_param("test_param", "setup_test")
            mlflow.log_param("model_type", "test")
            
            # Log métricas de prueba
            mlflow.log_metric("test_metric", 0.95)
            mlflow.log_metric("accuracy", 0.85)
            
            print("✅ Test logging completado")
            
        print("✅ MLflow logging funciona correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error en test logging: {e}")
        return False

if __name__ == "__main__":
    print("🎮 CHESS TRAINER - MLflow Setup")
    print("================================")
    
    # Verificar si MLflow está disponible
    try:
        import mlflow
        print(f"✅ MLflow instalado: versión {mlflow.__version__}")
    except ImportError:
        print("❌ MLflow no está instalado")
        print("💡 Instalar con: pip install mlflow[extras]")
        sys.exit(1)
    
    # Setup principal
    setup_success = setup_chess_mlflow()
    
    if setup_success:
        # Verificación
        verify_success = verify_mlflow_setup()
        
        if verify_success:
            # Test de logging
            test_success = test_mlflow_logging()
            
            if test_success:
                print("\n🎉 Setup completo - MLflow listo para usar!")
                print("🌐 Abrir UI: http://localhost:5000")
            else:
                print("\n⚠️ Setup básico OK, pero hay problemas con logging")
        else:
            print("\n⚠️ Setup completado con advertencias")
    else:
        print("\n❌ Setup falló - revisar configuración")
        sys.exit(1)
