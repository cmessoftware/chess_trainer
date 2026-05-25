#!/usr/bin/env python3
"""
Script simple para verificar estado de partidas novice
"""

import sys
from pathlib import Path

# Agregar src al path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

def check_novice_status():
    """Verificar estado actual de partidas novice"""
    print("🔍 ESTADO ACTUAL DE PARTIDAS NOVICE")
    print("=" * 50)
    
    try:
        from db.repository.games_repository import GamesRepository
        repo = GamesRepository()
        
        print("📊 Conectando a base de datos...")
        all_games = repo.get_all_games()
        
        print(f"✅ Total partidas en BD: {len(all_games)}")
        
        # Contar por fuente
        sources = {}
        for game in all_games:
            source = getattr(game, 'source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n📈 Partidas por fuente:")
        for source, count in sources.items():
            if source == 'novice':
                print(f"  - {source}: {count} ⭐")
            else:
                print(f"  - {source}: {count}")
        
        novice_count = sources.get('novice', 0)
        
        if novice_count >= 1000:
            print(f"\n🎉 ¡META ALCANZADA! {novice_count} partidas novice")
        else:
            remaining = 1000 - novice_count
            print(f"\n🎯 Faltan {remaining} partidas para llegar a 1000")
            print(f"📊 Progreso: {novice_count}/1000 ({novice_count/10:.1f}%)")
        
        # Mostrar ejemplos de partidas novice
        novice_games = [g for g in all_games if getattr(g, 'source', '') == 'novice']
        if novice_games:
            print(f"\n🎮 Últimas 5 partidas novice:")
            for i, game in enumerate(novice_games[-5:]):
                white = getattr(game, 'white_player', 'N/A')
                black = getattr(game, 'black_player', 'N/A')
                date = getattr(game, 'date_played', 'N/A')
                white_elo = getattr(game, 'white_elo', 'N/A')
                black_elo = getattr(game, 'black_elo', 'N/A')
                print(f"  {i+1}. {white} ({white_elo}) vs {black} ({black_elo}) - {date}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_novice_status()
