#!/usr/bin/env python3
"""
Script simple para importar PGNs de Th3Hound
"""
import os
import sys
import chess.pgn
import hashlib
import uuid
from pathlib import Path
from datetime import datetime

# Agregar el directorio src al path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

# Importaciones del proyecto
from db.models.games import Games
from db.session import get_session
from dotenv import load_dotenv

load_dotenv()

def generate_game_id(pgn_text: str) -> str:
    """Generar ID único basado en el contenido PGN"""
    return hashlib.md5(pgn_text.encode('utf-8')).hexdigest()

def extract_game_info(game, pgn_text: str, filename: str) -> dict:
    """Extraer información del juego PGN"""
    headers = game.headers
    
    return {
        'game_id': generate_game_id(pgn_text),
        'pgn': pgn_text,
        'source': 'personal',
        'white_player': headers.get('White', ''),
        'black_player': headers.get('Black', ''),
        'white_elo': headers.get('WhiteElo', ''),
        'black_elo': headers.get('BlackElo', ''),
        'result': headers.get('Result', ''),
        'time_control': headers.get('TimeControl', ''),
        'opening': headers.get('Opening', ''),
        'eco': headers.get('ECO', ''),
        'date_played': headers.get('Date', ''),
        'created_at': datetime.now().isoformat(),
        'import_batch_id': str(uuid.uuid4()),
        'source_filename': filename
    }

def import_pgn_file(file_path: Path, session):
    """Importar un archivo PGN específico"""
    print(f"📁 Procesando: {file_path.name}")
    games_imported = 0
    
    try:
        with open(file_path, 'r', encoding='utf-8') as pgn_file:
            while True:
                # Leer posición actual
                pos_start = pgn_file.tell()
                
                # Intentar leer un juego
                game = chess.pgn.read_game(pgn_file)
                if game is None:
                    break
                
                # Obtener el texto completo del juego
                pos_end = pgn_file.tell()
                pgn_file.seek(pos_start)
                pgn_text = pgn_file.read(pos_end - pos_start).strip()
                pgn_file.seek(pos_end)
                
                # Extraer información
                game_data = extract_game_info(game, pgn_text, file_path.name)
                
                # Verificar si ya existe
                existing = session.query(Games).filter_by(game_id=game_data['game_id']).first()
                if existing:
                    print(f"⏭️  Juego ya existe: {game_data['game_id'][:8]}...")
                    continue
                
                # Crear nuevo juego
                new_game = Games(**game_data)
                session.add(new_game)
                games_imported += 1
                
                if games_imported % 50 == 0:
                    print(f"   📊 Importados: {games_imported}")
                    session.commit()
    
    except Exception as e:
        print(f"❌ Error procesando {file_path.name}: {str(e)}")
        return 0
    
    # Commit final
    session.commit()
    print(f"✅ {file_path.name}: {games_imported} juegos importados")
    return games_imported

def main():
    """Función principal"""
    print("🚀 Importando PGNs de Th3Hound...")
    
    # Directorio de PGNs personales
    personal_dir = Path("data/games/personal")
    if not personal_dir.exists():
        print(f"❌ Directorio no encontrado: {personal_dir}")
        return
    
    # Buscar archivos de Th3Hound
    th3_files = []
    for pattern in ["*Th3*", "*th3*"]:
        th3_files.extend(list(personal_dir.glob(f"{pattern}.pgn")))
    
    if not th3_files:
        print("❌ No se encontraron archivos PGN de Th3Hound")
        return
    
    print(f"📋 Encontrados {len(th3_files)} archivos:")
    for f in th3_files:
        print(f"   - {f.name}")
    
    # Crear sesión de base de datos
    session = get_session()
    total_imported = 0
    
    try:
        # Procesar cada archivo
        for pgn_file in th3_files:
            imported = import_pgn_file(pgn_file, session)
            total_imported += imported
        
        print(f"\n🎉 COMPLETADO: {total_imported} juegos importados en total!")
        
        # Verificar importación
        th3_games = session.query(Games).filter(
            (Games.white_player.ilike('%th3%')) | 
            (Games.black_player.ilike('%th3%'))
        ).count()
        
        print(f"📊 Total de juegos de Th3Hound en BD: {th3_games}")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()