#!/usr/bin/env python3
"""
Script de análisis mejorado con clasificación on-the-fly
NO modifica BD - clasifica en memoria durante análisis
"""
import sys
from pathlib import Path

# Agregar src al path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

from db.session import get_session
from db.models.features import Features  
from db.models.games import Games

def classify_move_onthefly(feature):
    """
    Clasificar movimiento en memoria SIN modificar BD
    Misma lógica pero solo para análisis
    """
    score_diff = abs(feature.score_diff or 0)
    move_number = feature.move_number or 1
    
    # Si ya tiene clasificación, respetarla
    if feature.error_label and feature.error_label != 'unknown':
        return feature.error_label
    
    # Clasificar según lógica mejorada
    if move_number <= 12:  # Apertura
        if score_diff <= 15:
            return "book"
        elif score_diff <= 30:
            return "good"  
        else:
            return "inaccuracy"
    
    # Middlegame/Endgame
    if score_diff <= 10:
        return "excellent"
    elif score_diff <= 25:
        return "good"
    elif score_diff <= 50:
        return "inaccuracy"
    elif score_diff <= 150:
        return "mistake"
    else:
        return "blunder"

def analyze_player_with_onthefly_classification(player_name: str, min_games: int = 50):
    """
    Análisis completo CON clasificación on-the-fly
    NO modifica BD - solo mejora análisis
    """
    session = get_session()
    
    try:
        print(f"🚀 ANÁLISIS ON-THE-FLY: {player_name.upper()}")
        print("🎯 Clasificando movimientos en memoria (sin modificar BD)")
        print("=" * 70)
        
        # Recolectar features del jugador
        features = session.query(Features).join(
            Games, Features.game_id == Games.game_id
        ).filter(
            (Games.white_player.ilike(f'%{player_name}%')) | 
            (Games.black_player.ilike(f'%{player_name}%'))
        ).all()
        
        if len(features) < 50:
            print(f"⚠️ Pocas features disponibles: {len(features)}")
            return
        
        print(f"📊 Features encontrados: {len(features)}")
        
        # CLASIFICAR EN MEMORIA (sin tocar BD)
        classified_moves = {}
        total_classified = 0
        
        for feature in features:
            # Clasificar on-the-fly
            classified_label = classify_move_onthefly(feature)
            classified_moves[classified_label] = classified_moves.get(classified_label, 0) + 1
            total_classified += 1
        
        # Mostrar distribución mejorada
        print(f"\n📈 DISTRIBUCIÓN CON CLASIFICACIÓN ON-THE-FLY:")
        print(f"   🔢 Total movimientos: {total_classified}")
        
        for label, count in sorted(classified_moves.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_classified) * 100
            icon = get_label_icon(label)
            print(f"   {icon} {label}: {count} ({percentage:.1f}%)")
        
        # Calcular métricas de calidad
        print(f"\n🎯 MÉTRICAS DE CALIDAD:")
        
        precision_rate = (
            classified_moves.get('excellent', 0) + 
            classified_moves.get('good', 0) + 
            classified_moves.get('book', 0)
        ) / total_classified * 100
        
        error_rate = (
            classified_moves.get('mistake', 0) + 
            classified_moves.get('blunder', 0)
        ) / total_classified * 100
        
        print(f"   ✅ Tasa de precisión: {precision_rate:.1f}%")
        print(f"   ❌ Tasa de errores: {error_rate:.1f}%")
        print(f"   ⚖️ Nivel estimado: {estimate_level_from_distribution(classified_moves, total_classified)}")
        
        # Recomendaciones basadas en distribución
        generate_recommendations_from_distribution(classified_moves, total_classified)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()

def get_label_icon(label: str) -> str:
    """Iconos para cada tipo de movimiento"""
    icons = {
        'excellent': '🌟',
        'book': '📚', 
        'good': '✅',
        'inaccuracy': '⚠️',
        'mistake': '❌',
        'blunder': '💥',
        'unknown': '❓'
    }
    return icons.get(label, '📋')

def estimate_level_from_distribution(moves: dict, total: int) -> str:
    """Estimar nivel basado en distribución de movimientos"""
    precision_rate = (
        moves.get('excellent', 0) + 
        moves.get('good', 0) + 
        moves.get('book', 0)
    ) / total * 100
    
    error_rate = (
        moves.get('mistake', 0) + 
        moves.get('blunder', 0)
    ) / total * 100
    
    if precision_rate > 70 and error_rate < 10:
        return "Maestro (2400+)"
    elif precision_rate > 60 and error_rate < 15:
        return "Experto (2200-2400)" 
    elif precision_rate > 50 and error_rate < 20:
        return "Avanzado (2000-2200)"
    else:
        return "Intermedio (<2000)"

def generate_recommendations_from_distribution(moves: dict, total: int):
    """Generar recomendaciones basadas en distribución"""
    print(f"\n🎯 RECOMENDACIONES PERSONALIZADAS:")
    
    mistake_rate = moves.get('mistake', 0) / total * 100
    blunder_rate = moves.get('blunder', 0) / total * 100
    inaccuracy_rate = moves.get('inaccuracy', 0) / total * 100
    
    if blunder_rate > 3:
        print(f"   🚨 PRIORIDAD ALTA: Reducir blunders ({blunder_rate:.1f}%)")
        print(f"      💡 Objetivo: <2% blunders")
        print(f"      📚 Ejercicio: Verificar 2 veces antes de mover")
    
    if mistake_rate > 10:
        print(f"   ⚠️ PRIORIDAD MEDIA: Reducir errores ({mistake_rate:.1f}%)")
        print(f"      💡 Objetivo: <8% mistakes")
        print(f"      📚 Ejercicio: Táctica diaria 15 min")
    
    if inaccuracy_rate > 15:
        print(f"   📈 MEJORA: Reducir imprecisiones ({inaccuracy_rate:.1f}%)")
        print(f"      💡 Objetivo: <12% inaccuracies")
        print(f"      📚 Ejercicio: Análisis posicional")

def main():
    """Función principal de demostración"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Análisis con clasificación on-the-fly')
    parser.add_argument('player_name', help='Nombre del jugador')
    parser.add_argument('--min-games', type=int, default=50, help='Mínimo de juegos')
    
    args = parser.parse_args()
    
    print("🎯 ANÁLISIS CON CLASIFICACIÓN ON-THE-FLY")
    print("⚡ SIN modificar base de datos - Solo análisis mejorado")
    print()
    
    analyze_player_with_onthefly_classification(args.player_name, args.min_games)
    
    print(f"\n💡 VENTAJAS DE ESTE ENFOQUE:")
    print(f"   ✅ NO modifica BD existente")
    print(f"   ✅ Análisis inmediato y preciso")  
    print(f"   ✅ Clasificación inteligente on-demand")
    print(f"   ✅ Escalable para cualquier jugador")

if __name__ == "__main__":
    main()