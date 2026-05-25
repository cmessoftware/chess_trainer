"""
🚀 Pipeline Completo ML con MLflow
Ejecuta todo el proceso: análisis → entrenamiento → predicciones
"""

import subprocess
import sys
from pathlib import Path
import logging
import time

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_script(script_path, description):
    """Ejecutar un script Python y manejar errores"""
    
    logger.info(f"🔄 Ejecutando: {description}")
    logger.info(f"   📄 Script: {script_path}")
    
    try:
        # Ejecutar script
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} - Completado")
            return True
        else:
            logger.error(f"❌ {description} - Error")
            logger.error(f"   STDOUT: {result.stdout[-500:]}")  # Últimas 500 chars
            logger.error(f"   STDERR: {result.stderr[-500:]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️ {description} - Timeout (5 min)")
        return False
    except Exception as e:
        logger.error(f"❌ {description} - Excepción: {e}")
        return False

def check_prerequisites():
    """Verificar prerequisitos del pipeline"""
    
    logger.info("🔍 Verificando prerequisitos...")
    
    # Verificar datasets
    required_datasets = [
        Path("data/processed/unified_all_sources.parquet"),
        Path("data/processed/unified_small_sources.parquet")
    ]
    
    dataset_available = False
    for dataset in required_datasets:
        if dataset.exists():
            logger.info(f"✅ Dataset encontrado: {dataset.name}")
            dataset_available = True
            break
    
    if not dataset_available:
        logger.error("❌ No se encontraron datasets. Ejecuta el pipeline de datos primero.")
        return False
    
    # Verificar MLflow (opcional)
    try:
        import mlflow
        logger.info("✅ MLflow disponible")
    except ImportError:
        logger.warning("⚠️ MLflow no instalado - continuando sin tracking")
    
    # Verificar scikit-learn
    try:
        import sklearn
        logger.info("✅ Scikit-learn disponible")
    except ImportError:
        logger.error("❌ Scikit-learn no instalado")
        return False
    
    logger.info("✅ Prerequisitos verificados")
    return True

def run_ml_pipeline():
    """Ejecutar pipeline completo de ML"""
    
    print("🚀 PIPELINE COMPLETO ML CON MLFLOW")
    print("=" * 50)
    
    # Verificar prerequisitos
    if not check_prerequisites():
        logger.error("❌ Prerequisitos no cumplidos")
        return False
    
    # Scripts a ejecutar en orden
    pipeline_steps = [
        {
            "script": "src/ml/explore_datasets.py",
            "description": "Análisis de Datasets",
            "required": True
        },
        {
            "script": "src/ml/train_basic_model.py", 
            "description": "Entrenamiento Básico",
            "required": True
        },
        {
            "script": "src/ml/make_predictions.py",
            "description": "Predicciones ML",
            "required": True
        }
    ]
    
    results = {}
    
    # Ejecutar cada paso
    for i, step in enumerate(pipeline_steps, 1):
        print(f"\n📊 PASO {i}/{len(pipeline_steps)}: {step['description']}")
        print("-" * 40)
        
        script_path = Path(step['script'])
        
        if not script_path.exists():
            logger.error(f"❌ Script no encontrado: {script_path}")
            if step['required']:
                return False
            continue
        
        # Ejecutar paso
        success = run_script(script_path, step['description'])
        results[step['description']] = success
        
        if not success and step['required']:
            logger.error(f"❌ Paso requerido falló: {step['description']}")
            return False
        
        # Pausa entre pasos
        time.sleep(2)
    
    # Reporte final
    print("\n📋 REPORTE FINAL DEL PIPELINE")
    print("=" * 50)
    
    success_count = sum(results.values())
    total_count = len(results)
    
    for step_name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {step_name}")
    
    print(f"\n🎯 Éxito: {success_count}/{total_count} pasos completados")
    
    if success_count == total_count:
        print("\n🎉 ¡PIPELINE COMPLETADO EXITOSAMENTE!")
        print("\n🌐 Próximos pasos:")
        print("   1. Revisar MLflow UI: http://localhost:5000")
        print("   2. Analizar predicciones generadas")
        print("   3. Optimizar hiperparámetros si es necesario")
        print("   4. Implementar predicciones en tiempo real")
        return True
    else:
        print("\n⚠️ Pipeline completado con errores")
        return False

def run_extended_experiments():
    """Ejecutar experimentos adicionales si están disponibles"""
    
    print("\n🧪 EXPERIMENTOS ADICIONALES")
    print("=" * 40)
    
    optional_scripts = [
        {
            "script": "src/ml/compare_sources.py",
            "description": "Comparación por Fuentes"
        },
        {
            "script": "src/ml/hyperparameter_tuning.py", 
            "description": "Optimización de Hiperparámetros"
        },
        {
            "script": "src/ml/tactical_experiment.py",
            "description": "Experimento Features Tácticas"
        }
    ]
    
    for script_info in optional_scripts:
        script_path = Path(script_info['script'])
        
        if script_path.exists():
            logger.info(f"🔬 Experimento disponible: {script_info['description']}")
            response = input(f"¿Ejecutar {script_info['description']}? (y/n): ")
            
            if response.lower() in ['y', 'yes', 's', 'si']:
                run_script(script_path, script_info['description'])
        else:
            logger.info(f"📝 Experimento no disponible: {script_info['description']}")

def main():
    """Función principal"""
    
    # Ejecutar pipeline básico
    success = run_ml_pipeline()
    
    if success:
        # Preguntar por experimentos adicionales
        print("\n" + "="*50)
        response = input("¿Ejecutar experimentos adicionales? (y/n): ")
        
        if response.lower() in ['y', 'yes', 's', 'si']:
            run_extended_experiments()
    
    print("\n🎯 Pipeline terminado")

if __name__ == "__main__":
    main()
