#!/usr/bin/env python3
"""
Script para extraer PGNs de partidas específicas desde la base de datos
"""

import sys
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import argparse
from datetime import datetime

# Agregar el directorio src al path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from db.models.games import Games
from db.session import get_session
from dotenv import load_dotenv

load_dotenv()

def get_database_session():
    """Crear sesión de base de datos usando configuración del proyecto"""
    try:
        session = get_session()
        return session, None
    except Exception as e:
        print(f"❌ Error conectando a la base de datos: {e}")
        return None, None

def extract_game_pgn(session, game_id):
    """Extraer PGN de una partida específica"""
    try:
        game = session.query(Games).filter(Games.game_id == game_id).first()
        
        if not game:
            print(f"❌ No se encontró la partida con ID: {game_id}")
            return None
            
        return {
            'game_id': game.game_id,
            'white_player': game.white_player,
            'black_player': game.black_player,
            'date': game.date_played,
            'result': game.result,
            'eco': game.eco,
            'opening': game.opening,
            'white_elo': game.white_elo,
            'black_elo': game.black_elo,
            'pgn': game.pgn
        }
    except Exception as e:
        print(f"❌ Error extrayendo PGN para {game_id}: {e}")
        return None

def format_pgn_output(game_data):
    """Formatear datos de la partida en formato PGN estándar"""
    if not game_data:
        return None
        
    # Headers PGN estándar
    pgn_headers = []
    pgn_headers.append(f'[Event "Online Game"]')
    pgn_headers.append(f'[Site "Chess Platform"]')
    pgn_headers.append(f'[Date "{game_data["date"] or "????.??.??"}"]')
    pgn_headers.append(f'[Round "?"]')
    pgn_headers.append(f'[White "{game_data["white_player"]}"]')
    pgn_headers.append(f'[Black "{game_data["black_player"]}"]')
    pgn_headers.append(f'[Result "{game_data["result"] or "*"}"]')
    
    if game_data["eco"]:
        pgn_headers.append(f'[ECO "{game_data["eco"]}"]')
    if game_data["opening"]:
        pgn_headers.append(f'[Opening "{game_data["opening"]}"]')
    if game_data["white_elo"]:
        pgn_headers.append(f'[WhiteElo "{game_data["white_elo"]}"]')
    if game_data["black_elo"]:
        pgn_headers.append(f'[BlackElo "{game_data["black_elo"]}"]')
        
    pgn_headers.append(f'[GameId "{game_data["game_id"]}"]')
    
    # Movimientos
    moves = game_data["pgn"] or "* Movimientos no disponibles *"
    
    return "\n".join(pgn_headers) + "\n\n" + moves + "\n"

def main():
    parser = argparse.ArgumentParser(description='Extraer PGNs de partidas específicas')
    parser.add_argument('game_ids', nargs='+', help='IDs de las partidas a extraer')
    parser.add_argument('--output', '-o', help='Archivo de salida (opcional)')
    
    args = parser.parse_args()
    
    # IDs de las partidas de las rachas más importantes de cmess1315
    important_games = {
        "013df8920d082e406d7101917167a4cb3a5ec01058169988e359342cab5f1be3": "Racha de 20 errores vs bainian12345",
        "0142824e15cd88637cdba6791e39a0e60122b2698c73f3cd6c404abfc118c479": "Racha de 7 errores vs giurus", 
        "001c11b3a181c59fcfae14e03cbaeecfa27a1e24b0aadf5fad0a44bcb78e55ac": "Racha de 2 errores vs alexramirez9711"
    }
    
    if args.game_ids == ['all']:
        game_ids = list(important_games.keys())
    else:
        game_ids = args.game_ids
    
    session, engine = get_database_session()
    if not session:
        return
        
    try:
        print(f"🔍 Extrayendo PGNs de {len(game_ids)} partidas...")
        print("=" * 80)
        
        output_content = []
        output_content.append("# PGNs de Partidas con Rachas de Errores - cmess1315")
        output_content.append(f"Generado el: {Path(__file__).stem}")
        output_content.append("=" * 80)
        
        for i, game_id in enumerate(game_ids, 1):
            print(f"\n📋 Partida #{i}: {game_id}")
            
            if game_id in important_games:
                description = important_games[game_id]
                print(f"🎯 Descripción: {description}")
                output_content.append(f"\n## {description}")
                output_content.append(f"**Game ID**: {game_id}")
                output_content.append("")
            
            game_data = extract_game_pgn(session, game_id)
            
            if game_data:
                print(f"✅ {game_data['white_player']} vs {game_data['black_player']}")
                print(f"📅 Fecha: {game_data['date']}")
                print(f"🎲 Apertura: {game_data['eco']} - {game_data['opening']}")
                print(f"📊 Resultado: {game_data['result']}")
                
                pgn_formatted = format_pgn_output(game_data)
                if pgn_formatted:
                    print("🎮 PGN extraído correctamente")
                    output_content.append("```pgn")
                    output_content.append(pgn_formatted.strip())
                    output_content.append("```")
                    output_content.append("")
                else:
                    print("⚠️ Error formateando PGN")
            else:
                print("❌ No se pudo extraer la partida")
                
        # Guardar archivo si se especifica
        if args.output:
            output_file = Path(args.output)
        else:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            output_file = Path("reports") / f"pgns_rachas_cmess1315_{timestamp}.md"
            
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_content))
            
        print(f"\n💾 PGNs guardados en: {output_file}")
        
        # También mostrar información de criterios de error
        print("\n" + "=" * 80)
        print("📊 CRITERIOS DE CLASIFICACIÓN DE ERRORES:")
        print("=" * 80)
        print("🟡 INACCURACY: 50-100 centipeones (0.5-1.0 puntos)")
        print("🟠 MISTAKE: 100-300 centipeones (1.0-3.0 puntos)")  
        print("🔴 BLUNDER: 300+ centipeones (3.0+ puntos)")
        print("\n💡 NOTA: Todas las categorías son consideradas 'errores'")
        print("   La diferencia está en la gravedad de la pérdida de ventaja.")
        
    finally:
        session.close()

if __name__ == "__main__":
    main()