#!/usr/bin/env python3
"""
Script de demostración de uso de scripts genéricos
Muestra ejemplos de análisis con diferentes jugadores
"""
import sys
import subprocess
from pathlib import Path

def run_demo_command(description: str, command: list, show_output: bool = True):
    """Ejecutar comando de demostración"""
    print(f"\n🔍 {description}")
    print(f"💻 Comando: {' '.join(command)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=60)
        
        if show_output:
            if result.stdout:
                print(result.stdout)
            if result.stderr and result.returncode != 0:
                print(f"ERROR: {result.stderr}")
        
        print(f"✅ Completado (código: {result.returncode})")
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Timeout - comando tomó demasiado tiempo")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Demostración de scripts genéricos"""
    print("🚀 DEMOSTRACIÓN DE SCRIPTS GENÉRICOS DE ANÁLISIS")
    print("=" * 80)
    print("Esta demostración muestra cómo usar los scripts genéricos")
    print("para analizar diferentes tipos de jugadores.")
    print()
    
    # Cambiar al directorio src
    src_dir = Path(__file__).parent.parent / "src"
    subprocess.run(["cd", str(src_dir)], shell=True)
    
    # Demostración 1: Verificación de datos
    run_demo_command(
        "VERIFICACIÓN DE DATOS - Th3Hound", 
        [sys.executable, "scripts/check_player_data.py", "Th3Hound", "--details"],
        show_output=True
    )
    
    # Demostración 2: Análisis seco (dry-run) 
    run_demo_command(
        "PIPELINE SECO - Magnus (Simulado)",
        [sys.executable, "scripts/player_analysis_pipeline.py", "Magnus", 
         "--source", "elite", "--dry-run"],
        show_output=True
    )
    
    # Demostración 3: Análisis rápido con datos existentes
    run_demo_command(
        "ANÁLISIS RÁPIDO - Th3Hound (Solo básico)",
        [sys.executable, "scripts/analyze_player.py", "Th3Hound", 
         "--min-games", "50", "--output-dir", "../reports"],
        show_output=False  # Ya vimos el output antes
    )
    
    print(f"\n🎯 RESUMEN DE LA DEMOSTRACIÓN")
    print("=" * 50)
    print("✅ Script de verificación: check_player_data.py")
    print("✅ Script de análisis: analyze_player.py") 
    print("✅ Pipeline completo: player_analysis_pipeline.py")
    print("✅ Script de importación: import_player_pgns.py")
    print()
    
    print("📚 EJEMPLOS DE USO ADICIONALES:")
    print("# Importar datos de nuevo jugador:")
    print("python scripts/import_player_pgns.py NuevoJugador --source personal")
    print()
    print("# Pipeline completo para jugador elite:")
    print("python scripts/player_analysis_pipeline.py Magnus --source elite --min-games 100")
    print()
    print("# Verificar cualquier jugador:")
    print("python scripts/check_player_data.py CualquierJugador --details")
    print()
    print("# Análisis personalizado:")
    print("python scripts/analyze_player.py MiJugador --min-games 20 --output-dir mis_reportes")
    print()
    
    print("🎯 TODOS LOS SCRIPTS SON GENÉRICOS Y REUTILIZABLES")
    print("   ✅ Sin datos hardcodeados")
    print("   ✅ Parámetros configurables")
    print("   ✅ Funcionan con cualquier jugador") 
    print("   ✅ Manejo de errores robusto")
    print("\n🎉 ¡DEMOSTRACIÓN COMPLETADA!")

if __name__ == "__main__":
    main()