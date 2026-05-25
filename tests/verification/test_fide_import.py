#!/usr/bin/env python3
"""
Script simple para probar la importación de archivos ZIP de FIDE
"""

import os
import sys
import zipfile
import tempfile
from pathlib import Path
import chess.pgn
import logging

# Agregar el directorio src al path de Python
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from modules.pgn_batch_loader import extract_features_from_game
from db.repository.games_repository import GamesRepository

def test_zip_import(zip_path, max_games=20):
    """Importa hasta max_games partidas de un archivo ZIP específico"""
    print(f"Procesando: {Path(zip_path).name}")
    
    try:
        repo = GamesRepository()
        imported_count = 0
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extraer archivos PGN
                pgn_files = []
                for file_info in zip_ref.filelist:
                    if file_info.filename.lower().endswith('.pgn'):
                        zip_ref.extract(file_info, temp_dir)
                        pgn_files.append(os.path.join(temp_dir, file_info.filename))
                
                if not pgn_files:
                    print(f"  No hay archivos PGN en {Path(zip_path).name}")
                    return 0
                
                # Procesar primer archivo PGN encontrado
                pgn_file = pgn_files[0]
                print(f"  Procesando: {Path(pgn_file).name}")
                
                with open(pgn_file, 'r', encoding='utf-8', errors='ignore') as f:
                    while imported_count < max_games:
                        game = chess.pgn.read_game(f)
                        if game is None:
                            break
                        
                        try:
                            # Extraer features
                            game_data = extract_features_from_game(game, "fide")
                            if game_data:
                                # Guardar en BD
                                result = repo.create_game(game_data)
                                if result:
                                    imported_count += 1
                                    if imported_count % 5 == 0:
                                        print(f"    Importadas: {imported_count}")
                        except Exception as e:
                            print(f"    Error en partida: {str(e)[:50]}...")
                            continue
                
                print(f"  Total importadas: {imported_count}")
                return imported_count
                
    except Exception as e:
        print(f"  Error: {str(e)}")
        return 0

def main():
    """Función principal para probar algunos ZIPs"""
    fide_dir = Path("src/data/games/fide")
    
    # Seleccionar algunos ZIPs de grandes maestros famosos
    test_zips = [
        "Carlsen.zip",
        "Kasparov.zip", 
        "Fischer.zip",
        "Anand.zip",
        "Kramnik.zip"
    ]
    
    total_imported = 0
    
    for zip_name in test_zips:
        zip_path = fide_dir / zip_name
        if zip_path.exists():
            imported = test_zip_import(zip_path, max_games=20)
            total_imported += imported
        else:
            print(f"No encontrado: {zip_name}")
    
    print(f"\nTotal de partidas FIDE importadas: {total_imported}")

if __name__ == "__main__":
    main()
