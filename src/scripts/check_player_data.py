#!/usr/bin/env python3
"""
Script genérico para verificar datos de cualquier jugador
Uso: python check_player_data.py <player_name> [--details]
"""
import sys
import argparse
from pathlib import Path

# Agregar el directorio src al path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from db.session import get_session
from db.models.features import Features  
from db.models.games import Games

def check_player_data(player_name: str, show_details: bool = False):
    """Verificar datos disponibles de un jugador"""
    session = get_session()
    
    try:
        print(f"🔍 VERIFICANDO DATOS DE {player_name.upper()}")
        print("=" * 50)
        
        # Contar juegos
        games_count = session.query(Games).filter(
            (Games.white_player.ilike(f'%{player_name}%')) | 
            (Games.black_player.ilike(f'%{player_name}%'))
        ).count()
        
        print(f"🎮 Juegos totales: {games_count}")
        
        if games_count == 0:
            print(f"❌ No se encontraron juegos para {player_name}")
            return False
        
        # Contar games por color
        white_games = session.query(Games).filter(
            Games.white_player.ilike(f'%{player_name}%')
        ).count()
        
        black_games = session.query(Games).filter(
            Games.black_player.ilike(f'%{player_name}%')
        ).count()
        
        print(f"   ⚪ Como Blanco: {white_games}")
        print(f"   ⚫ Como Negro: {black_games}")
        
        # Contar features
        features_count = session.query(Features).join(
            Games, Features.game_id == Games.game_id
        ).filter(
            (Games.white_player.ilike(f'%{player_name}%')) | 
            (Games.black_player.ilike(f'%{player_name}%'))
        ).count()
        
        print(f"🤖 Features disponibles: {features_count}")
        
        # Estado para ML
        ml_ready = features_count >= 100
        analysis_ready = games_count >= 50
        
        print(f"\n📊 ESTADO PARA ANÁLISIS:")
        print(f"   {'✅' if analysis_ready else '❌'} Análisis básico: {'Listo' if analysis_ready else f'Necesita {50 - games_count} juegos más'}")
        print(f"   {'✅' if ml_ready else '❌'} Análisis ML: {'Listo' if ml_ready else f'Necesita {100 - features_count} features más'}")
        
        if show_details and games_count > 0:
            print(f"\n📋 DETALLES ADICIONALES:")
            
            # Distribución por fuente
            sources = session.query(Games.source, session.query(Games).filter(
                (Games.white_player.ilike(f'%{player_name}%')) | 
                (Games.black_player.ilike(f'%{player_name}%'))
            ).filter(Games.source == Games.source).count()).distinct().all()
            
            print("   📁 Por fuente:")
            for source, in session.query(Games.source).filter(
                (Games.white_player.ilike(f'%{player_name}%')) | 
                (Games.black_player.ilike(f'%{player_name}%'))
            ).distinct().all():
                if source:
                    source_count = session.query(Games).filter(
                        Games.source == source,
                        (Games.white_player.ilike(f'%{player_name}%')) | 
                        (Games.black_player.ilike(f'%{player_name}%'))
                    ).count()
                    print(f"      - {source}: {source_count} juegos")
            
            # Últimos juegos
            recent_games = session.query(Games).filter(
                (Games.white_player.ilike(f'%{player_name}%')) | 
                (Games.black_player.ilike(f'%{player_name}%'))
            ).order_by(Games.created_at.desc()).limit(3).all()
            
            print("   🕒 Juegos recientes:")
            for game in recent_games:
                is_white = game.white_player.lower().find(player_name.lower()) != -1
                color = "⚪" if is_white else "⚫"
                opponent = game.black_player if is_white else game.white_player
                print(f"      {color} vs {opponent} ({game.result}) - {game.date_played or 'Sin fecha'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        session.close()

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Verificar datos de jugador')
    parser.add_argument('player_name', help='Nombre del jugador a verificar')
    parser.add_argument('--details', action='store_true',
                       help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    success = check_player_data(args.player_name, args.details)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())