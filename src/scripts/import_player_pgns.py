#!/usr/bin/env python3
"""
Script genérico para importar PGNs de cualquier jugador
Uso: python import_player_pgns.py <player_name> [--source personal]
"""
import os
import sys
import chess.pgn
import hashlib
import uuid
import argparse
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

def extract_game_info(game, pgn_text: str, filename: str, source: str) -> dict:
    """Extraer información del juego PGN"""
    headers = game.headers
    
    return {
        'game_id': generate_game_id(pgn_text),
        'pgn': pgn_text,
        'source': source,
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

def import_pgn_file(file_path: Path, session, source: str):
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
                game_data = extract_game_info(game, pgn_text, file_path.name, source)
                
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

def find_player_files(player_name: str, source_dir: Path) -> list:
    """Buscar archivos PGN de un jugador específico"""
    player_files = []
    
    # Patrones de búsqueda (case insensitive)
    patterns = [
        f"*{player_name}*",
        f"*{player_name.lower()}*",
        f"*{player_name.upper()}*"
    ]
    
    for pattern in patterns:
        player_files.extend(list(source_dir.glob(f"{pattern}.pgn")))
    
    # Eliminar duplicados
    return list(set(player_files))

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Importar PGNs de un jugador específico')
    parser.add_argument('player_name', help='Nombre del jugador a buscar')
    parser.add_argument('--source', default='personal', 
                       choices=['personal', 'elite', 'novice', 'stockfish', 'fide'],
                       help='Directorio fuente de PGNs (default: personal)')
    parser.add_argument('--data-dir', default='data/games',
                       help='Directorio base de datos de juegos')
    
    args = parser.parse_args()
    
    print(f"🚀 Importando PGNs de {args.player_name}...")
    
    # Directorio de PGNs
    source_dir = Path(args.data_dir) / args.source
    if not source_dir.exists():
        print(f"❌ Directorio no encontrado: {source_dir}")
        return 1
    
    # Buscar archivos del jugador
    player_files = find_player_files(args.player_name, source_dir)
    
    if not player_files:
        print(f"❌ No se encontraron archivos PGN para {args.player_name} en {source_dir}")
        print(f"   Patrones buscados: *{args.player_name}*.pgn")
        return 1
    
    print(f"📋 Encontrados {len(player_files)} archivos:")
    for f in player_files:
        print(f"   - {f.name}")
    
    # Crear sesión de base de datos
    session = get_session()
    total_imported = 0
    
    try:
        # Procesar cada archivo
        for pgn_file in player_files:
            imported = import_pgn_file(pgn_file, session, args.source)
            total_imported += imported
        
        print(f"\n🎉 COMPLETADO: {total_imported} juegos importados en total!")
        
        # Verificar importación
        player_games = session.query(Games).filter(
            (Games.white_player.ilike(f'%{args.player_name}%')) | 
            (Games.black_player.ilike(f'%{args.player_name}%'))
        ).count()
        
        print(f"📊 Total de juegos de {args.player_name} en BD: {player_games}")
        return 0
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        session.rollback()
        return 1
    finally:
        session.close()

if __name__ == "__main__":
    sys.exit(main())