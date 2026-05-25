#!/usr/bin/env python3
"""
Script temporal para verificar batch 821780fb en PostgreSQL
"""
import sys
sys.path.append('src')

from db.session import get_session
from db.models import Games, Features

def main():
    session = get_session()
    
    # 1. Verificar últimos batch_ids en la base de datos
    print("🔍 Últimos 5 batch_ids en la base de datos:")
    latest_batches = session.query(Games.import_batch_id).distinct().order_by(Games.import_batch_id.desc()).limit(5).all()
    for i, (batch_id,) in enumerate(latest_batches, 1):
        if batch_id:
            count = session.query(Games).filter(Games.import_batch_id == batch_id).count()
            print(f"   {i}. {batch_id[:16]}... ({count} partidas)")
        else:
            count = session.query(Games).filter(Games.import_batch_id.is_(None)).count()
            print(f"   {i}. None ({count} partidas)")
    
    print("\n" + "="*60 + "\n")
    
    # 2. Batch de prueba (1581df7e)
    batch_id = '1581df7e'
    games = session.query(Games).filter(Games.import_batch_id.like(f'{batch_id}%')).all()
    
    print(f'🎯 Batch {batch_id} (PRUEBA):')
    print(f'   Partidas encontradas: {len(games)}')
    
    if games:
        first_game = games[0]
        print(f'\n📊 Primera partida:')
        print(f'   ID: {first_game.game_id[:16]}...')
        print(f'   Blancas: {first_game.white_player}')
        print(f'   Negras: {first_game.black_player}')
        print(f'   Resultado: {first_game.result}')
        print(f'   Fecha: {first_game.date_played}')
        print(f'   Importado por: {first_game.imported_by}')
        print(f'   Batch completo: {first_game.import_batch_id}')
        
        # Verificar features
        features_count = session.query(Features).filter(
            Features.game_id.in_([g.game_id for g in games])
        ).count()
        
        status = 'COMPLETO' if features_count == len(games) else 'PENDIENTE'
        print(f'\n✅ Features extraídas: {features_count}/{len(games)}')
        print(f'   Estado: {status}')
        
        # Detalles de todas las partidas
        print(f'\n📋 Todas las partidas en este batch:')
        for i, game in enumerate(games, 1):            print(f'   {i}. {game.white_player} vs {game.black_player} - {game.result}')
    
    print("\n" + "="*60 + "\n")
    
    # 3. Verificar últimas importaciones (batches más recientes que no sean None)
    print("🔍 Últimas importaciones recientes (con batch_id):")
    recent_batches = session.query(Games.import_batch_id, Games.imported_by).filter(
        Games.import_batch_id.isnot(None)
    ).distinct().order_by(Games.import_batch_id.desc()).limit(3).all()
    
    for batch_id, imported_by in recent_batches:
        count = session.query(Games).filter(Games.import_batch_id == batch_id).count()
        features_count = session.query(Features).join(
            Games, Features.game_id == Games.game_id
        ).filter(Games.import_batch_id == batch_id).count()
        print(f"   - {batch_id[:16]}... ({count} partidas, {features_count} features) - Importado por: {imported_by}")
    
    print("\n" + "="*60 + "\n")
    
    # 4. Batch 65ec6ed3 (kabir_pathak_10bis.pgn)
    batch_id = '65ec6ed3'
    games = session.query(Games).filter(Games.import_batch_id.like(f'{batch_id}%')).all()
    
    print(f'🎯 Batch {batch_id} (EXTRACCIÓN ACTUAL):')
    print(f'   Partidas encontradas: {len(games)}')
    
    if games:
        first_game = games[0]
        print(f'\n📊 Primera partida:')
        print(f'   ID: {first_game.game_id[:16]}...')
        print(f'   Blancas: {first_game.white_player}')
        print(f'   Negras: {first_game.black_player}')
        print(f'   Resultado: {first_game.result}')
        print(f'   Fecha: {first_game.date_played}')
        print(f'   Importado por: {first_game.imported_by}')
        print(f'   Batch completo: {first_game.import_batch_id}')
        
        # Verificar features
        features_count = session.query(Features).filter(
            Features.game_id.in_([g.game_id for g in games])
        ).count()
        
        status = 'COMPLETO' if features_count == len(games) else 'PENDIENTE'
        print(f'\n✅ Features extraídas: {features_count}/{len(games)}')
        print(f'   Estado: {status}')
        
        # Detalles de todas las partidas
        print(f'\n📋 Todas las partidas en este batch:')
        for i, game in enumerate(games, 1):
            print(f'   {i}. {game.white_player} vs {game.black_player} - {game.result}')
    else:
        print('   ⚠️ No se encontraron partidas con este batch_id')
    
    session.close()

if __name__ == '__main__':
    main()
