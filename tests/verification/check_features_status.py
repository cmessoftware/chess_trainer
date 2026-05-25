#!/usr/bin/env python3
"""
Script para verificar estado de features en tiempo real
"""
import sys
sys.path.append('src')

from db.session import get_session
from db.models.games import Games
from db.models.features import Features
from sqlalchemy import func, desc

def main():
    session = get_session()
    
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE ESTADO DE FEATURES")
    print("=" * 70)
    
    # 1. Últimas importaciones (las más recientes primero)
    print("\n📦 Últimas 5 importaciones (ordenadas por created_at DESC):")
    latest_imports = session.query(
        Games.import_batch_id, 
        Games.imported_by,
        func.min(Games.created_at).label('created_at'),
        func.count(Games.game_id).label('count')
    ).filter(
        Games.import_batch_id.isnot(None)
    ).group_by(
        Games.import_batch_id, Games.imported_by
    ).order_by(
        desc('created_at')
    ).limit(5).all()
    
    for batch_id, imported_by, created_at, count in latest_imports:
        # Contar features para este batch
        features_count = session.query(Features).join(
            Games, Features.game_id == Games.game_id
        ).filter(Games.import_batch_id == batch_id).count()
        
        status = "✅ COMPLETO" if features_count == count else f"⚠️ {features_count}/{count}"
        print(f"   {batch_id[:16]}... - {count} partidas ({status}) - {imported_by} - {created_at}")
    
    print("\n" + "=" * 70)
    
    # 2. Features más recientes extraídas
    print("\n🎯 Últimas 10 features extraídas (ordenadas por created_at DESC):")
    latest_features = session.query(
        Features.game_id,
        Features.created_at,
        Games.white_player,
        Games.black_player,
        Games.import_batch_id
    ).join(
        Games, Features.game_id == Games.game_id
    ).order_by(
        desc(Features.created_at)
    ).limit(10).all()
    
    if latest_features:
        for game_id, created_at, white, black, batch_id in latest_features:
            print(f"   {game_id[:16]}... - {white} vs {black} - Batch: {batch_id[:8] if batch_id else 'None'}... - {created_at}")
    else:
        print("   ⚠️ No hay features extraídas recientemente")
    
    print("\n" + "=" * 70)
    
    # 3. Resumen total
    total_games = session.query(func.count(Games.game_id)).scalar()
    total_features = session.query(func.count(Features.game_id)).scalar()
    games_without_features = total_games - total_features
    
    print(f"\n📊 RESUMEN GLOBAL:")
    print(f"   Total partidas: {total_games:,}")
    print(f"   Total features: {total_features:,}")
    print(f"   Partidas sin features: {games_without_features:,}")
    print(f"   Cobertura: {(total_features / total_games * 100):.2f}%")
    
    session.close()

if __name__ == '__main__':
    main()
