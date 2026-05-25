import os
import traceback
from pathlib import Path
import chess
from dotenv import load_dotenv
from src.modules.pgn_batch_loader import extract_pgn_files, extract_features_from_game
from src.db.repository.games_repository import GamesRepository

load_dotenv()
DB_PATH_URL = os.environ.get("CHESS_TRAINER_DB_URL")
BASE_DIR = Path(os.environ.get("PGN_PATH"))
SOURCES = ["personal", "novice", "elite", "stockfish"]
MAX_GAMES_PER_SOURCE = 10000
BATCH_SIZE = 100

def import_balanced_10k_games():
    """Importa máximo 10k juegos de cada fuente de manera balanceada"""
    repo = GamesRepository()
    
    # Contadores por fuente
    imported_counts = {source: 0 for source in SOURCES}
    total_imported = 0
    
    print(f"🎯 Objetivo: Importar máximo {MAX_GAMES_PER_SOURCE} juegos de cada fuente")
    print(f"📂 Fuentes: {SOURCES}")
    
    # Procesar cada fuente
    for source in SOURCES:
        if imported_counts[source] >= MAX_GAMES_PER_SOURCE:
            print(f"✅ {source}: Ya se importaron {MAX_GAMES_PER_SOURCE} juegos")
            continue
            
        source_path = BASE_DIR / source
        if not source_path.exists():
            print(f"⚠️ {source}: Carpeta no encontrada - {source_path}")
            continue
            
        print(f"📦 Procesando fuente: {source}")
        
        # Encontrar archivos PGN en la fuente
        pgn_files = []
        for root, _, files in os.walk(source_path):
            for name in files:
                if any(name.endswith(ext) for ext in [".pgn", ".zip", ".tar", ".gz", ".bz2"]):
                    pgn_files.append(Path(root) / name)
        
        if not pgn_files:
            print(f"⚠️ {source}: No se encontraron archivos PGN")
            continue
            
        print(f"📄 {source}: Encontrados {len(pgn_files)} archivos PGN")
        
        # Procesar archivos de esta fuente
        games_batch = []
        
        for file_path in pgn_files:
            if imported_counts[source] >= MAX_GAMES_PER_SOURCE:
                break
                
            print(f"📖 Procesando: {file_path.name}")
            
            try:
                for filename, pgn_io in extract_pgn_files(str(file_path)):
                    while imported_counts[source] < MAX_GAMES_PER_SOURCE:
                        try:
                            game = chess.pgn.read_game(pgn_io)
                            if game is None:
                                break

                            pgn_str = str(game)
                            game_data = extract_features_from_game(pgn_str)
                            game_data["source"] = source

                            if not repo.game_exists(game_data["game_id"]):
                                games_batch.append(game_data)
                                imported_counts[source] += 1
                                total_imported += 1
                                
                                # Progress update
                                if imported_counts[source] % 1000 == 0:
                                    print(f"📊 {source}: {imported_counts[source]}/{MAX_GAMES_PER_SOURCE} juegos")
                                
                                # Batch insert
                                if len(games_batch) >= BATCH_SIZE:
                                    try:
                                        repo.save_games_batch(games_batch)
                                        games_batch = []
                                    except Exception as batch_error:
                                        print(f"❌ Error guardando lote: {batch_error}")
                                        repo.rollback()
                                        games_batch = []
                            
                            # Break if we reached the limit
                            if imported_counts[source] >= MAX_GAMES_PER_SOURCE:
                                break
                                
                        except Exception as game_error:
                            print(f"⚠️ Error procesando juego: {game_error}")
                            continue
                            
            except Exception as file_error:
                print(f"❌ Error procesando archivo {file_path}: {file_error}")
                continue
        
        # Save remaining games in batch
        if games_batch:
            try:
                repo.save_games_batch(games_batch)
                print(f"💾 Guardado lote final de {len(games_batch)} juegos para {source}")
            except Exception as batch_error:
                print(f"❌ Error guardando lote final: {batch_error}")
                repo.rollback()
        
        print(f"✅ {source}: Completado - {imported_counts[source]} juegos importados")
    
    # Resumen final
    print("\n📈 RESUMEN FINAL:")
    for source in SOURCES:
        print(f"  {source}: {imported_counts[source]:,} juegos")
    print(f"  TOTAL: {total_imported:,} juegos")
    
    return imported_counts

if __name__ == "__main__":
    try:
        print("🚀 Iniciando importación balanceada de 10k juegos por fuente...")
        result = import_balanced_10k_games()
        print("🎉 Importación completada exitosamente!")
    except Exception as e:
        print(f"💥 Error durante la importación: {e}")
        traceback.print_exc()
