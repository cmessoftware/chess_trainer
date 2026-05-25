#!/usr/bin/env python3
"""
Script para importar partidas de archivos ZIP de grandes maestros de la carpeta FIDE.
Extrae al menos 100 partidas de cada archivo ZIP para crear una muestra representativa.
"""

import os
import sys
import zipfile
import tempfile
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import chess.pgn

# Agregar el directorio src al path de Python
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.insert(0, str(src_dir))

def safe_log_message(message):
    """Convierte un mensaje a formato seguro para logging en Windows"""
    try:
        return str(message).encode('ascii', 'ignore').decode('ascii')
    except:
        return "[MENSAJE_CON_CARACTERES_ESPECIALES]"

from modules.pgn_batch_loader import extract_pgn_files, extract_features_from_game
from db.repository.games_repository import GamesRepository

def import_pgn_from_file(pgn_file_path, source="fide", limit=100):
    """
    Importa partidas de un archivo PGN específico.
    
    Args:
        pgn_file_path: Ruta al archivo PGN
        source: Fuente de las partidas
        limit: Número máximo de partidas a importar
    
    Returns:
        int: Número de partidas importadas
    """
    logger = logging.getLogger(__name__)
    repo = GamesRepository()
    imported_count = 0
    
    try:
        with open(pgn_file_path, 'r', encoding='utf-8', errors='ignore') as pgn_file:
            while imported_count < limit:
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                
                try:
                    # Extraer features de la partida
                    game_data = extract_features_from_game(game, source)
                    if game_data:
                        # Intentar guardar en la base de datos
                        result = repo.create_game(game_data)
                        if result:
                            imported_count += 1
                        
                except Exception as e:
                    # Continuar con la siguiente partida si hay error
                    # Usar solo ASCII para evitar problemas de codificación
                    error_msg = f"Error procesando partida: {str(e).encode('ascii', 'ignore').decode('ascii')}"
                    logger.debug(error_msg)
                    continue
                    
    except Exception as e:
        # Usar solo ASCII para evitar problemas de codificación
        error_msg = f"Error leyendo archivo {pgn_file_path}: {str(e).encode('ascii', 'ignore').decode('ascii')}"
        logger.error(error_msg)
    
    return imported_count

def setup_logging():
    """Configurar logging con manejo de codificación para Windows"""
    # Configurar handler de consola con codificación UTF-8
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Configurar handler de archivo con codificación UTF-8
    file_handler = logging.FileHandler('fide_import.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # Formato común
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Configurar logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
    """Configurar logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('fide_import.log')
        ]
    )
    return logging.getLogger(__name__)

def extract_and_import_zip(zip_path, games_per_zip=100, max_workers=2):
    """
    Extrae partidas de un archivo ZIP e importa hasta games_per_zip partidas.
    
    Args:
        zip_path: Ruta al archivo ZIP
        games_per_zip: Número máximo de partidas a importar por ZIP
        max_workers: Número de workers para procesamiento paralelo
    
    Returns:
        tuple: (nombre_archivo, partidas_importadas, errores)
    """
    logger = logging.getLogger(__name__)
    zip_name = Path(zip_path).stem
    logger.info(f"Procesando {safe_log_message(zip_name)}.zip...")
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Crear directorio temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extraer archivos PGN del ZIP
                pgn_files = []
                for file_info in zip_ref.filelist:
                    if file_info.filename.lower().endswith('.pgn'):
                        zip_ref.extract(file_info, temp_dir)
                        pgn_files.append(os.path.join(temp_dir, file_info.filename))
                
                if not pgn_files:
                    logger.warning(f"No se encontraron archivos PGN en {safe_log_message(zip_name)}.zip")
                    return zip_name, 0, ["No hay archivos PGN"]
                
                total_imported = 0
                errors = []
                
                # Procesar cada archivo PGN extraído
                for pgn_file in pgn_files:
                    try:
                        # Calcular cuántas partidas importar de este archivo
                        remaining = games_per_zip - total_imported
                        if remaining <= 0:
                            break
                        
                        # Importar partidas con límite
                        imported_count = import_pgn_from_file(
                            pgn_file, 
                            source="fide",
                            limit=remaining
                        )
                        
                        total_imported += imported_count
                        safe_filename = safe_log_message(Path(pgn_file).name)
                        logger.info(f"  {safe_filename}: {imported_count} partidas importadas")
                        
                    except Exception as e:
                        safe_filename = safe_log_message(Path(pgn_file).name)
                        error_msg = f"Error procesando {safe_filename}: {safe_log_message(str(e))}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                logger.info(f"[COMPLETADO] {safe_log_message(zip_name)}: {total_imported} partidas importadas total")
                return zip_name, total_imported, errors
                
    except Exception as e:
        error_msg = f"Error procesando {safe_log_message(zip_name)}.zip: {safe_log_message(str(e))}"
        logger.error(error_msg)
        return zip_name, 0, [error_msg]

def import_fide_zip_games(fide_dir, games_per_zip=100, max_workers=2, zip_workers=3):
    """
    Importa partidas de todos los archivos ZIP en el directorio FIDE.
    
    Args:
        fide_dir: Directorio con archivos ZIP de FIDE
        games_per_zip: Número de partidas a importar por ZIP
        max_workers: Workers para procesar PGN dentro de cada ZIP
        zip_workers: Workers para procesar ZIPs en paralelo
    """
    logger = setup_logging()
    logger.info(f"Iniciando importación de partidas FIDE desde {fide_dir}")
    logger.info(f"Configuración: {games_per_zip} partidas por ZIP, {max_workers} workers PGN, {zip_workers} workers ZIP")
    
    # Buscar archivos ZIP
    zip_files = list(Path(fide_dir).glob("*.zip"))
    logger.info(f"Encontrados {len(zip_files)} archivos ZIP")
    
    if not zip_files:
        logger.warning("No se encontraron archivos ZIP en el directorio FIDE")
        return
    
    # Procesar ZIPs en paralelo
    total_imported = 0
    total_errors = []
    successful_zips = 0
    
    with ThreadPoolExecutor(max_workers=zip_workers) as executor:
        # Enviar trabajos
        future_to_zip = {
            executor.submit(extract_and_import_zip, zip_path, games_per_zip, max_workers): zip_path 
            for zip_path in zip_files
        }
        
        # Procesar resultados conforme completan
        for future in as_completed(future_to_zip):
            zip_path = future_to_zip[future]
            try:
                zip_name, imported, errors = future.result()
                total_imported += imported
                total_errors.extend(errors)
                if imported > 0:
                    successful_zips += 1
                    
            except Exception as e:
                error_msg = f"Error inesperado procesando {Path(zip_path).name}: {str(e)}"
                logger.error(error_msg)
                total_errors.append(error_msg)
    
    # Resumen final
    logger.info("=" * 60)
    logger.info("RESUMEN DE IMPORTACIÓN FIDE")
    logger.info("=" * 60)
    logger.info(f"ZIPs procesados exitosamente: {successful_zips}/{len(zip_files)}")
    logger.info(f"Total de partidas importadas: {total_imported}")
    logger.info(f"Promedio por ZIP exitoso: {total_imported/max(successful_zips,1):.1f}")
    
    if total_errors:
        logger.info(f"Total de errores: {len(total_errors)}")
        for error in total_errors[:10]:  # Mostrar solo los primeros 10 errores
            logger.warning(f"  • {error}")
        if len(total_errors) > 10:
            logger.warning(f"  ... y {len(total_errors)-10} errores más")
    
    logger.info("Importación FIDE completada")

def main():
    parser = argparse.ArgumentParser(description="Importar partidas de archivos ZIP de grandes maestros FIDE")
    parser.add_argument("--fide-dir", default="src/data/games/fide", 
                       help="Directorio con archivos ZIP de FIDE")
    parser.add_argument("--games-per-zip", type=int, default=100,
                       help="Número de partidas a importar por ZIP (default: 100)")
    parser.add_argument("--max-workers", type=int, default=2,
                       help="Workers para procesar PGN dentro de cada ZIP (default: 2)")
    parser.add_argument("--zip-workers", type=int, default=3,
                       help="Workers para procesar ZIPs en paralelo (default: 3)")
    
    args = parser.parse_args()
    
    # Verificar que el directorio existe
    if not Path(args.fide_dir).exists():
        print(f"Error: El directorio {args.fide_dir} no existe")
        sys.exit(1)
    
    # Ejecutar importación
    import_fide_zip_games(
        args.fide_dir,
        args.games_per_zip,
        args.max_workers,
        args.zip_workers
    )

if __name__ == "__main__":
    main()
