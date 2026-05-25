#!/usr/bin/env python3
"""
Análisis detallado de rachas de errores con información específica de partidas y movimientos
Muestra exactamente dónde ocurrieron las rachas de errores más largas
"""

import sys
import argparse
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime
import os
from pathlib import Path

# Agregar el directorio src al path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from db.models.games import Games
from db.models.features import Features
from db.session import get_session
from dotenv import load_dotenv

load_dotenv()

class DetailedStreakAnalyzer:
    def __init__(self, player_name):
        self.player_name = player_name
        self.session = get_session()
        self.features_data = None
        
    def connect_to_database(self):
        """Verificar conexión a la base de datos"""
        try:
            # Probar la sesión
            test_query = self.session.query(Games).limit(1).all()
            print(f"✅ Conectado a la base de datos correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error conectando a la base de datos: {e}")
            return False
    
    def load_player_data(self):
        """Cargar datos de features del jugador usando SQLAlchemy"""
        try:
            # Query usando SQLAlchemy
            query = self.session.query(
                Features.game_id,
                Features.move_number,
                Features.error_label,
                Features.score_diff,
                Features.player_color,
                Games.white_player,
                Games.black_player,
                Games.date_played,
                Games.result,
                Games.white_elo,
                Games.black_elo,
                Games.eco,
                Games.opening,
                Features.move_san,
                Features.fen
            ).join(
                Games, Features.game_id == Games.game_id
            ).filter(
                (Games.white_player.ilike(f'%{self.player_name}%')) | 
                (Games.black_player.ilike(f'%{self.player_name}%'))
            ).order_by(
                Games.date_played.desc(),
                Features.game_id,
                Features.move_number
            )
            
            # Convertir a DataFrame
            results = query.all()
            
            if not results:
                print(f"❌ No se encontraron datos para el jugador '{self.player_name}'")
                return False
            
            # Crear DataFrame
            data = []
            for row in results:
                data.append({
                    'game_id': row.game_id,
                    'move_number': row.move_number,
                    'error_label': row.error_label,
                    'score_diff': row.score_diff,
                    'player_color': row.player_color,  # 1 for white, 0 for black
                    'white_player': row.white_player,
                    'black_player': row.black_player,
                    'date_played': row.date_played,
                    'result': row.result,
                    'white_elo': row.white_elo,
                    'black_elo': row.black_elo,
                    'eco': row.eco,
                    'opening': row.opening,
                    'move_san': row.move_san,
                    'fen': row.fen
                })
            
            self.features_data = pd.DataFrame(data)
            
            # Filtrar solo los movimientos del jugador objetivo
            player_moves = self.features_data[
                ((self.features_data['white_player'].str.contains(self.player_name, case=False, na=False)) & 
                 (self.features_data['player_color'] == 1)) |
                ((self.features_data['black_player'].str.contains(self.player_name, case=False, na=False)) & 
                 (self.features_data['player_color'] == 0))
            ]
            
            self.features_data = player_moves
            
            print(f"✅ Cargados {len(self.features_data)} movimientos de {len(self.features_data['game_id'].unique())} partidas")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
            return False
    
    def analyze_detailed_streaks(self):
        """Análisis detallado de rachas con información específica"""
        if self.features_data is None or len(self.features_data) == 0:
            print("❌ No hay datos para analizar")
            return None
        
        print(f"\n🔍 ANÁLISIS DETALLADO DE RACHAS - {self.player_name.upper()}")
        print("=" * 80)
        
        # Agrupar por partida
        game_groups = self.features_data.groupby('game_id')
        all_streaks = []
        detailed_streaks = []
        game_streak_info = {}
        
        for game_id, moves in game_groups:
            moves_sorted = moves.sort_values('move_number')
            current_streak = 0
            streak_start = None
            streak_moves = []
            
            # Obtener información general de la partida
            game_info = moves_sorted.iloc[0]
            opponent = game_info['black_player'] if game_info['player_color'] == 1 else game_info['white_player']
            date_played = game_info['date_played']
            player_color = "Blancas" if game_info['player_color'] == 1 else "Negras"
            opening = f"{game_info.get('eco', 'N/A')} - {game_info.get('opening', 'N/A')}"
            
            for _, move in moves_sorted.iterrows():
                if move['error_label'] in ['mistake', 'blunder', 'inaccuracy']:
                    if current_streak == 0:
                        streak_start = move['move_number']
                        streak_moves = []
                    
                    current_streak += 1
                    streak_moves.append({
                        'move_number': move['move_number'],
                        'error_type': move['error_label'],
                        'score_diff': move['score_diff'],
                        'move_san': move.get('move_san', 'N/A')
                    })
                else:
                    if current_streak > 0:
                        # Guardar información detallada de la racha
                        streak_info = {
                            'game_id': game_id,
                            'streak_length': current_streak,
                            'start_move': streak_start,
                            'end_move': streak_moves[-1]['move_number'],
                            'moves': streak_moves.copy(),
                            'opponent': opponent,
                            'date': date_played,
                            'color': player_color,
                            'opening': opening,
                            'game_info': game_info
                        }
                        
                        detailed_streaks.append(streak_info)
                        all_streaks.append(current_streak)
                        
                    current_streak = 0
                    streak_moves = []
            
            # Racha final si existe
            if current_streak > 0:
                streak_info = {
                    'game_id': game_id,
                    'streak_length': current_streak,
                    'start_move': streak_start,
                    'end_move': streak_moves[-1]['move_number'],
                    'moves': streak_moves.copy(),
                    'opponent': opponent,
                    'date': date_played,
                    'color': player_color,
                    'opening': opening,
                    'game_info': game_info
                }
                
                detailed_streaks.append(streak_info)
                all_streaks.append(current_streak)
        
        if not all_streaks:
            print("✅ ¡Excelente! No se encontraron rachas de errores.")
            return None
        
        # Estadísticas generales
        max_streak = max(all_streaks)
        avg_streak = np.mean(all_streaks)
        total_streaks = len(all_streaks)
        streak_distribution = Counter(all_streaks)
        
        print(f"📊 ESTADÍSTICAS GENERALES:")
        print(f"   • Racha máxima: {max_streak} errores consecutivos")
        print(f"   • Racha promedio: {avg_streak:.1f}")
        print(f"   • Total de rachas: {total_streaks}")
        print(f"   • Distribución: {dict(streak_distribution)}")
        
        # Mostrar las rachas más largas
        detailed_streaks.sort(key=lambda x: x['streak_length'], reverse=True)
        
        print(f"\n🔥 RACHAS MÁS LARGAS (Top 10):")
        print("-" * 80)
        
        for i, streak in enumerate(detailed_streaks[:10], 1):
            print(f"\n#{i} - RACHA DE {streak['streak_length']} ERRORES:")
            print(f"   📅 Fecha: {streak['date']}")
            print(f"   🎯 Vs: {streak['opponent']} (jugando con {streak['color']})")
            print(f"   🎮 Partida ID: {streak['game_id']}")
            print(f"   📍 Movimientos: {streak['start_move']} al {streak['end_move']}")
            print(f"   🎲 Apertura: {streak['opening']}")
            
            print(f"   🎯 DETALLES DE LOS ERRORES:")
            for j, error_move in enumerate(streak['moves'], 1):
                score_info = f"Score diff: {error_move['score_diff']:.2f}" if error_move['score_diff'] is not None else "Score diff: N/A"
                move_san = error_move.get('move_san', 'N/A')
                
                print(f"      {j}. Mov {error_move['move_number']}: {error_move['error_type'].upper()} | {move_san} | {score_info}")
        
        # Análisis de patrones
        self.analyze_streak_patterns(detailed_streaks)
        
        return {
            'max_streak': max_streak,
            'avg_streak': avg_streak,
            'total_streaks': total_streaks,
            'distribution': dict(streak_distribution),
            'detailed_streaks': detailed_streaks
        }
    
    def analyze_streak_patterns(self, detailed_streaks):
        """Analizar patrones en las rachas"""
        print(f"\n📈 ANÁLISIS DE PATRONES:")
        print("-" * 50)
        
        # Patrones por color
        by_color = defaultdict(list)
        for streak in detailed_streaks:
            by_color[streak['color']].append(streak['streak_length'])
        
        if by_color:
            print(f"🎨 Por color:")
            for color, lengths in by_color.items():
                avg_length = np.mean(lengths)
                count = len(lengths)
                print(f"   • {color}: {count} rachas, promedio {avg_length:.1f}")
        
        # Patrones por fase del juego
        early_game = [s for s in detailed_streaks if s['start_move'] <= 15]
        middle_game = [s for s in detailed_streaks if 16 <= s['start_move'] <= 30]
        late_game = [s for s in detailed_streaks if s['start_move'] > 30]
        
        print(f"\n🎯 Por fase del juego:")
        print(f"   • Apertura (mov 1-15): {len(early_game)} rachas")
        print(f"   • Medio juego (mov 16-30): {len(middle_game)} rachas") 
        print(f"   • Final (mov 30+): {len(late_game)} rachas")
        
        # Las 5 rachas más recientes
        recent_streaks = sorted(detailed_streaks, key=lambda x: x['date'], reverse=True)[:5]
        
        print(f"\n🕐 RACHAS MÁS RECIENTES:")
        for i, streak in enumerate(recent_streaks, 1):
            print(f"   {i}. {streak['date']}: {streak['streak_length']} errores (mov {streak['start_move']}-{streak['end_move']})")
    
    def save_detailed_report(self, results, output_file=None):
        """Guardar reporte detallado en archivo"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            output_file = f"reports/detailed_streaks_{self.player_name}_{timestamp}.md"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 🔥 Análisis Detallado de Rachas - {self.player_name}\n\n")
            f.write(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Estadísticas generales
            f.write(f"## 📊 Estadísticas Generales\n\n")
            f.write(f"- **Racha máxima**: {results['max_streak']} errores consecutivos\n")
            f.write(f"- **Racha promedio**: {results['avg_streak']:.1f}\n") 
            f.write(f"- **Total rachas**: {results['total_streaks']}\n")
            f.write(f"- **Distribución**: {results['distribution']}\n\n")
            
            # Detalles de rachas
            f.write(f"## 🔍 Detalles de Todas las Rachas\n\n")
            
            for i, streak in enumerate(results['detailed_streaks'], 1):
                f.write(f"### Racha #{i} - {streak['streak_length']} errores\n\n")
                f.write(f"- **Fecha**: {streak['date']}\n")
                f.write(f"- **Oponente**: {streak['opponent']}\n")
                f.write(f"- **Color**: {streak['color']}\n")
                f.write(f"- **Partida ID**: {streak['game_id']}\n")
                f.write(f"- **Movimientos**: {streak['start_move']} al {streak['end_move']}\n")
                f.write(f"- **Apertura**: {streak.get('eco', 'N/A')} - {streak.get('opening', 'N/A')}\n\n")
                
                f.write(f"**Errores detallados:**\n")
                for j, move in enumerate(streak['moves'], 1):
                    score_info = ""
                    if move['score_diff'] is not None:
                        score_info = f" (Score diff: {move['score_diff']:.2f})"
                    
                    move_san = move.get('move_san', 'N/A')
                    
                    f.write(f"{j}. Movimiento {move['move_number']}: **{move['error_type'].upper()}** - {move_san}{score_info}\n")
                
                f.write(f"\n---\n\n")
        
        print(f"\n💾 Reporte detallado guardado en: {output_file}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description='Análisis detallado de rachas de errores')
    parser.add_argument('player_name', help='Nombre del jugador a analizar')
    parser.add_argument('--output', '-o', help='Archivo de salida para el reporte detallado')
    parser.add_argument('--max-streaks', '-m', type=int, default=20, help='Máximo número de rachas a mostrar en detalle')
    
    args = parser.parse_args()
    
    print(f"🔍 Iniciando análisis detallado de rachas para: {args.player_name}")
    print("=" * 80)
    
    # Crear analizador
    analyzer = DetailedStreakAnalyzer(args.player_name)
    
    # Conectar y cargar datos
    if not analyzer.connect_to_database():
        sys.exit(1)
    
    if not analyzer.load_player_data():
        sys.exit(1)
    
    # Realizar análisis
    results = analyzer.analyze_detailed_streaks()
    
    if results:
        # Guardar reporte detallado
        output_file = analyzer.save_detailed_report(results, args.output)
        
        print(f"\n🎯 CONCLUSIÓN:")
        print(f"   La racha máxima de {results['max_streak']} errores consecutivos")
        print(f"   indica un nivel de control emocional {'excelente' if results['max_streak'] <= 2 else 'bueno' if results['max_streak'] <= 3 else 'mejorable'}.")
        
        if results['max_streak'] <= 2:
            print(f"   ✅ {args.player_name} mantiene la compostura y se recupera rápido de los errores.")
        elif results['max_streak'] <= 3:
            print(f"   ⚠️ {args.player_name} ocasionalmente comete errores en serie, pero se controla bien.")
        else:
            print(f"   🔥 {args.player_name} puede beneficiarse de trabajo en control emocional y concentración.")
    
    # Cerrar sesión
    if analyzer.session:
        analyzer.session.close()

if __name__ == "__main__":
    main()