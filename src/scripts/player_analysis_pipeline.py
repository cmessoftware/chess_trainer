#!/usr/bin/env python3
"""
Pipeline completo de análisis de jugador
Automatiza: importación -> features -> análisis 
Uso: python player_analysis_pipeline.py <player_name> [opciones]
"""
import sys
import argparse
import subprocess
import time
from pathlib import Path

# Agregar el directorio src al path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

def run_script(script_name: str, args: list) -> tuple[bool, str]:
    """Ejecutar un script y retornar éxito y output"""
    try:
        # Construir comando
        script_path = Path(__file__).parent / script_name
        cmd = [sys.executable, str(script_path)] + args
        
        print(f"🔄 Ejecutando: {' '.join(cmd)}")
        
        # Ejecutar con timeout
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5 minutos timeout
            cwd=Path(__file__).parent.parent  # Ejecutar desde src/
        )
        
        if result.returncode == 0:
            print("✅ Completado exitosamente")
            return True, result.stdout
        else:
            print(f"❌ Error (código {result.returncode})")
            print(f"STDERR: {result.stderr}")
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        print("⏰ Timeout ejecutando script")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ Error ejecutando script: {e}")
        return False, str(e)

def check_prerequisites():
    """Verificar que los scripts necesarios existan"""
    scripts_dir = Path(__file__).parent
    required_scripts = [
        "import_player_pgns.py",
        "check_player_data.py", 
        "analyze_player.py"
    ]
    
    missing = []
    for script in required_scripts:
        if not (scripts_dir / script).exists():
            missing.append(script)
    
    if missing:
        print(f"❌ Scripts faltantes: {', '.join(missing)}")
        return False
    
    return True

def main():
    """Función principal del pipeline"""
    parser = argparse.ArgumentParser(
        description='Pipeline completo de análisis de jugador',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python player_analysis_pipeline.py Th3Hound
  python player_analysis_pipeline.py Magnus --source elite --force-reimport
  python player_analysis_pipeline.py hikaru --min-games 20 --skip-features
        """
    )
    
    # Argumentos principales
    parser.add_argument('player_name', help='Nombre del jugador a analizar')
    
    # Opciones de importación
    parser.add_argument('--source', default='personal',
                       choices=['personal', 'elite', 'novice', 'stockfish', 'fide'],
                       help='Fuente de PGNs (default: personal)')
    parser.add_argument('--data-dir', default='data/games',
                       help='Directorio base de juegos')
    
    # Opciones de pipeline
    parser.add_argument('--skip-import', action='store_true',
                       help='Saltar importación de PGNs')
    parser.add_argument('--skip-features', action='store_true',
                       help='Saltar generación de features')
    parser.add_argument('--force-reimport', action='store_true',
                       help='Forzar re-importación incluso si ya existen datos')
    
    # Opciones de análisis
    parser.add_argument('--min-games', type=int, default=50,
                       help='Mínimo juegos para análisis (default: 50)')
    parser.add_argument('--output-dir', default='../reports',
                       help='Directorio de reportes (default: ../reports)')
    
    # Opciones de ejecución
    parser.add_argument('--dry-run', action='store_true',
                       help='Mostrar qué se ejecutaría sin hacerlo')
    
    args = parser.parse_args()
    
    print("🚀 PIPELINE DE ANÁLISIS DE JUGADOR")
    print("=" * 60)
    print(f"📋 Jugador: {args.player_name}")
    print(f"📁 Fuente: {args.source}")
    print(f"🎯 Mínimo juegos: {args.min_games}")
    print()
    
    if args.dry_run:
        print("🔍 MODO DRY-RUN - Solo mostrando pasos")
        print()
    
    # Verificar prerequisitos
    if not check_prerequisites():
        return 1
    
    pipeline_success = True
    
    # PASO 1: Verificar datos existentes
    print("📊 PASO 1: Verificando datos existentes...")
    if not args.dry_run:
        success, output = run_script('check_player_data.py', [args.player_name, '--details'])
        if not success and not args.force_reimport:
            print("❌ Error verificando datos. Use --force-reimport para continuar.")
            return 1
    else:
        print(f"   Ejecutaría: check_player_data.py {args.player_name} --details")
    
    # PASO 2: Importar PGNs (si es necesario)
    if not args.skip_import:
        print(f"\n📥 PASO 2: Importando PGNs de {args.source}...")
        import_args = [args.player_name, '--source', args.source, '--data-dir', args.data_dir]
        
        if not args.dry_run:
            success, output = run_script('import_player_pgns.py', import_args)
            if not success:
                print("⚠️ Error en importación, continuando...")
                pipeline_success = False
        else:
            print(f"   Ejecutaría: import_player_pgns.py {' '.join(import_args)}")
    else:
        print("\n⏭️ PASO 2: Saltando importación (--skip-import)")
    
    # PASO 3: Generar features (si es necesario)
    if not args.skip_features:
        print(f"\n🤖 PASO 3: Generando features tácticas...")
        features_script = "../scripts/generate_features_with_tactics.py"
        
        if not args.dry_run:
            print("   ⚠️ Nota: Generación de features puede tomar varios minutos...")
            print("   🚀 Iniciando generación en segundo plano...")
            
            # Iniciar proceso en background para features
            try:
                subprocess.Popen([
                    sys.executable, 
                    features_script
                ], cwd=Path(__file__).parent.parent)
                
                print("   ✅ Proceso de features iniciado en background")
                print("   💡 El análisis continuará con features disponibles")
                
            except Exception as e:
                print(f"   ⚠️ Error iniciando features: {e}")
                print("   📊 Continuando con features existentes...")
        else:
            print(f"   Ejecutaría: {features_script} (en background)")
    else:
        print(f"\n⏭️ PASO 3: Saltando generación de features (--skip-features)")
    
    # PASO 4: Verificar datos finales
    print(f"\n🔍 PASO 4: Verificación final de datos...")
    if not args.dry_run:
        success, output = run_script('check_player_data.py', [args.player_name])
        # Continuar aunque falle - el análisis puede funcionar con datos parciales
    else:
        print(f"   Ejecutaría: check_player_data.py {args.player_name}")
    
    # PASO 5: Análisis completo
    print(f"\n📊 PASO 5: Ejecutando análisis completo...")
    analysis_args = [
        args.player_name,
        '--min-games', str(args.min_games),
        '--output-dir', args.output_dir
    ]
    
    if not args.dry_run:
        success, output = run_script('analyze_player.py', analysis_args)
        if not success:
            print("❌ Falla en análisis")
            pipeline_success = False
        else:
            print("✅ Análisis completado exitosamente")
    else:
        print(f"   Ejecutaría: analyze_player.py {' '.join(analysis_args)}")
    
    # Resumen final
    print(f"\n🏁 PIPELINE COMPLETADO")
    print("=" * 40)
    
    if args.dry_run:
        print("📋 Modo dry-run - no se ejecutó nada")
        return 0
    
    if pipeline_success:
        print("✅ Todos los pasos completados exitosamente")
        print(f"📄 Buscar reporte en: {args.output_dir}/{args.player_name.lower()}_analysis_*.md")
    else:
        print("⚠️ Pipeline completado con algunos errores")
        print("💡 Verificar logs anteriores para detalles")
    
    return 0 if pipeline_success else 1

if __name__ == "__main__":
    sys.exit(main())