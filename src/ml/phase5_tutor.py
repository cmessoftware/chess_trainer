#!/usr/bin/env python3
"""
PHASE 5 - Tutor Adaptativo y Reportes
====================================

Objetivo: Convertir predicciones en entrenamiento accionable

Componentes:
- Ranking de debilidades por jugador
- Portafolio de ejercicios personalizados  
- Reglas pedagógicas
- Reporte PDF por jugador
- Plan de entrenamiento adaptativo

Outputs:
- Plan de entrenamiento personalizado
- Estadísticas por fase del juego
- Progreso y regresión
- Recomendaciones específicas

Métricas: Reducción de errores repetidos, tendencia de mejora
"""

import numpy as np
import pandas as pd
from collections import Counter, defaultdict
import json
from datetime import datetime, timedelta
import psycopg2
import warnings
warnings.filterwarnings('ignore')

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.backends.backend_pdf import PdfPages
    PLOT_AVAILABLE = True
    print("✅ Matplotlib disponible para reportes PDF")
except ImportError:
    PLOT_AVAILABLE = False
    print("⚠️ Matplotlib no disponible - solo reportes texto")

class Phase5AdaptiveTutor:
    def __init__(self):
        """
        Phase 5: Sistema de tutor adaptativo y generación de reportes
        """
        
        # Resultados de fases anteriores (para usar en recomendaciones)
        self.phase_results = {
            'phase1_rf_f1': 1.000,
            'phase2_mlp_f1': 0.9679,
            'phase3_temporal_f1': 0.7497,
            'phase4_coherence': 0.569
        }
        
        # Reglas pedagógicas predefinidas
        self.pedagogical_rules = {
            'blunder': {
                'priority': 1,  # Máxima prioridad
                'description': 'Errores graves que pierden material o posición',
                'recommendation': 'Practicar cálculo de variantes y verificación antes de mover',
                'exercises': ['tactical_puzzles', 'calculation_training', 'blunder_check'],
                'time_allocation': 0.4  # 40% del tiempo de entrenamiento
            },
            'mistake': {
                'priority': 2,
                'description': 'Errores significativos que empeoran la posición',
                'recommendation': 'Mejorar evaluación posicional y planificación',
                'exercises': ['positional_puzzles', 'plan_training', 'evaluation_practice'],
                'time_allocation': 0.3
            },
            'inaccuracy': {
                'priority': 3,
                'description': 'Jugadas subóptimas pero no críticas',
                'recommendation': 'Refinar técnica y conocimiento de patrones',
                'exercises': ['pattern_recognition', 'endgame_technique', 'opening_principles'],
                'time_allocation': 0.2
            },
            'good': {
                'priority': 4,
                'description': 'Jugadas correctas - mantener nivel',
                'recommendation': 'Continuar con el enfoque actual',
                'exercises': ['maintain_level', 'advanced_concepts'],
                'time_allocation': 0.1
            }
        }
        
        print("🎓 Chess Trainer - Phase 5 Adaptive Tutor")
        print("=" * 45)
        print(f"📚 Reglas pedagógicas: {len(self.pedagogical_rules)}")
        print(f"📊 PDF Reports: {'✅' if PLOT_AVAILABLE else '❌'}")
        
    def load_player_data_from_db(self, limit=30000):
        """
        Cargar datos completos de jugadores para análisis personalizado
        """
        print("📊 Cargando datos de jugadores...")
        
        conn = psycopg2.connect(
            host="localhost", port="5432", database="chess_trainer_db",
            user="chess", password="chess_pass"
        )
        
        query = f"""
        SELECT 
            f.game_id, f.move_number, f.player_color,
            f.material_balance, f.material_total, f.num_pieces,
            f.branching_factor, f.self_mobility, f.opponent_mobility,
            f.has_castling_rights, f.is_repetition, f.is_low_mobility,
            f.is_center_controlled, f.is_pawn_endgame, f.score_diff,
            f.error_label, f.phase,
            g.source, g.white_player, g.black_player, g.result,
            g.white_elo, g.black_elo
        FROM features f 
        JOIN games g ON f.game_id = g.game_id 
        WHERE f.error_label IS NOT NULL
        ORDER BY f.game_id, f.move_number
        LIMIT {limit}
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Crear identificador único de jugador por jugada
        df['player_name'] = df.apply(
            lambda row: row['white_player'] if row['player_color'] == 1 else row['black_player'], 
            axis=1
        )
        df['player_elo'] = df.apply(
            lambda row: row['white_elo'] if row['player_color'] == 1 else row['black_elo'], 
            axis=1
        )
        
        # Limpiar ELO: manejar valores problemáticos
        df['player_elo'] = pd.to_numeric(df['player_elo'], errors='coerce')
        
        # Filtrar valores ELO válidos (entre 800 y 3000)
        df = df[(df['player_elo'] >= 800) & (df['player_elo'] <= 3000)].copy()
        
        # Rellenar ELOs faltantes con la media por fuente
        elo_means_by_source = df.groupby('source')['player_elo'].mean()
        df['player_elo'] = df.apply(
            lambda row: elo_means_by_source[row['source']] if pd.isna(row['player_elo']) else row['player_elo'],
            axis=1
        )
        
        print(f"📈 Datos cargados: {len(df)} jugadas")
        print(f"👥 Jugadores únicos: {df['player_name'].nunique()}")
        print(f"🎯 Fuentes de datos: {', '.join(df['source'].unique())}")
        
        return df
    
    def analyze_player_weaknesses(self, df, player_name=None):
        """
        Analizar debilidades específicas por jugador
        """
        print(f"🔍 Analizando debilidades{' de ' + player_name if player_name else ' generales'}...")
        
        if player_name:
            player_data = df[df['player_name'] == player_name].copy()
            if len(player_data) == 0:
                print(f"❌ No se encontraron datos para jugador: {player_name}")
                return None
        else:
            # Análisis de una muestra de jugadores
            top_players = df['player_name'].value_counts().head(10).index
            player_data = df[df['player_name'].isin(top_players)].copy()
        
        weaknesses = {}
        
        for player in player_data['player_name'].unique():
            player_moves = player_data[player_data['player_name'] == player]
            
            # Distribución de errores
            error_dist = player_moves['error_label'].value_counts(normalize=True)
            
            # Errores por fase del juego  
            phase_errors = player_moves.groupby(['phase', 'error_label']).size().unstack(fill_value=0)
            
            # Patrones específicos
            blunder_rate = error_dist.get('blunder', 0)
            mistake_rate = error_dist.get('mistake', 0)
            critical_error_rate = blunder_rate + mistake_rate
            
            # Tendencias por ELO
            avg_elo = player_moves['player_elo'].mean()
            
            # Análisis específico por fase
            opening_issues = self._analyze_phase_issues(player_moves, 'opening')
            middlegame_issues = self._analyze_phase_issues(player_moves, 'middlegame')
            endgame_issues = self._analyze_phase_issues(player_moves, 'endgame')
            
            weaknesses[player] = {
                'total_moves': len(player_moves),
                'avg_elo': avg_elo,
                'error_distribution': error_dist.to_dict(),
                'critical_error_rate': critical_error_rate,
                'blunder_rate': blunder_rate,
                'mistake_rate': mistake_rate,
                'phase_analysis': {
                    'opening': opening_issues,
                    'middlegame': middlegame_issues,
                    'endgame': endgame_issues
                },
                'priority_areas': self._identify_priority_areas(error_dist, phase_errors)
            }
        
        print(f"✅ Análisis completado para {len(weaknesses)} jugadores")
        
        return weaknesses
    
    def _analyze_phase_issues(self, player_data, phase):
        """
        Analizar problemas específicos por fase del juego
        """
        phase_data = player_data[player_data['phase'] == phase]
        
        if len(phase_data) == 0:
            return {'total_moves': 0, 'issues': []}
        
        error_dist = phase_data['error_label'].value_counts(normalize=True)
        critical_errors = error_dist.get('blunder', 0) + error_dist.get('mistake', 0)
        
        issues = []
        if critical_errors > 0.2:  # >20% errores críticos
            issues.append(f"Alta tasa de errores críticos ({critical_errors:.1%})")
        
        # Análisis específico por fase
        if phase == 'opening':
            if error_dist.get('inaccuracy', 0) > 0.3:
                issues.append("Principios de apertura débiles")
        elif phase == 'middlegame':
            if error_dist.get('mistake', 0) > 0.15:
                issues.append("Planificación y cálculo deficientes")
        elif phase == 'endgame':
            if error_dist.get('blunder', 0) > 0.1:
                issues.append("Técnica de finales insuficiente")
        
        return {
            'total_moves': len(phase_data),
            'error_distribution': error_dist.to_dict(),
            'critical_error_rate': critical_errors,
            'issues': issues
        }
    
    def _identify_priority_areas(self, error_dist, phase_errors):
        """
        Identificar áreas prioritarias para entrenamiento
        """
        priorities = []
        
        # Prioridad por gravedad de errores
        if error_dist.get('blunder', 0) > 0.05:  # >5% blunders
            priorities.append({
                'area': 'blunder_prevention',
                'priority': 1,
                'description': 'Reducir errores graves',
                'target_reduction': 0.5  # Reducir 50%
            })
        
        if error_dist.get('mistake', 0) > 0.15:  # >15% mistakes
            priorities.append({
                'area': 'tactical_awareness',
                'priority': 2,
                'description': 'Mejorar visión táctica',
                'target_reduction': 0.3
            })
        
        if error_dist.get('inaccuracy', 0) > 0.30:  # >30% inaccuracies
            priorities.append({
                'area': 'positional_understanding',
                'priority': 3,
                'description': 'Desarrollar comprensión posicional',
                'target_reduction': 0.2
            })
        
        return sorted(priorities, key=lambda x: x['priority'])
    
    def generate_personalized_training_plan(self, weaknesses, player_name):
        """
        Generar plan de entrenamiento personalizado
        """
        if player_name not in weaknesses:
            print(f"❌ No hay datos de debilidades para {player_name}")
            return None
        
        print(f"🎯 Generando plan de entrenamiento para {player_name}...")
        
        player_analysis = weaknesses[player_name]
        
        training_plan = {
            'player_name': player_name,
            'generated_date': datetime.now().isoformat(),
            'player_level': self._estimate_player_level(player_analysis['avg_elo']),
            'total_training_hours_week': self._calculate_training_time(player_analysis),
            'priority_areas': player_analysis['priority_areas'],
            'weekly_schedule': self._create_weekly_schedule(player_analysis),
            'specific_exercises': self._recommend_exercises(player_analysis),
            'progress_tracking': self._setup_progress_tracking(player_analysis)
        }
        
        return training_plan
    
    def _estimate_player_level(self, avg_elo):
        """Estimar nivel del jugador basado en ELO"""
        if avg_elo < 1200:
            return 'beginner'
        elif avg_elo < 1600:
            return 'intermediate'
        elif avg_elo < 2000:
            return 'advanced'
        else:
            return 'expert'
    
    def _calculate_training_time(self, player_analysis):
        """Calcular tiempo de entrenamiento recomendado"""
        critical_rate = player_analysis['critical_error_rate']
        
        # Más errores = más tiempo de entrenamiento necesario
        if critical_rate > 0.3:
            return 8  # 8 horas por semana
        elif critical_rate > 0.2:
            return 6
        elif critical_rate > 0.1:
            return 4
        else:
            return 2  # Mantenimiento
    
    def _create_weekly_schedule(self, player_analysis):
        """Crear horario semanal de entrenamiento"""
        total_hours = self._calculate_training_time(player_analysis)
        
        schedule = {
            'monday': {'focus': 'tactical_puzzles', 'duration': 1.0},
            'tuesday': {'focus': 'opening_study', 'duration': 1.0},
            'wednesday': {'focus': 'game_analysis', 'duration': 1.5},
            'thursday': {'focus': 'endgame_practice', 'duration': 1.0},
            'friday': {'focus': 'blunder_check', 'duration': 1.0},
            'saturday': {'focus': 'playing_practice', 'duration': 2.0},
            'sunday': {'focus': 'review_week', 'duration': 0.5}
        }
        
        # Ajustar duración según tiempo total
        factor = total_hours / 8.0
        for day in schedule:
            schedule[day]['duration'] *= factor
            
        return schedule
    
    def _recommend_exercises(self, player_analysis):
        """Recomendar ejercicios específicos"""
        exercises = []
        
        for priority_area in player_analysis['priority_areas']:
            area = priority_area['area']
            
            if area == 'blunder_prevention':
                exercises.extend([
                    {'type': 'blunder_check', 'daily_count': 10, 'description': 'Verificar jugadas antes de mover'},
                    {'type': 'calculation_tree', 'daily_count': 5, 'description': 'Árbol de cálculo sistemático'},
                    {'type': 'critical_moments', 'daily_count': 3, 'description': 'Identificar momentos críticos'}
                ])
            
            elif area == 'tactical_awareness':
                exercises.extend([
                    {'type': 'tactical_puzzles', 'daily_count': 15, 'description': 'Problemas tácticos variados'},
                    {'type': 'pattern_recognition', 'daily_count': 10, 'description': 'Reconocimiento de patrones'},
                    {'type': 'combination_training', 'daily_count': 5, 'description': 'Combinaciones complejas'}
                ])
            
            elif area == 'positional_understanding':
                exercises.extend([
                    {'type': 'positional_puzzles', 'daily_count': 8, 'description': 'Evaluación posicional'},
                    {'type': 'plan_formulation', 'daily_count': 5, 'description': 'Formular planes'},
                    {'type': 'structure_analysis', 'daily_count': 3, 'description': 'Análisis de estructuras'}
                ])
        
        return exercises[:10]  # Limitar a 10 ejercicios principales
    
    def _setup_progress_tracking(self, player_analysis):
        """Configurar seguimiento de progreso"""
        current_rates = player_analysis['error_distribution']
        
        targets = {}
        for error_type, current_rate in current_rates.items():
            if error_type in self.pedagogical_rules:
                # Objetivo: reducir errores según prioridad
                priority = self.pedagogical_rules[error_type]['priority']
                reduction_factor = 0.8 ** priority  # Más reducción para mayor prioridad
                targets[error_type] = current_rate * reduction_factor
        
        return {
            'current_rates': current_rates,
            'target_rates': targets,
            'tracking_period_weeks': 4,
            'evaluation_metrics': ['error_reduction', 'consistency', 'elo_improvement']
        }
    
    def create_player_report(self, weaknesses, training_plan, output_file=None):
        """
        Crear reporte completo del jugador
        """
        player_name = training_plan['player_name']
        print(f"📋 Creando reporte para {player_name}...")
        
        report = {
            'header': {
                'player_name': player_name,
                'report_date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'analysis_period': 'Últimos datos disponibles',
                'total_games_analyzed': weaknesses[player_name]['total_moves']
            },
            'current_analysis': weaknesses[player_name],
            'training_recommendations': training_plan,
            'phase_results_context': self.phase_results
        }
        
        # Generar reporte texto
        report_text = self._format_text_report(report)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"📄 Reporte guardado: {output_file}")
        
        # Generar PDF si está disponible
        if PLOT_AVAILABLE and output_file:
            # Asegurar que el PDF también vaya a reports
            if not output_file.startswith("reports"):
                pdf_filename = os.path.basename(output_file.replace('.txt', '.pdf'))
                pdf_file = os.path.join("reports", pdf_filename)
            else:
                pdf_file = output_file.replace('.txt', '.pdf')
            self._create_pdf_report(report, pdf_file)
        
        return report
    
    def _format_text_report(self, report):
        """Formatear reporte en texto"""
        player_name = report['header']['player_name']
        analysis = report['current_analysis']
        training = report['training_recommendations']
        
        text = f"""
🎯 CHESS TRAINER - REPORTE PERSONALIZADO
========================================

👤 Jugador: {player_name}
📅 Fecha: {report['header']['report_date']}
🎮 Partidas analizadas: {report['header']['total_games_analyzed']}
📊 ELO promedio: {analysis['avg_elo']:.0f}
🎓 Nivel estimado: {training['player_level'].upper()}

📈 ANÁLISIS DE ERRORES
----------------------
• Blunders: {analysis['error_distribution'].get('blunder', 0):.1%}
• Mistakes: {analysis['error_distribution'].get('mistake', 0):.1%}  
• Inaccuracies: {analysis['error_distribution'].get('inaccuracy', 0):.1%}
• Good moves: {analysis['error_distribution'].get('good', 0):.1%}

🚨 Tasa de errores críticos: {analysis['critical_error_rate']:.1%}

🎯 ÁREAS PRIORITARIAS
--------------------
"""
        
        for i, area in enumerate(analysis['priority_areas'], 1):
            text += f"{i}. {area['description']}\n"
            text += f"   Target: Reducir {area['target_reduction']:.0%}\n\n"
        
        text += f"""
📚 PLAN DE ENTRENAMIENTO
-----------------------
⏱️ Tiempo semanal: {training['total_training_hours_week']} horas

📅 HORARIO SEMANAL:
"""
        
        for day, activity in training['weekly_schedule'].items():
            text += f"• {day.title()}: {activity['focus']} ({activity['duration']:.1f}h)\n"
        
        text += f"""
🎯 EJERCICIOS RECOMENDADOS:
"""
        
        for exercise in training['specific_exercises'][:5]:
            text += f"• {exercise['description']}: {exercise['daily_count']} por día\n"
        
        text += f"""

📊 SEGUIMIENTO DE PROGRESO
--------------------------
Periodo de evaluación: {training['progress_tracking']['tracking_period_weeks']} semanas

Objetivos de reducción:
"""
        
        for error_type, target_rate in training['progress_tracking']['target_rates'].items():
            current_rate = training['progress_tracking']['current_rates'][error_type]
            text += f"• {error_type}: {current_rate:.1%} → {target_rate:.1%}\n"
        
        text += f"""

🔬 CONTEXTO TÉCNICO
------------------
Sistema basado en análisis de {self.phase_results['phase1_rf_f1']:.3f} F1-score
Embeddings con coherencia {self.phase_results['phase4_coherence']:.3f}

Generado por Chess Trainer Phase 5 - Adaptive Tutor
"""
        
        return text
    
    def _create_pdf_report(self, report, pdf_file):
        """Crear reporte PDF con gráficos"""
        try:
            with PdfPages(pdf_file) as pdf:
                # Página 1: Análisis de errores
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(11, 8))
                
                analysis = report['current_analysis']
                
                # Gráfico 1: Distribución de errores
                error_dist = analysis['error_distribution']
                ax1.pie(error_dist.values(), labels=error_dist.keys(), autopct='%1.1f%%')
                ax1.set_title('Distribución de Errores')
                
                # Gráfico 2: Errores por fase
                phases = ['opening', 'middlegame', 'endgame']
                error_rates = [analysis['phase_analysis'][phase]['critical_error_rate'] for phase in phases]
                ax2.bar(phases, error_rates)
                ax2.set_title('Tasa de Errores Críticos por Fase')
                ax2.set_ylabel('Tasa de Error')
                
                # Gráfico 3: Progreso objetivo
                current = list(analysis['error_distribution'].values())
                target = list(report['training_recommendations']['progress_tracking']['target_rates'].values())
                x = range(len(current))
                ax3.bar([i-0.2 for i in x], current, 0.4, label='Actual')
                ax3.bar([i+0.2 for i in x], target, 0.4, label='Objetivo')
                ax3.set_title('Progreso Esperado')
                ax3.legend()
                
                # Gráfico 4: Plan de entrenamiento
                schedule = report['training_recommendations']['weekly_schedule']
                days = list(schedule.keys())
                hours = [schedule[day]['duration'] for day in days]
                ax4.bar(days, hours)
                ax4.set_title('Distribución Semanal de Entrenamiento')
                ax4.set_ylabel('Horas')
                ax4.tick_params(axis='x', rotation=45)
                
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
            
            print(f"📊 Reporte PDF creado: {pdf_file}")
            
        except Exception as e:
            print(f"⚠️ Error creando PDF: {e}")
    
    def run_phase5(self, sample_players=5):
        """
        Ejecutar Phase 5 completo: análisis y reportes personalizados
        """
        print("🚀 Iniciando Phase 5 - Adaptive Tutor & Reports")
        
        # 1. Cargar datos de jugadores
        df = self.load_player_data_from_db()
        
        # 2. Analizar debilidades
        weaknesses = self.analyze_player_weaknesses(df)
        
        # 3. Generar planes de entrenamiento para jugadores muestra
        top_players = list(weaknesses.keys())[:sample_players]
        training_plans = {}
        reports = {}
        
        for player_name in top_players:
            print(f"\n🎯 Procesando jugador: {player_name}")
            
            # Generar plan personalizado
            training_plan = self.generate_personalized_training_plan(weaknesses, player_name)
            training_plans[player_name] = training_plan
            
            # Crear reporte
            import os
            reports_dir = "reports"
            os.makedirs(reports_dir, exist_ok=True)
            report_file = f"report_{player_name.replace(' ', '_')}.txt"
            report_filepath = os.path.join(reports_dir, report_file)
            report = self.create_player_report(weaknesses, training_plan, report_filepath)
            reports[player_name] = report
        
        # 4. Resumen general
        self.summarize_phase5_results(weaknesses, training_plans)
        
        return {
            'weaknesses_analysis': weaknesses,
            'training_plans': training_plans,
            'reports': reports
        }
    
    def summarize_phase5_results(self, weaknesses, training_plans):
        """
        Resumir resultados de Phase 5
        """
        print("\n🏆 RESUMEN PHASE 5 - ADAPTIVE TUTOR")
        print("=" * 45)
        
        total_players = len(weaknesses)
        total_plans = len(training_plans)
        
        # Estadísticas generales
        avg_critical_error_rate = np.mean([w['critical_error_rate'] for w in weaknesses.values()])
        avg_training_hours = np.mean([p['total_training_hours_week'] for p in training_plans.values()])
        
        # Distribución de niveles
        levels = [p['player_level'] for p in training_plans.values()]
        level_counts = Counter(levels)
        
        print(f"👥 Jugadores analizados: {total_players}")
        print(f"📋 Planes generados: {total_plans}")
        print(f"⚠️ Tasa promedio de errores críticos: {avg_critical_error_rate:.1%}")
        print(f"⏱️ Tiempo promedio de entrenamiento: {avg_training_hours:.1f}h/semana")
        
        print(f"\n📊 Distribución por nivel:")
        for level, count in level_counts.items():
            print(f"   {level.title()}: {count} jugadores")
        
        # Evaluación del sistema
        if avg_critical_error_rate > 0.25:
            print("\n📈 OPORTUNIDAD ALTA: Muchos jugadores con errores críticos")
            print("✅ Sistema de tutor adaptativo será muy útil")
        elif avg_critical_error_rate > 0.15:
            print("\n📈 OPORTUNIDAD MEDIA: Espacio para mejora significativa")
            print("✅ Recomendaciones personalizadas tienen potencial")
        else:
            print("\n📈 OPORTUNIDAD LIMITADA: Jugadores ya bastante competentes")
            print("⚠️ Enfoque en mantenimiento y refinamiento")
        
        print(f"\n🔍 Capacidades desarrolladas:")
        print("  ✅ Análisis personalizado de debilidades")
        print("  ✅ Planes de entrenamiento adaptativos")
        print("  ✅ Reportes detallados por jugador")
        print("  ✅ Seguimiento de progreso estructurado")
        print("  ✅ Base para intervención de entrenadores (Phase 6)")

if __name__ == "__main__":
    tutor = Phase5AdaptiveTutor()
    results = tutor.run_phase5(sample_players=3)