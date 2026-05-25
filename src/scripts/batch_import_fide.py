#!/usr/bin/env python3
"""
Script masivo para importar partidas de archivos ZIP de grandes maestros FIDE
Versión optimizada con mejor manejo de errores y progreso
"""

import os
import sys
import zipfile
import tempfile
from pathlib import Path
import chess.pgn
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Agregar el directorio src al path de Python
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

from modules.pgn_batch_loader import extract_features_from_game
from db.repository.games_repository import GamesRepository

def safe_string(text, max_len=50):
    """Convierte texto a formato seguro para mostrar"""
    try:
        return str(text)[:max_len].encode('ascii', 'ignore').decode('ascii')
    except:
        return "[texto_especial]"

def import_from_single_zip(zip_path, games_per_zip=100):
    """Importa partidas de un solo archivo ZIP"""
    zip_name = Path(zip_path).name
    print(f"\n[INICIO] {safe_string(zip_name)}")
    
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
                    print(f"  [VACIO] {safe_string(zip_name)} - No hay PGN")
                    return zip_name, 0
                
                # Procesar cada archivo PGN hasta alcanzar el límite
                for pgn_file in pgn_files:
                    if imported_count >= games_per_zip:
                        break
                        
                    try:
                        with open(pgn_file, 'r', encoding='utf-8', errors='ignore') as f:
                            while imported_count < games_per_zip:
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
                                            
                                            # Mostrar progreso cada 25 partidas
                                            if imported_count % 25 == 0:
                                                print(f"  [PROGRESO] {safe_string(zip_name)}: {imported_count}")
                                                
                                except Exception:
                                    # Silenciosamente continuar con siguiente partida
                                    continue
                                    
                    except Exception as e:
                        print(f"  [ERROR_PGN] {safe_string(Path(pgn_file).name)}: {safe_string(str(e))}")
                        continue
                
                print(f"  [COMPLETADO] {safe_string(zip_name)}: {imported_count} partidas")
                return zip_name, imported_count
                
    except Exception as e:
        print(f"  [ERROR_ZIP] {safe_string(zip_name)}: {safe_string(str(e))}")
        return zip_name, 0

def batch_import_fide_zips(games_per_zip=100, max_workers=3):
    """Importa partidas de todos los ZIPs de FIDE en paralelo"""
    fide_dir = Path("src/data/games/fide")
    
    # Buscar archivos ZIP
    zip_files = list(fide_dir.glob("*.zip"))
    print(f"Encontrados {len(zip_files)} archivos ZIP en FIDE")
    
    if not zip_files:
        print("No se encontraron archivos ZIP")
        return
    
    # Procesar en lotes para evitar sobrecargar la BD
    total_imported = 0
    successful_zips = 0
    start_time = time.time()
    
    # Procesar ZIPs en paralelo
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar trabajos
        future_to_zip = {
            executor.submit(import_from_single_zip, zip_path, games_per_zip): zip_path 
            for zip_path in zip_files
        }
        
        # Recoger resultados
        for future in as_completed(future_to_zip):
            try:
                zip_name, imported = future.result()
                total_imported += imported
                if imported > 0:
                    successful_zips += 1
                    
            except Exception as e:
                print(f"Error inesperado: {safe_string(str(e))}")
    
    # Resumen final
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print(f"RESUMEN IMPORTACION FIDE")
    print(f"{'='*60}")
    print(f"ZIPs procesados: {len(zip_files)}")
    print(f"ZIPs exitosos: {successful_zips}")
    print(f"Total partidas importadas: {total_imported}")
    print(f"Promedio por ZIP exitoso: {total_imported/max(successful_zips,1):.1f}")
    print(f"Tiempo total: {elapsed/60:.1f} minutos")
    print(f"Partidas por minuto: {total_imported/(elapsed/60):.1f}")
    
def main():
    """Función principal"""
    print("Iniciando importación masiva de partidas FIDE...")
    print("Configuración: 100 partidas por ZIP, 3 workers paralelos")
    
    # Ejecutar importación
    batch_import_fide_zips(games_per_zip=100, max_workers=3)
    
    print("\nImportación FIDE completada!")

if __name__ == "__main__":
    main()
