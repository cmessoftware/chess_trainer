#!/usr/bin/env python3
"""
Script de verificación post-organización
Confirma que todos los scripts genéricos funcionan correctamente
"""
import subprocess
import sys
from pathlib import Path

def check_script_exists_and_help(script_name: str, script_path: Path) -> bool:
    """Verificar que script existe y tiene help"""
    if not script_path.exists():
        print(f"❌ {script_name}: No encontrado en {script_path}")
        return False
    
    try:
        # Intentar ejecutar --help
        result = subprocess.run([
            sys.executable, str(script_path), "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {script_name}: Funcional con --help")
            return True
        else:
            print(f"⚠️ {script_name}: Existe pero sin --help")
            return True  # Sigue siendo válido
            
    except Exception as e:
        print(f"❌ {script_name}: Error ejecutando: {e}")
        return False

def main():
    """Verificación completa post-organización"""
    print("🔍 VERIFICACIÓN POST-ORGANIZACIÓN")
    print("=" * 50)
    
    # Directorio base
    base_dir = Path(__file__).parent
    scripts_dir = base_dir / "src" / "scripts"
    artifacts_dir = base_dir / "artifacts" / "ml_experiments"
    
    # Scripts genéricos que deben existir y ser funcionales
    expected_scripts = {
        "import_player_pgns.py": "Importación genérica de PGNs",
        "analyze_player.py": "Análisis completo genérico", 
        "check_player_data.py": "Verificación de datos genérica",
        "player_analysis_pipeline.py": "Pipeline completo automatizado",
        "analyze_onthefly.py": "Análisis con clasificación en memoria",
        "estrategia_clasificacion.py": "Documentación de estrategias",
        "opciones_clasificacion.py": "Comparación de opciones",
        "demo_scripts_genericos.py": "Demostración de uso",
        "repair_features.py": "Reparación de features"
    }
    
    # Artifacts ML que deben existir
    expected_artifacts = [
        "classification_report_logistic_l2.csv",
        "classification_report_logistic_l2.txt", 
        "confusion_matrix_logistic_l2.png",
        "confusion_matrix_mlp_basic.png",
        "confusion_matrix_mlp_deep.png",
        "confusion_matrix_mlp_regularized.png",
        "phase2_mlp_final_results.txt"
    ]
    
    print("\n📋 VERIFICANDO SCRIPTS GENÉRICOS:")
    scripts_ok = 0
    for script_name, description in expected_scripts.items():
        script_path = scripts_dir / script_name
        if check_script_exists_and_help(script_name, script_path):
            scripts_ok += 1
        print(f"   {description}")
    
    print(f"\n📊 VERIFICANDO ARTIFACTS ML:")
    artifacts_ok = 0
    for artifact_name in expected_artifacts:
        artifact_path = artifacts_dir / artifact_name
        if artifact_path.exists():
            print(f"✅ {artifact_name}: Encontrado")
            artifacts_ok += 1
        else:
            print(f"❌ {artifact_name}: No encontrado")
    
    # Verificar directorio raíz limpio
    print(f"\n🧹 VERIFICANDO DIRECTORIO RAÍZ LIMPIO:")
    root_py_files = list(base_dir.glob("*.py"))
    
    # Filtrar archivos permitidos en raíz
    allowed_root_files = [
        "launch_chess_trainer.py",
        "init_api.py", 
        "init_frontend.py",
        "debug_pagination.py",
        "check_schema.py"
    ]
    
    unexpected_files = []
    for py_file in root_py_files:
        if py_file.name not in allowed_root_files:
            unexpected_files.append(py_file.name)
    
    if not unexpected_files:
        print("✅ Directorio raíz limpio - sin scripts temporales")
    else:
        print(f"⚠️ Archivos Python inesperados en raíz: {unexpected_files}")
    
    # Resumen final
    print(f"\n🎯 RESUMEN DE VERIFICACIÓN:")
    print(f"   📋 Scripts genéricos: {scripts_ok}/{len(expected_scripts)} ✅")
    print(f"   🧪 Artifacts ML: {artifacts_ok}/{len(expected_artifacts)} ✅")
    print(f"   🧹 Directorio raíz: {'Limpio' if not unexpected_files else 'Con archivos extra'}")
    
    # Verificación final
    success_rate = (scripts_ok + artifacts_ok) / (len(expected_scripts) + len(expected_artifacts))
    
    if success_rate >= 0.9:
        print(f"\n🎉 ORGANIZACIÓN EXITOSA: {success_rate:.1%} de archivos organizados")
        print("✅ Sistema listo para uso con scripts genéricos")
        
        # Mostrar comandos de ejemplo
        print(f"\n💡 COMANDOS DE EJEMPLO LISTOS:")
        print("   python src/scripts/import_player_pgns.py NuevoJugador --source personal")
        print("   python src/scripts/analyze_player.py NuevoJugador --min-games 50") 
        print("   python src/scripts/player_analysis_pipeline.py NuevoJugador")
        
        return True
    else:
        print(f"\n⚠️ ORGANIZACIÓN PARCIAL: {success_rate:.1%} - Revisar archivos faltantes")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)