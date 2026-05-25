#!/usr/bin/env python3
"""
Script genérico para análisis completo de cualquier jugador
Uso: python analyze_player.py <player_name> [--min-games 100] [--output-dir reports]
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from collections import Counter, defaultdict

# Agregar el directorio src al path
current_dir = Path(__file__).parent
src_dir = current_dir.parent
sys.path.append(str(src_dir))

from db.models.games import Games
from db.models.features import Features
from db.session import get_session
from dotenv import load_dotenv

load_dotenv()

class PlayerAnalyzer:
    """Clase para análisis completo de jugadores"""
    
    def __init__(self, player_name: str, min_games: int = 50):
        self.player_name = player_name
        self.min_games = min_games
        self.session = get_session()
        self.games_data = None
        self.features_data = None
        
    def collect_games_data(self):
        """Recolectar datos de juegos del jugador"""
        print(f"📊 RECOLECTANDO DATOS DE JUEGOS PARA {self.player_name}...")
        
        games = self.session.query(Games).filter(
            (Games.white_player.ilike(f'%{self.player_name}%')) | 
            (Games.black_player.ilike(f'%{self.player_name}%'))
        ).all()
        
        if len(games) < self.min_games:
            print(f"⚠️ Datos insuficientes: {len(games)} juegos encontrados (mínimo: {self.min_games})")
            return False
            
        print(f"✅ {len(games)} juegos encontrados")
        
        # Procesar datos
        games_list = []
        for game in games:
            is_white = game.white_player.lower().find(self.player_name.lower()) != -1
            player_elo = game.white_elo if is_white else game.black_elo
            opponent_elo = game.black_elo if is_white else game.white_elo
            
            # Determinar resultado desde perspectiva del jugador
            if game.result == "1-0":
                result = "win" if is_white else "loss"
            elif game.result == "0-1":
                result = "loss" if is_white else "win"
            else:
                result = "draw"
            
            games_list.append({
                'game_id': game.game_id,
                'color': 'white' if is_white else 'black',
                'player_elo': self._safe_int(player_elo),
                'opponent_elo': self._safe_int(opponent_elo),
                'result': result,
                'time_control': game.time_control or 'unknown',
                'opening': game.opening or 'unknown',
                'eco': game.eco or '',
                'date_played': game.date_played or '',
                'source': game.source or 'unknown'
            })
        
        self.games_data = pd.DataFrame(games_list)
        return True
        
    def collect_features_data(self):
        """Recolectar features de ML si están disponibles"""
        print(f"🤖 VERIFICANDO FEATURES PARA ML...")
        
        features = self.session.query(Features).join(
            Games, Features.game_id == Games.game_id
        ).filter(
            (Games.white_player.ilike(f'%{self.player_name}%')) | 
            (Games.black_player.ilike(f'%{self.player_name}%'))
        ).all()
        
        print(f"   🔢 Features disponibles: {len(features)}")
        
        if len(features) < 50:
            print(f"   ⚠️ Pocas features para análisis ML completo")
            return False
        
        # Procesar features
        features_list = []
        for feature in features:
            # Extraer tags del JSON si existe
            tags_data = feature.tags if feature.tags else {}
            main_tag = 'none'
            if isinstance(tags_data, dict):
                main_tag = tags_data.get('primary_tag', 'none')
            elif isinstance(tags_data, list) and tags_data:
                main_tag = tags_data[0] if tags_data[0] else 'none'
            
            features_list.append({
                'game_id': feature.game_id,
                'move_number': feature.move_number or 0,
                'error_label': feature.error_label or 'unknown',
                'score_diff': feature.score_diff or 0,
                'player_color': feature.player_color or 0,
                'tag': main_tag
            })
        
        if features_list:
            self.features_data = pd.DataFrame(features_list)
            print(f"   ✅ Suficientes features para análisis ML")
            return True
        return False
        
    def analyze_game_statistics(self):
        """Análisis estadístico básico de juegos"""
        if self.games_data is None:
            return {}
            
        stats = {}
        
        # Estadísticas por color
        white_games = self.games_data[self.games_data['color'] == 'white']
        black_games = self.games_data[self.games_data['color'] == 'black']
        
        stats['games_as_white'] = len(white_games)
        stats['games_as_black'] = len(black_games)
        stats['total_games'] = len(self.games_data)
        
        # ELO promedio
        stats['avg_elo_white'] = white_games['player_elo'].mean() if len(white_games) > 0 else 0
        stats['avg_elo_black'] = black_games['player_elo'].mean() if len(black_games) > 0 else 0
        
        # Resultados por color
        white_results = white_games['result'].value_counts() if len(white_games) > 0 else pd.Series()
        black_results = black_games['result'].value_counts() if len(black_games) > 0 else pd.Series()
        
        stats['white_wins'] = white_results.get('win', 0)
        stats['white_draws'] = white_results.get('draw', 0)
        stats['white_losses'] = white_results.get('loss', 0)
        stats['white_win_rate'] = (stats['white_wins'] / max(1, stats['games_as_white'])) * 100
        
        stats['black_wins'] = black_results.get('win', 0)
        stats['black_draws'] = black_results.get('draw', 0)
        stats['black_losses'] = black_results.get('loss', 0)
        stats['black_win_rate'] = (stats['black_wins'] / max(1, stats['games_as_black'])) * 100
        
        # Totales
        total_results = self.games_data['result'].value_counts()
        stats['total_wins'] = total_results.get('win', 0)
        stats['total_draws'] = total_results.get('draw', 0)
        stats['total_losses'] = total_results.get('loss', 0)
        stats['overall_win_rate'] = (stats['total_wins'] / stats['total_games']) * 100
        
        # Controles de tiempo más populares
        time_controls = self.games_data['time_control'].value_counts().head(5)
        stats['top_time_controls'] = time_controls.to_dict()
        
        # Aperturas más jugadas
        openings = self.games_data['opening'].value_counts().head(5)
        stats['top_openings'] = openings.to_dict()
        
        return stats
        
    def analyze_errors_and_streaks(self):
        """Análisis de errores y rachas"""
        if self.features_data is None:
            return {}
            
        error_stats = {}
        
        # Distribución de errores
        error_dist = self.features_data['error_label'].value_counts()
        error_stats['error_distribution'] = error_dist.to_dict()
        
        # Calcular porcentajes
        total_moves = len(self.features_data)
        error_percentages = {}
        for error_type, count in error_dist.items():
            error_percentages[error_type] = (count / total_moves) * 100
        error_stats['error_percentages'] = error_percentages
        
        # Análisis de rachas (secuencias consecutivas de errores)
        streaks = self._calculate_error_streaks()
        error_stats['streaks'] = streaks
        
        return error_stats
        
    def _calculate_error_streaks(self):
        """Calcular rachas de errores consecutivos"""
        # Agrupar por juego y ordenar por número de movimiento
        game_groups = self.features_data.groupby('game_id')
        all_streaks = []
        
        for game_id, moves in game_groups:
            moves_sorted = moves.sort_values('move_number')
            current_streak = 0
            max_streak = 0
            
            for _, move in moves_sorted.iterrows():
                if move['error_label'] in ['mistake', 'blunder', 'inaccuracy']:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    if current_streak > 0:
                        all_streaks.append(current_streak)
                    current_streak = 0
            
            # Agregar racha final si existe
            if current_streak > 0:
                all_streaks.append(current_streak)
        
        if not all_streaks:
            return {'max_streak': 0, 'avg_streak': 0, 'total_streaks': 0}
        
        return {
            'max_streak': max(all_streaks),
            'avg_streak': np.mean(all_streaks),
            'total_streaks': len(all_streaks),
            'streak_distribution': Counter(all_streaks)
        }
        
    def generate_recommendations(self, stats, error_stats):
        """Generar recomendaciones personalizadas"""
        recommendations = []
        
        # Basado en ELO promedio
        avg_elo = (stats.get('avg_elo_white', 0) + stats.get('avg_elo_black', 0)) / 2
        
        if avg_elo >= 2400:
            level = "Maestro"
            level_recommendations = self._get_master_recommendations(stats, error_stats)
        elif avg_elo >= 2200:
            level = "Experto"
            level_recommendations = self._get_expert_recommendations(stats, error_stats)
        elif avg_elo >= 2000:
            level = "Avanzado"
            level_recommendations = self._get_advanced_recommendations(stats, error_stats)
        else:
            level = "Intermedio"
            level_recommendations = self._get_intermediate_recommendations(stats, error_stats)
        
        recommendations.extend(level_recommendations)
        
        # Recomendaciones basadas en errores
        if error_stats and 'error_percentages' in error_stats:
            error_recommendations = self._get_error_recommendations(error_stats['error_percentages'])
            recommendations.extend(error_recommendations)
        
        return {
            'player_level': level,
            'avg_elo': avg_elo,
            'recommendations': recommendations
        }
        
    def _get_master_recommendations(self, stats, error_stats):
        """Recomendaciones para nivel maestro (2400+)"""
        return [
            {
                'title': 'Perfeccionamiento en Finales Complejos',
                'description': 'Enfoque en finales de alta precisión teórica',
                'exercises': [
                    'Finales de Torres con múltiples peones',
                    'Finales de piezas menores vs peones pasados',
                    'Conversiones exactas en finales ganados'
                ]
            },
            {
                'title': 'Optimización de Apertura según Oponente',
                'description': 'Preparación específica basada en repertorio enemigo',
                'exercises': [
                    'Análisis de bases de datos de oponentes fuertes',
                    'Preparación de sorpresas teóricas',
                    'Dominio de sistemas universales'
                ]
            }
        ]
        
    def _get_expert_recommendations(self, stats, error_stats):
        """Recomendaciones para nivel experto (2200-2400)"""
        return [
            {
                'title': 'Precisión Táctica Avanzada',
                'description': 'Mejora en cálculo profundo y verificación',
                'exercises': [
                    'Combinaciones de 5+ movimientos',
                    'Análisis sin mover piezas',
                    'Verificación sistemática de tácticas enemigas'
                ]
            },
            {
                'title': 'Planificación Estratégica a Largo Plazo',
                'description': 'Desarrollo de planes complejos multi-fase',
                'exercises': [
                    'Análisis de partidas clásicas',
                    'Identificación de debilidades menores',
                    'Coordinación de piezas en ataques complejos'
                ]
            }
        ]
        
    def _get_advanced_recommendations(self, stats, error_stats):
        """Recomendaciones para nivel avanzado (2000-2200)"""
        return [
            {
                'title': 'Mejora en Middlegame',
                'description': 'Profundización en planes típicos del medio juego',
                'exercises': [
                    'Estructuras de peones típicas',
                    'Ataques coordinados Rey-Dama',
                    'Defensa activa vs ataques directos'
                ]
            }
        ]
        
    def _get_intermediate_recommendations(self, stats, error_stats):
        """Recomendaciones para nivel intermedio (<2000)"""
        return [
            {
                'title': 'Fundamentos Tácticos',
                'description': 'Consolidación de patrones tácticos básicos',
                'exercises': [
                    'Motivos tácticos básicos (clavada, horqueta, etc.)',
                    'Cálculo simple de 2-3 movimientos',
                    'Reconocimiento rápido de amenazas'
                ]
            }
        ]
        
    def _get_error_recommendations(self, error_percentages):
        """Recomendaciones basadas en tipos de errores"""
        recommendations = []
        
        mistake_rate = error_percentages.get('mistake', 0)
        blunder_rate = error_percentages.get('blunder', 0)
        inaccuracy_rate = error_percentages.get('inaccuracy', 0)
        
        if blunder_rate > 3:
            recommendations.append({
                'title': 'Control de Blunders Críticos',
                'description': f'Tasa de blunders: {blunder_rate:.1f}% (objetivo: <3%)',
                'exercises': [
                    'Verificación sistemática antes de cada movimiento',
                    'Práctica de "movimiento candidato"',
                    'Pausas mentales en posiciones críticas'
                ]
            })
            
        if mistake_rate > 15:
            recommendations.append({
                'title': 'Reducción de Errores Tácticos',
                'description': f'Tasa de errores: {mistake_rate:.1f}% (objetivo: <12%)',
                'exercises': [
                    'Ejercicios diarios de táctica',
                    'Análisis profundo de errores propios',
                    'Práctica de cálculo sin prisa'
                ]
            })
            
        return recommendations
        
    def generate_report(self, output_dir: Path):
        """Generar reporte completo"""
        stats = self.analyze_game_statistics()
        error_stats = self.analyze_errors_and_streaks()
        recommendations = self.generate_recommendations(stats, error_stats)
        
        # Crear reporte markdown
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        report_filename = f"{self.player_name.lower()}_analysis_{timestamp}.md"
        report_path = output_dir / report_filename
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 📊 Análisis Completo: {self.player_name}\n\n")
            f.write(f"**Generado**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Resumen ejecutivo
            f.write("## 🎯 Resumen Ejecutivo\n\n")
            f.write(f"- **Nivel**: {recommendations['player_level']}\n")
            f.write(f"- **ELO Promedio**: {recommendations['avg_elo']:.0f}\n")
            f.write(f"- **Total Partidas**: {stats['total_games']}\n")
            f.write(f"- **Tasa de Victoria**: {stats['overall_win_rate']:.1f}%\n\n")
            
            # Estadísticas detalladas
            f.write("## 📈 Estadísticas de Juego\n\n")
            f.write(f"### Por Color\n")
            f.write(f"- **Blanco**: {stats['games_as_white']} partidas, {stats['white_win_rate']:.1f}% victorias\n")
            f.write(f"- **Negro**: {stats['games_as_black']} partidas, {stats['black_win_rate']:.1f}% victorias\n\n")
            
            # Controles de tiempo
            f.write("### ⏰ Controles de Tiempo Preferidos\n")
            for tc, count in stats['top_time_controls'].items():
                percentage = (count / stats['total_games']) * 100
                f.write(f"- {tc}: {count} partidas ({percentage:.1f}%)\n")
            f.write("\n")
            
            # Aperturas
            f.write("### 🎼 Aperturas Más Jugadas\n")
            for opening, count in stats['top_openings'].items():
                f.write(f"- {opening}: {count} partidas\n")
            f.write("\n")
            
            # Análisis de errores
            if error_stats:
                f.write("## 🎯 Análisis de Errores\n\n")
                if 'error_percentages' in error_stats:
                    f.write("### Distribución de Errores\n")
                    for error_type, percentage in error_stats['error_percentages'].items():
                        f.write(f"- {error_type}: {percentage:.1f}%\n")
                    f.write("\n")
                
                if 'streaks' in error_stats:
                    streaks = error_stats['streaks']
                    f.write("### 🔥 Análisis de Rachas\n")
                    f.write(f"- **Racha máxima**: {streaks['max_streak']} errores consecutivos\n")
                    f.write(f"- **Racha promedio**: {streaks['avg_streak']:.1f}\n")
                    f.write(f"- **Total rachas**: {streaks['total_streaks']}\n\n")
            
            # Recomendaciones
            f.write("## 🎯 Recomendaciones Personalizadas\n\n")
            for i, rec in enumerate(recommendations['recommendations'], 1):
                f.write(f"### {i}. {rec['title']}\n")
                f.write(f"**{rec['description']}**\n\n")
                f.write("**Ejercicios sugeridos:**\n")
                for exercise in rec['exercises']:
                    f.write(f"- {exercise}\n")
                f.write("\n")
        
        return report_path
        
    def _safe_int(self, value):
        """Conversión segura a entero"""
        try:
            return int(value) if value and value != '?' else 0
        except (ValueError, TypeError):
            return 0
            
    def close(self):
        """Cerrar conexión de base de datos"""
        self.session.close()

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Análisis completo de jugador')
    parser.add_argument('player_name', help='Nombre del jugador a analizar')
    parser.add_argument('--min-games', type=int, default=50,
                       help='Mínimo número de juegos requeridos (default: 50)')
    parser.add_argument('--output-dir', default='reports',
                       help='Directorio de salida para reportes (default: reports)')
    
    args = parser.parse_args()
    
    # Crear directorio de salida
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"🚀 ANÁLISIS COMPLETO DE {args.player_name.upper()}")
    print("=" * 60)
    
    # Crear analizador
    analyzer = PlayerAnalyzer(args.player_name, args.min_games)
    
    try:
        # Recolectar datos de juegos
        if not analyzer.collect_games_data():
            print(f"❌ No hay suficientes datos para análisis")
            return 1
        
        # Recolectar features (opcional)
        analyzer.collect_features_data()
        
        # Generar reporte
        report_path = analyzer.generate_report(output_dir)
        
        print(f"\n📄 Reporte guardado en: {report_path}")
        print("✅ ANÁLISIS COMPLETADO!")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error durante análisis: {str(e)}")
        return 1
        
    finally:
        analyzer.close()

if __name__ == "__main__":
    sys.exit(main())