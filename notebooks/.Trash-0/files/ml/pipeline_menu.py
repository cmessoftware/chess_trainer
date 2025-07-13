"""
🎯 Pipeline Simplificado de Predicciones
Script consolidado para ejecutar todo el flujo de predicciones
"""

import sys
from pathlib import Path

def main():
    """Ejecutar pipeline simplificado"""
    
    print("🎯 PIPELINE SIMPLIFICADO DE PREDICCIONES")
    print("=" * 60)
    
    print("\n🚀 PASOS DISPONIBLES:")
    print("1. 🔮 Hacer predicciones simples (recomendado)")
    print("2. 🎮 Predicciones interactivas")
    print("3. 📊 Explorar datasets")
    print("4. � Pipeline completo con MLflow (NUEVO)")
    print("5. �🔄 Pipeline completo automatizado")
    print("6. 🚪 Salir")
    
    while True:
        try:
            choice = input("\n🎯 Elige una opción (1-6): ").strip()
            
            if choice == '1':
                print("\n🔮 Ejecutando predicciones simples...")
                import subprocess
                result = subprocess.run([
                    sys.executable, "src/ml/simple_predictions.py"
                ], cwd=Path.cwd())
                if result.returncode == 0:
                    print("\n✅ Predicciones completadas")
                else:
                    print("\n❌ Error en predicciones")
            
            elif choice == '2':
                print("\n🎮 Iniciando predicciones interactivas...")
                import subprocess
                subprocess.run([
                    sys.executable, "src/ml/interactive_predictions.py"
                ], cwd=Path.cwd())
            
            elif choice == '3':
                print("\n📊 Explorando datasets...")
                import subprocess
                result = subprocess.run([
                    sys.executable, "src/ml/explore_datasets.py"
                ], cwd=Path.cwd())
                if result.returncode == 0:
                    print("\n✅ Exploración completada")
                else:
                    print("\n❌ Error en exploración")
            
            elif choice == '4':
                print("\n🚀 Ejecutando pipeline MLflow completo...")
                print("💡 Asegúrate de que MLflow esté ejecutándose:")
                print("   docker-compose up -d mlflow")
                print("\n🔄 Iniciando tutorial MLflow...")
                import subprocess
                subprocess.run([
                    sys.executable, "src/ml/mlflow_complete_tutorial.py"
                ], cwd=Path.cwd())
            
            elif choice == '5':
                print("\n🔄 Ejecutando pipeline completo...")
                import subprocess
                subprocess.run([
                    sys.executable, "src/ml/run_complete_pipeline.py"
                ], cwd=Path.cwd())
            
            elif choice == '6':
                print("\n👋 ¡Hasta luego!")
                break
            
            else:
                print("   ⚠️  Opción no válida. Elige 1-6.")
                
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
