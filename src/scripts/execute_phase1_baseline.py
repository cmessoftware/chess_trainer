#!/usr/bin/env python3
"""
Script de ejecución para Phase 1 Baseline con tracking detallado
=================================================================

Este script ejecuta el baseline de Phase 1 con:
- Logging detallado del progreso
- Tracking en MLflow (local)
- Validación de criterios de avance
- Reporte final con recomendaciones

Uso:
    python execute_phase1_baseline.py

Requirements:
- PostgreSQL corriendo en localhost:5432
- MLflow configurado (local file-based)
- Datos etiquetados en tabla 'features'
"""

import os
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.ml.phase1_baseline import Phase1BaselineTrainer


def check_prerequisites():
    """Verificar que requisitos estén listos"""
    
    print("🔍 Verificando prerequisites...")
    
    # 1. PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="chess_trainer_db",
            user="chess",
            password="chess_pass"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM features WHERE error_label IS NOT NULL")
        labeled_count = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ PostgreSQL conectado")
        print(f"   Datos etiquetados: {labeled_count} registros")
        
        if labeled_count == 0:
            print("⚠️ WARNING: No hay datos etiquetados en la tabla 'features'")
            print("   Necesitas ejecutar el pipeline de feature engineering primero")
            return False
            
    except Exception as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        print("   Asegúrate de que Docker esté corriendo: docker-compose up -d postgres")
        return False
    
    # 2. MLflow
    try:
        import mlflow
        print(f"✅ MLflow instalado (versión {mlflow.__version__})")
    except ImportError:
        print("❌ MLflow no instalado")
        print("   Instala con: pip install mlflow")
        return False
    
    # 3. Scikit-learn
    try:
        import sklearn
        print(f"✅ Scikit-learn instalado (versión {sklearn.__version__})")
    except ImportError:
        print("❌ Scikit-learn no instalado")
        print("   Instala con: pip install scikit-learn")
        return False
    
    return True


def main():
    """Función principal de ejecución"""
    
    print("=" * 70)
    print("CHESS TRAINER - PHASE 1 BASELINE EXECUTION")
    print("=" * 70)
    print()
    
    # Verificar prerequisites
    if not check_prerequisites():
        print("\nPrerequisites no cumplidos. Abortando ejecución.")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("INICIANDO ENTRENAMIENTO")
    print("=" * 70)
    print()
    
    try:
        # Crear trainer
        trainer = Phase1BaselineTrainer(experiment_name="chess_trainer_phase1_baseline")
        
        # Entrenar todos los modelos
        print("🏋️ Entrenando modelos...")
        results = trainer.train_all_models()
        
        print("\n" + "=" * 70)
        print("✅ EJECUCIÓN COMPLETADA CON ÉXITO")
        print("=" * 70)
        print()
        
        # Mostrar URL de MLflow
        print("📊 Revisar experimentos en MLflow:")
        print("   http://localhost:5000")
        print()
        
        # Siguiente paso
        print("🎯 PRÓXIMOS PASOS:")
        print("   1. Revisar métricas en MLflow UI")
        print("   2. Validar criterios de avance (F1>0.70, confusión<5%)")
        print("   3. Si criterios OK → Continuar a Phase 2 (Deep Learning)")
        print("   4. Si criterios NO OK → Revisar feature engineering")
        print()
        
    except KeyboardInterrupt:
        print("\n⚠️ Ejecución interrumpida por usuario")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ ERROR DURANTE EJECUCIÓN:")
        print(f"   {e}")
        print()
        print("Stack trace:")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
