#!/usr/bin/env python3
"""
Script de diagnóstico para verificar por qué no se importan partidas de FIDE
"""

import os
import sys
import zipfile
import tempfile
from pathlib import Path
import chess.pgn

# Agregar el directorio src al path de Python
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from modules.pgn_batch_loader import extract_features_from_game
from db.repository.games_repository import GamesRepository

def diagnose_single_zip(zip_path):
    """Diagnostica un solo archivo ZIP para ver qué está pasando"""
    zip_name = Path(zip_path).name
    print(f"\n{'='*50}")
    print(f"DIAGNOSTICANDO: {zip_name}")
    print(f"{'='*50}")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Listar contenidos
            print(f"Archivos en ZIP:")
            for file_info in zip_ref.filelist:
                print(f"  - {file_info.filename} ({file_info.file_size} bytes)")
            
            # Extraer y analizar PGN
            with tempfile.TemporaryDirectory() as temp_dir:
                pgn_files = []
                for file_info in zip_ref.filelist:
                    if file_info.filename.lower().endswith('.pgn'):
                        zip_ref.extract(file_info, temp_dir)
                        pgn_files.append(os.path.join(temp_dir, file_info.filename))
                
                if not pgn_files:
                    print("❌ No hay archivos PGN en el ZIP")
                    return False
                
                # Analizar primer archivo PGN
                pgn_file = pgn_files[0]
                print(f"\nAnalizando: {Path(pgn_file).name}")
                
                try:
                    with open(pgn_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # Leer primera partida
                        game = chess.pgn.read_game(f)
                        if game is None:
                            print("❌ No se pudo leer ninguna partida del archivo")
                            return False
                        
                        print("✅ Primera partida leída exitosamente")
                        print(f"  Headers: {dict(game.headers)}")
                        
                        # Probar extracción de features
                        print("\nProbando extracción de features...")
                        game_data = extract_features_from_game(game, "fide")
                        
                        if game_data is None:
                            print("❌ extract_features_from_game retornó None")
                            return False
                        
                        print("✅ Features extraídas exitosamente")
                        print(f"  Keys: {list(game_data.keys())}")
                        
                        # Probar inserción en BD
                        print("\nProbando inserción en base de datos...")
                        repo = GamesRepository()
                        result = repo.create_game(game_data)
                        
                        if result:
                            print("✅ Partida insertada exitosamente en BD")
                            return True
                        else:
                            print("❌ Error al insertar en BD - create_game retornó False/None")
                            return False
                            
                except Exception as e:
                    print(f"❌ Error procesando PGN: {str(e)}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error abriendo ZIP: {str(e)}")
        return False

def main():
    """Función principal de diagnóstico"""
    fide_dir = Path("src/data/games/fide")
    
    # Buscar archivos ZIP famosos para probar
    famous_zips = ["Carlsen.zip", "Kasparov.zip", "Fischer.zip", "Anand.zip"]
    
    print("🔍 DIAGNÓSTICO DE IMPORTACIÓN FIDE")
    print("=" * 60)
    
    # Verificar estado de BD primero
    print("\n1. Verificando conexión a base de datos...")
    try:
        repo = GamesRepository()
        print("✅ Conexión a BD exitosa")
    except Exception as e:
        print(f"❌ Error conectando a BD: {str(e)}")
        return
    
    # Diagnosticar ZIPs famosos
    for zip_name in famous_zips:
        zip_path = fide_dir / zip_name
        if zip_path.exists():
            success = diagnose_single_zip(zip_path)
            if success:
                print(f"✅ {zip_name} funciona correctamente")
                break
            else:
                print(f"❌ {zip_name} tiene problemas")
        else:
            print(f"⚠️  {zip_name} no encontrado")
    
    print(f"\n{'='*60}")
    print("Diagnóstico completado")

if __name__ == "__main__":
    main()
