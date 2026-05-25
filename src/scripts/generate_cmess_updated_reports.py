#!/usr/bin/env python3
"""
Generador de Reporte Actualizado para Usuarios cmess
====================================================

Usa datos reales de la base de datos para generar reportes actualizados
"""

import sys
import os
import pandas as pd
import psycopg2
from collections import Counter
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class CMESSReportGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost", port="5432", database="chess_trainer_db",
            user="chess", password="chess_pass"
        )
        print("🎯 Chess Trainer - Reporte Actualizado CMESS")
        print("=" * 50)
    
    def get_cmess_stats(self, username):
        """
        Obtener estadísticas reales de la base de datos
        """
        print(f"📊 Obteniendo estadísticas para {username}...")
        
        # Query principal para estadísticas del jugador
        query = """
        SELECT 
            COUNT(DISTINCT g.game_id) as total_games,
            COUNT(f.game_id) as total_features,
            COUNT(CASE WHEN f.error_label IS NOT NULL THEN 1 END) as labeled_features,
            COUNT(CASE WHEN f.error_label = 'blunder' THEN 1 END) as blunders,
            COUNT(CASE WHEN f.error_label = 'mistake' THEN 1 END) as mistakes,
            COUNT(CASE WHEN f.error_label = 'inaccuracy' THEN 1 END) as inaccuracies,
            COUNT(CASE WHEN f.error_label = 'good' THEN 1 END) as good_moves,
            MIN(g.date_played) as fecha_mas_antigua,
            MAX(g.date_played) as fecha_mas_reciente,
            AVG(CASE WHEN g.white_player = %s THEN CAST(g.white_elo AS INTEGER)
                     ELSE CAST(g.black_elo AS INTEGER) END) as avg_elo
        FROM games g
        LEFT JOIN features f ON g.game_id = f.game_id AND f.error_label IS NOT NULL
        WHERE (g.white_player = %s OR g.black_player = %s)
            AND g.date_played >= '2024.01.01'
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, (username, username, username))
        result = cursor.fetchone()
        cursor.close()
        
        if not result or result[0] == 0:
            return None
            
        stats = {
            'username': username,
            'total_games': result[0],
            'total_features': result[1], 
            'labeled_features': result[2],
            'blunders': result[3] or 0,
            'mistakes': result[4] or 0,
            'inaccuracies': result[5] or 0,
            'good_moves': result[6] or 0,
            'fecha_mas_antigua': result[7],
            'fecha_mas_reciente': result[8],
            'avg_elo': result[9] or 1400
        }
        
        # Calcular porcentajes
        if stats['labeled_features'] > 0:
            total = stats['labeled_features']
            stats['blunder_rate'] = (stats['blunders'] / total) * 100
            stats['mistake_rate'] = (stats['mistakes'] / total) * 100
            stats['inaccuracy_rate'] = (stats['inaccuracies'] / total) * 100
            stats['good_rate'] = (stats['good_moves'] / total) * 100
        else:
            stats['blunder_rate'] = 0
            stats['mistake_rate'] = 0
            stats['inaccuracy_rate'] = 0
            stats['good_rate'] = 0
        
        return stats
    
    def get_level_from_elo(self, avg_elo):
        """
        Determinar nivel basado en ELO
        """
        if avg_elo >= 2200:
            return {
                'level_name': 'EXPERT',
                'expected_blunders': 0.5,
                'expected_mistakes': 8.0,
                'critical_threshold': 'blunders únicamente'
            }
        elif avg_elo >= 1600:
            return {
                'level_name': 'ADVANCED',
                'expected_blunders': 1.5,
                'expected_mistakes': 12.0,
                'critical_threshold': 'blunders únicamente'
            }
        elif avg_elo >= 1200:
            return {
                'level_name': 'INTERMEDIATE',
                'expected_blunders': 3.0,
                'expected_mistakes': 18.0,
                'critical_threshold': 'blunders únicamente'
            }
        else:
            return {
                'level_name': 'BEGINNER',
                'expected_blunders': 6.0,
                'expected_mistakes': 25.0,
                'critical_threshold': 'blunders + mistakes graves'
            }
    
    def generate_updated_report(self, username):
        """
        Generar reporte actualizado con datos reales
        """
        print(f"📋 Generando reporte actualizado para {username}...")
        
        # Obtener estadísticas reales
        stats = self.get_cmess_stats(username)
        
        if not stats:
            print(f"❌ No se encontraron datos para {username}")
            return None
        
        # Determinar nivel
        level_config = self.get_level_from_elo(stats['avg_elo'])
        
        # Calcular errores críticos según nivel
        if level_config['level_name'] in ['EXPERT', 'ADVANCED']:
            critical_errors = stats['blunder_rate']  # Solo blunders
        else:
            critical_errors = stats['blunder_rate'] + (stats['mistake_rate'] * 0.4)
        
        # Crear contenido del reporte
        report_content = f"""🎯 CHESS TRAINER - REPORTE ACTUALIZADO 2024-2025
================================================

👤 Jugador: {username}
📅 Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M')}
🎮 Total partidas: {stats['total_games']:,}
📊 Partidas analizadas: {stats['labeled_features']:,} features de {stats['total_games']:,} partidas
📈 ELO promedio: {stats['avg_elo']:.0f}
🎓 Nivel: {level_config['level_name']}
📅 Período: {stats['fecha_mas_antigua']} → {stats['fecha_mas_reciente']}
✅ DATOS REALES (2 AÑOS DE HISTORIAL)

📈 ANÁLISIS DE ERRORES (DATOS REALES)
====================================
• Blunders: {stats['blunder_rate']:.1f}% ({stats['blunders']:,} movimientos)
• Mistakes: {stats['mistake_rate']:.1f}% ({stats['mistakes']:,} movimientos)
• Inaccuracies: {stats['inaccuracy_rate']:.1f}% ({stats['inaccuracies']:,} movimientos)
• Good moves: {stats['good_rate']:.1f}% ({stats['good_moves']:,} movimientos)

🚨 Errores críticos: {critical_errors:.1f}%
📏 Criterio para {level_config['level_name']}: {level_config['critical_threshold']}

🎯 COMPARACIÓN CON NIVEL ESPERADO
================================
Blunders: {stats['blunder_rate']:.1f}% (esperado: {level_config['expected_blunders']:.1f}%)
Mistakes: {stats['mistake_rate']:.1f}% (esperado: {level_config['expected_mistakes']:.1f}%)

{"✅ BLUNDERS DENTRO DEL RANGO" if abs(stats['blunder_rate'] - level_config['expected_blunders']) < 2 else "⚠️ BLUNDERS FUERA DEL RANGO ESPERADO"}
{"✅ MISTAKES DENTRO DEL RANGO" if abs(stats['mistake_rate'] - level_config['expected_mistakes']) < 5 else "⚠️ MISTAKES FUERA DEL RANGO ESPERADO"}

📊 ESTADÍSTICAS DETALLADAS
=========================
• Total de partidas en BD: {stats['total_games']:,}
• Features generadas: {stats['total_features']:,}  
• Features etiquetadas: {stats['labeled_features']:,}
• Cobertura de análisis: {(stats['labeled_features']/stats['total_features']*100) if stats['total_features'] > 0 else 0:.1f}%
• Promedio features/partida: {(stats['total_features']/stats['total_games']):.1f}

📚 RECOMENDACIONES ESPECÍFICAS PARA {level_config['level_name']}
{'=' * 50}"""

        # Recomendaciones específicas por nivel
        if level_config['level_name'] == 'EXPERT':
            report_content += """
• Foco: Optimización fina y preparación específica
• Táctica: Combinaciones complejas de 4+ jugadas
• Estrategia: Planes a largo plazo y evaluaciones profundas
• Aperturas: Preparación teórica específica por variante
• Objetivo principal: Mantener blunders < 1%
• Tiempo sugerido: 10-15 horas/semana
"""
        elif level_config['level_name'] == 'ADVANCED':
            report_content += """
• Foco: Reducir mistakes posicionales y mejorar cálculo
• Táctica: Problemas de 3-4 jugadas con tiempo limitado
• Estrategia: Evaluación de estructuras de peones complejas
• Finales: Técnicas teóricas avanzadas
• Objetivo principal: Blunders < 2%, Mistakes < 15%
• Tiempo sugerido: 8-12 horas/semana
"""
        elif level_config['level_name'] == 'INTERMEDIATE':
            report_content += """
• Foco: Consolidar fundamentos tácticos y estratégicos
• Táctica: Problemas de 2-3 jugadas diarios
• Estrategia: Principios básicos de evaluación posicional
• Aperturas: 2-3 sistemas principales por color
• Objetivo principal: Blunders < 4%, aumentar good moves > 65%
• Tiempo sugerido: 5-8 horas/semana
"""
        else:
            report_content += """
• Foco: Evitar blunders básicos y mejorar visión táctica
• Táctica: Problemas simples de 1-2 jugadas
• Estrategia: Principios fundamentales (desarrollo, centro, seguridad del rey)
• Aperturas: 1 apertura principal por color
• Objetivo principal: Reducir blunders a < 6%
• Tiempo sugerido: 3-5 horas/semana
"""

        report_content += f"""

🎯 PLAN DE MEJORA PERSONALIZADO
=============================
Basado en {stats['labeled_features']:,} jugadas analizadas:

1. **Prioridad ALTA**: {'Reducir blunders críticos' if stats['blunder_rate'] > level_config['expected_blunders'] else 'Mantener control de blunders'}
2. **Prioridad MEDIA**: {'Optimizar mistakes posicionales' if stats['mistake_rate'] > level_config['expected_mistakes'] else 'Mejorar precisión general'}
3. **Prioridad BAJA**: Incrementar porcentaje de good moves

📈 EVOLUCIÓN TEMPORAL RECOMENDADA
================================
Próximos 3 meses:
• Objetivo blunders: {stats['blunder_rate']:.1f}% → {max(0.5, stats['blunder_rate'] * 0.8):.1f}%
• Objetivo mistakes: {stats['mistake_rate']:.1f}% → {stats['mistake_rate'] * 0.9:.1f}%
• Objetivo good moves: {stats['good_rate']:.1f}% → {min(80, stats['good_rate'] * 1.1):.1f}%

🔬 CONTEXTO TÉCNICO
==================
• Dataset: {stats['total_games']:,} partidas desde enero 2024
• Análisis: {stats['labeled_features']:,} jugadas etiquetadas con Stockfish
• Metodología: Clasificación ML con calibración por nivel ELO
• Última actualización: {datetime.now().strftime('%Y-%m-%d')}

Generado por Chess Trainer - Análisis de Datos Reales 2024-2025
"""

        # Guardar reporte
        import os
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"report_{username}_actualizado_2024-2025.txt"
        filepath = os.path.join(reports_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ Reporte actualizado guardado: {filepath}")
        print(f"📊 Estadísticas:")
        print(f"   • {stats['total_games']:,} partidas totales")
        print(f"   • {stats['labeled_features']:,} jugadas analizadas") 
        print(f"   • ELO {stats['avg_elo']:.0f} - Nivel {level_config['level_name']}")
        print(f"   • Blunders: {stats['blunder_rate']:.1f}% | Mistakes: {stats['mistake_rate']:.1f}%")
        
        return filepath
    
    def generate_comparison_report(self):
        """
        Generar reporte comparativo de ambos usuarios
        """
        print("📊 Generando reporte comparativo...")
        
        reports = []
        for username in ['cmess4401', 'cmess1315']:
            stats = self.get_cmess_stats(username)
            if stats:
                reports.append(stats)
                print(f"✅ Datos encontrados para {username}")
            else:
                print(f"❌ No hay datos para {username}")
        
        if not reports:
            print("❌ No se encontraron datos para ningún usuario")
            return None
        
        # Crear reporte comparativo
        comparison_content = "🎯 CHESS TRAINER - REPORTE COMPARATIVO CMESS\n"
        comparison_content += "=" * 50 + "\n\n"
        
        for i, stats in enumerate(reports, 1):
            level_config = self.get_level_from_elo(stats['avg_elo'])
            comparison_content += f"👤 USUARIO {i}: {stats['username']}\n"
            comparison_content += f"📊 ELO: {stats['avg_elo']:.0f} | Nivel: {level_config['level_name']}\n"
            comparison_content += f"🎮 Partidas: {stats['total_games']:,} | Jugadas analizadas: {stats['labeled_features']:,}\n"
            comparison_content += f"⚠️ Blunders: {stats['blunder_rate']:.1f}% | Mistakes: {stats['mistake_rate']:.1f}%\n"
            comparison_content += f"✅ Good moves: {stats['good_rate']:.1f}%\n\n"
        
        # Guardar comparación
        filepath = os.path.join("reports", "report_cmess_comparison.txt")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(comparison_content)
        
        print(f"✅ Reporte comparativo guardado: {filepath}")
        return filepath
    
    def run_full_update(self):
        """
        Ejecutar actualización completa
        """
        print("🚀 Iniciando actualización completa de reportes CMESS...")
        
        generated_reports = []
        
        # Generar reportes individuales
        for username in ['cmess4401', 'cmess1315']:
            try:
                report_file = self.generate_updated_report(username)
                if report_file:
                    generated_reports.append(report_file)
            except Exception as e:
                print(f"❌ Error generando reporte para {username}: {e}")
        
        # Generar reporte comparativo si hay datos
        if generated_reports:
            try:
                comparison_report = self.generate_comparison_report()
                if comparison_report:
                    generated_reports.append(comparison_report)
            except Exception as e:
                print(f"❌ Error generando reporte comparativo: {e}")
        
        print(f"\n🎉 Actualización completada!")
        print(f"📁 Reportes generados: {len(generated_reports)}")
        for report in generated_reports:
            print(f"   • {os.path.basename(report)}")
        
        self.conn.close()
        return generated_reports

if __name__ == "__main__":
    generator = CMESSReportGenerator()
    reports = generator.run_full_update()