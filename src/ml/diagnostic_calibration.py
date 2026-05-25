#!/usr/bin/env python3
"""
Diagnóstico de Calibración y Generación de Reportes Multi-Nivel
===============================================================

1. Investigar problema de calibración ELO vs errores
2. Generar reportes para cada nivel de jugador
3. Usar username específico para nivel personal
"""

import numpy as np
import pandas as pd
import psycopg2
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

class DiagnosticReportGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost", port="5432", database="chess_trainer_db",
            user="chess", password="chess_pass"
        )
        
        print("🔍 Chess Trainer - Diagnóstico de Calibración")
        print("=" * 50)
    
    def analyze_error_distribution_by_source(self):
        """
        Analizar distribución de errores por fuente/nivel
        """
        print("📊 Analizando distribución de errores por nivel...")
        
        query = """
        SELECT 
            g.source,
            f.error_label,
            COUNT(*) as count,
            AVG(CAST(f.score_diff AS FLOAT)) as avg_score_diff
        FROM features f
        JOIN games g ON f.game_id = g.game_id
        WHERE f.error_label IS NOT NULL
        GROUP BY g.source, f.error_label
        ORDER BY g.source, f.error_label
        """
        
        df = pd.read_sql(query, self.conn)
        
        # Calcular porcentajes por fuente
        results = {}
        for source in df['source'].unique():
            source_data = df[df['source'] == source]
            total = source_data['count'].sum()
            
            distribution = {}
            for _, row in source_data.iterrows():
                error_type = row['error_label']
                count = row['count']
                avg_score = row['avg_score_diff']
                
                distribution[error_type] = {
                    'count': count,
                    'percentage': (count / total) * 100,
                    'avg_score_diff': avg_score
                }
            
            results[source] = distribution
            
            print(f"\n🎯 {source.upper()}:")
            for error_type in ['good', 'inaccuracy', 'mistake', 'blunder']:
                if error_type in distribution:
                    data = distribution[error_type]
                    print(f"   {error_type}: {data['percentage']:.1f}% (avg_cp: {data['avg_score_diff']:.0f})")
        
        return results
    
    def get_players_by_level(self):
        """
        Obtener jugadores representativos por nivel
        """
        print("\n🎮 Identificando jugadores por nivel...")
        
        # Query para obtener jugadores con estadísticas
        query = """
        SELECT 
            COALESCE(g.white_player, g.black_player, 'unknown') as player,
            g.source,
            COUNT(DISTINCT g.game_id) as games_count,
            COUNT(f.error_label) as labeled_moves,
            AVG(CASE WHEN f.error_label = 'blunder' THEN 1.0 ELSE 0.0 END) * 100 as blunder_rate,
            AVG(CASE WHEN f.error_label = 'mistake' THEN 1.0 ELSE 0.0 END) * 100 as mistake_rate,
            AVG(CASE WHEN f.error_label = 'good' THEN 1.0 ELSE 0.0 END) * 100 as good_rate
        FROM games g
        JOIN features f ON g.game_id = f.game_id
        WHERE f.error_label IS NOT NULL
            AND COALESCE(g.white_player, g.black_player, 'unknown') != 'unknown'
        GROUP BY COALESCE(g.white_player, g.black_player, 'unknown'), g.source
        HAVING COUNT(f.error_label) >= 50
        ORDER BY g.source, good_rate DESC
        """
        
        df = pd.read_sql(query, self.conn)
        
        # Seleccionar jugadores representativos
        selected_players = {}
        
        for source in df['source'].unique():
            source_data = df[df['source'] == source]
            
            if source == 'personal' or source == 'novice':
                # Para personal/novice, buscar cmess1315 primero
                user_data = source_data[source_data['player'].str.contains('cmess', case=False, na=False)]
                if not user_data.empty:
                    selected_players[source] = user_data.iloc[0]['player']
                else:
                    # Fallback: jugador con más partidas
                    selected_players[source] = source_data.iloc[0]['player']
            else:
                # Para otros niveles, tomar el jugador más representativo
                selected_players[source] = source_data.iloc[0]['player']
        
        # Agregar cmess1315 manualmente si no está en la BD
        if 'personal' not in selected_players and 'novice' not in selected_players:
            selected_players['personal'] = 'cmess1315'
        
        print("🎯 Jugadores seleccionados:")
        for source, player in selected_players.items():
            games_count = len(df[(df['source'] == source) & (df['player'] == player)])
            print(f"   {source}: {player} ({games_count} partidas)")
        
        return selected_players
    
    def generate_calibrated_report(self, player, source):
        """
        Generar reporte calibrado por nivel
        """
        print(f"\n📝 Generando reporte para {player} ({source})...")
        
        # Si el jugador no existe en BD, crear reporte simulado
        query_check = """
        SELECT COUNT(*) as count 
        FROM games g 
        WHERE g.white_player = %s OR g.black_player = %s
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query_check, (player, player))
        player_exists = cursor.fetchone()[0] > 0
        cursor.close()
        
        if not player_exists:
            return self.generate_simulated_report(player, source)
        
        # Query para estadísticas del jugador
        query = """
        SELECT 
            COUNT(DISTINCT g.game_id) as games_count,
            COUNT(f.error_label) as labeled_moves,
            AVG(CASE WHEN f.error_label = 'blunder' THEN 1.0 ELSE 0.0 END) * 100 as blunder_rate,
            AVG(CASE WHEN f.error_label = 'mistake' THEN 1.0 ELSE 0.0 END) * 100 as mistake_rate,
            AVG(CASE WHEN f.error_label = 'inaccuracy' THEN 1.0 ELSE 0.0 END) * 100 as inaccuracy_rate,
            AVG(CASE WHEN f.error_label = 'good' THEN 1.0 ELSE 0.0 END) * 100 as good_rate,
            g.source
        FROM games g
        JOIN features f ON g.game_id = f.game_id
        WHERE (g.white_player = %s OR g.black_player = %s)
            AND f.error_label IS NOT NULL
        GROUP BY g.source
        """
        
        df = pd.read_sql(query, self.conn, params=(player, player))
        
        if df.empty:
            return self.generate_simulated_report(player, source)
        
        stats = df.iloc[0]
        
        # Calibración por nivel
        level_config = self.get_level_configuration(source)
        
        # Aplicar calibración
        calibrated_stats = self.apply_elo_calibration(stats, level_config)
        
        # Generar reporte
        report_content = self.create_calibrated_report_content(
            player, source, calibrated_stats, level_config
        )
        
        # Guardar reporte
        import os
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"report_{player}_{source}.txt"
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Reporte guardado: {filepath}")
        return filename
    
    def get_level_configuration(self, source):
        """
        Obtener configuración calibrada por nivel
        """
        configs = {
            'novice': {
                'elo_range': '800-1200',
                'expected_blunders': 8.0,
                'expected_mistakes': 25.0,
                'expected_good': 45.0,
                'level_name': 'NOVICE',
                'critical_threshold': 'blunders + mistakes graves'
            },
            'personal': {
                'elo_range': '1200-1600', 
                'expected_blunders': 3.0,
                'expected_mistakes': 18.0,
                'expected_good': 60.0,
                'level_name': 'INTERMEDIATE',
                'critical_threshold': 'blunders únicamente'
            },
            'elite': {
                'elo_range': '2200-2600',
                'expected_blunders': 0.5,
                'expected_mistakes': 8.0,
                'expected_good': 75.0,
                'level_name': 'ELITE',
                'critical_threshold': 'blunders únicamente'
            },
            'stockfish': {
                'elo_range': '3000+',
                'expected_blunders': 0.1,
                'expected_mistakes': 2.0,
                'expected_good': 90.0,
                'level_name': 'ENGINE',
                'critical_threshold': 'solo blunders flagrantes'
            }
        }
        
        return configs.get(source, configs['personal'])
    
    def apply_elo_calibration(self, raw_stats, level_config):
        """
        Aplicar calibración específica por nivel ELO
        """
        # Para niveles altos, ser menos estricto con mistakes
        if level_config['level_name'] in ['ELITE', 'ENGINE']:
            # Reclasificar algunos mistakes como inaccuracies
            mistake_reduction = 0.6  # Reducir mistakes en 60%
            
            calibrated = {
                'blunder_rate': raw_stats['blunder_rate'],
                'mistake_rate': raw_stats['mistake_rate'] * mistake_reduction,
                'inaccuracy_rate': raw_stats['inaccuracy_rate'] + (raw_stats['mistake_rate'] * (1 - mistake_reduction)),
                'good_rate': raw_stats['good_rate'],
                'games_count': raw_stats['games_count'],
                'labeled_moves': raw_stats['labeled_moves']
            }
        else:
            calibrated = {
                'blunder_rate': raw_stats['blunder_rate'],
                'mistake_rate': raw_stats['mistake_rate'],
                'inaccuracy_rate': raw_stats['inaccuracy_rate'], 
                'good_rate': raw_stats['good_rate'],
                'games_count': raw_stats['games_count'],
                'labeled_moves': raw_stats['labeled_moves']
            }
        
        return calibrated
    
    def generate_simulated_report(self, player, source):
        """
        Generar reporte simulado para jugadores no en BD
        """
        print(f"⚠️ Jugador {player} no encontrado - generando reporte simulado")
        
        level_config = self.get_level_configuration(source)
        
        # Estadísticas simuladas realistas
        if source == 'personal' and player == 'cmess1315':
            simulated_stats = {
                'blunder_rate': 2.1,
                'mistake_rate': 15.3,
                'inaccuracy_rate': 22.7,
                'good_rate': 59.9,
                'games_count': 156,
                'labeled_moves': 1847
            }
        else:
            simulated_stats = {
                'blunder_rate': level_config['expected_blunders'],
                'mistake_rate': level_config['expected_mistakes'],
                'inaccuracy_rate': 25.0,
                'good_rate': level_config['expected_good'],
                'games_count': 120,
                'labeled_moves': 1500
            }
        
        report_content = self.create_calibrated_report_content(
            player, source, simulated_stats, level_config, is_simulated=True
        )
        
        import os
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"report_{player}_{source}.txt"
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Reporte simulado guardado: {filepath}")
        return filename
    
    def create_calibrated_report_content(self, player, source, stats, level_config, is_simulated=False):
        """
        Crear contenido del reporte calibrado
        """
        from datetime import datetime
        
        # Calcular errores críticos CORRECTAMENTE
        if level_config['level_name'] in ['ELITE', 'ENGINE']:
            critical_errors = stats['blunder_rate']  # Solo blunders para expertos
        else:
            critical_errors = stats['blunder_rate'] + (stats['mistake_rate'] * 0.3)  # Blunders + mistakes graves
        
        # ELO estimado por fuente
        elo_estimates = {
            'novice': 1000,
            'personal': 1400,
            'elite': 2400,
            'stockfish': 3200
        }
        
        estimated_elo = elo_estimates.get(source, 1400)
        
        report = f"""🎯 CHESS TRAINER - REPORTE CALIBRADO
=====================================

👤 Jugador: {player}
📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎮 Partidas analizadas: {int(stats['games_count'])}
📊 ELO estimado: {estimated_elo}
🎓 Nivel: {level_config['level_name']}
{"⚠️ DATOS SIMULADOS" if is_simulated else "✅ DATOS REALES"}

📈 ANÁLISIS DE ERRORES (CALIBRADO)
---------------------------------
• Blunders: {stats['blunder_rate']:.1f}%
• Mistakes: {stats['mistake_rate']:.1f}%  
• Inaccuracies: {stats['inaccuracy_rate']:.1f}%
• Good moves: {stats['good_rate']:.1f}%

🚨 Errores críticos: {critical_errors:.1f}%
📏 Criterio: {level_config['critical_threshold']}

🎯 COMPARACIÓN CON NIVEL ESPERADO
--------------------------------
Blunders: {stats['blunder_rate']:.1f}% (esperado: {level_config['expected_blunders']:.1f}%)
Mistakes: {stats['mistake_rate']:.1f}% (esperado: {level_config['expected_mistakes']:.1f}%)
Good moves: {stats['good_rate']:.1f}% (esperado: {level_config['expected_good']:.1f}%)

{'✅ DENTRO DEL RANGO ESPERADO' if abs(stats['blunder_rate'] - level_config['expected_blunders']) < 2 else '⚠️ FUERA DEL RANGO ESPERADO'}

📚 RECOMENDACIONES ESPECÍFICAS
-----------------------------
"""

        # Recomendaciones específicas por nivel
        if level_config['level_name'] == 'NOVICE':
            report += """• Foco principal: Evitar blunders básicos
• Táctica: Problemas de 1-2 jugadas
• Tiempo: 20 min táctica diaria
• Objetivo: Reducir blunders a <5%
"""
        elif level_config['level_name'] == 'INTERMEDIATE':
            report += """• Foco principal: Reducir mistakes posicionales
• Táctica: Problemas de 2-3 jugadas
• Estrategia: Principios básicos
• Objetivo: Aumentar good moves a >65%
"""
        elif level_config['level_name'] == 'ELITE':
            report += """• Foco principal: Optimización fina
• Táctica: Combinaciones complejas
• Estrategia: Planes a largo plazo
• Objetivo: Mantener blunders <1%
"""
        else:
            report += """• Análisis de variantes profundas
• Preparación de aperturas específicas
• Finales teóricos avanzados
"""

        report += f"""
🔬 CONTEXTO TÉCNICO
------------------
Calibración aplicada para nivel {level_config['level_name']}
Rango ELO objetivo: {level_config['elo_range']}
Movimientos analizados: {int(stats['labeled_moves'])}

Generado por Chess Trainer - Diagnóstico Calibrado
"""

        return report
    
    def run_full_diagnostic(self):
        """
        Ejecutar diagnóstico completo y generar reportes
        """
        print("🚀 Iniciando diagnóstico completo...")
        
        # 1. Analizar distribución por fuente
        error_distributions = self.analyze_error_distribution_by_source()
        
        # 2. Identificar jugadores por nivel
        selected_players = self.get_players_by_level()
        
        # 3. Generar reportes calibrados
        generated_reports = []
        for source, player in selected_players.items():
            try:
                report_file = self.generate_calibrated_report(player, source)
                generated_reports.append(report_file)
            except Exception as e:
                print(f"❌ Error generando reporte para {player}: {e}")
        
        print(f"\n🎉 Diagnóstico completado!")
        print(f"📁 Reportes generados: {len(generated_reports)}")
        for report in generated_reports:
            print(f"   • {report}")
        
        self.conn.close()
        return generated_reports

if __name__ == "__main__":
    diagnostic = DiagnosticReportGenerator()
    reports = diagnostic.run_full_diagnostic()