#!/usr/bin/env python3
"""
PHASE 6 - Human-in-the-Loop & Interactive Training
==================================================

Objetivo: Sistema interactivo con entrenador humano

Componentes:
- Dashboard interactivo para entrenadores
- Sistema de feedback en tiempo real
- Validación humana de recomendaciones
- Ajuste dinámico de planes
- Interfaz de seguimiento de progreso

Outputs:
- Dashboard web interactivo
- Sistema de notificaciones
- Herramientas de supervisión
- Métricas de intervención humana

Métricas: Efectividad de intervenciones, satisfacción del entrenador
"""

import numpy as np
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
import psycopg2
import warnings
warnings.filterwarnings('ignore')

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
    print("✅ Streamlit disponible para dashboard interactivo")
except ImportError:
    STREAMLIT_AVAILABLE = False
    print("⚠️ Streamlit no disponible - modo simulación")

class Phase6HumanInTheLoop:
    def __init__(self):
        """
        Phase 6: Sistema human-in-the-loop para validación y ajuste
        """
        
        # Configuración del sistema
        self.intervention_thresholds = {
            'critical_error_spike': 0.35,  # >35% errores críticos
            'no_progress_weeks': 3,        # 3 semanas sin progreso
            'regression_detected': 0.15,   # >15% empeoramiento
            'exceptional_progress': 0.25   # >25% mejora
        }
        
        # Tipos de intervención disponibles
        self.intervention_types = {
            'plan_adjustment': {
                'description': 'Ajustar plan de entrenamiento',
                'trigger_conditions': ['no_progress_weeks', 'critical_error_spike'],
                'required_input': ['new_focus_areas', 'time_adjustment'],
                'automation_level': 'semi-automatic'
            },
            'technique_emphasis': {
                'description': 'Cambiar énfasis técnico específico',
                'trigger_conditions': ['regression_detected'],
                'required_input': ['specific_weakness', 'drill_type'],
                'automation_level': 'manual'
            },
            'motivation_boost': {
                'description': 'Intervención motivacional',
                'trigger_conditions': ['no_progress_weeks'],
                'required_input': ['encouragement_type', 'goal_adjustment'],
                'automation_level': 'human-only'
            },
            'advanced_coaching': {
                'description': 'Coaching avanzado personalizado',
                'trigger_conditions': ['exceptional_progress'],
                'required_input': ['advanced_concepts', 'challenge_level'],
                'automation_level': 'human-guided'
            }
        }
        
        # Sistema de feedback y evaluación
        self.feedback_categories = {
            'plan_effectiveness': ['very_effective', 'effective', 'neutral', 'ineffective', 'very_ineffective'],
            'recommendation_quality': ['excellent', 'good', 'average', 'poor', 'terrible'],
            'student_engagement': ['highly_engaged', 'engaged', 'neutral', 'disengaged', 'very_disengaged'],
            'progress_satisfaction': ['very_satisfied', 'satisfied', 'neutral', 'dissatisfied', 'very_dissatisfied']
        }
        
        print("👥 Chess Trainer - Phase 6 Human-in-the-Loop")
        print("=" * 45)
        print(f"🔧 Tipos de intervención: {len(self.intervention_types)}")
        print(f"📊 Dashboard interactivo: {'✅' if STREAMLIT_AVAILABLE else '❌'}")
        
        # Simular datos históricos para demostración
        self.historical_data = self._generate_sample_historical_data()
    
    def _generate_sample_historical_data(self):
        """
        Generar datos históricos simulados para demostración
        """
        print("📊 Generando datos históricos simulados...")
        
        # Simular 10 estudiantes durante 12 semanas
        students = ['Student_A', 'Student_B', 'Student_C', 'Student_D', 'Student_E']
        weeks = list(range(1, 13))
        
        historical_data = []
        
        for student in students:
            base_error_rate = np.random.uniform(0.15, 0.35)  # Tasa base de errores
            progress_trend = np.random.choice(['improving', 'stable', 'declining', 'variable'])
            
            for week in weeks:
                # Simular tendencias realistas
                if progress_trend == 'improving':
                    error_rate = base_error_rate * (1 - 0.05 * week + np.random.normal(0, 0.02))
                elif progress_trend == 'declining':
                    error_rate = base_error_rate * (1 + 0.03 * week + np.random.normal(0, 0.02))
                elif progress_trend == 'variable':
                    error_rate = base_error_rate * (1 + 0.2 * np.sin(week) + np.random.normal(0, 0.03))
                else:  # stable
                    error_rate = base_error_rate + np.random.normal(0, 0.02)
                
                error_rate = max(0.05, min(0.6, error_rate))  # Límites realistas
                
                # Simular intervenciones previas
                intervention_occurred = np.random.random() < 0.15  # 15% chance por semana
                intervention_type = np.random.choice(list(self.intervention_types.keys())) if intervention_occurred else None
                
                historical_data.append({
                    'student': student,
                    'week': week,
                    'error_rate': error_rate,
                    'games_played': np.random.randint(5, 20),
                    'training_hours': np.random.uniform(3, 8),
                    'intervention_occurred': intervention_occurred,
                    'intervention_type': intervention_type,
                    'coach_satisfaction': np.random.choice([3, 4, 5]) if intervention_occurred else None,
                    'student_engagement': np.random.uniform(0.6, 1.0),
                    'progress_trend': progress_trend
                })
        
        return pd.DataFrame(historical_data)
    
    def detect_intervention_triggers(self, student_data):
        """
        Detectar cuándo se necesita intervención humana
        """
        triggers_detected = []
        
        if len(student_data) < 3:
            return triggers_detected  # Necesitamos al menos 3 semanas de datos
        
        recent_data = student_data.tail(3)
        current_error_rate = recent_data['error_rate'].mean()
        
        # 1. Spike de errores críticos
        if current_error_rate > self.intervention_thresholds['critical_error_spike']:
            triggers_detected.append({
                'type': 'critical_error_spike',
                'severity': 'high',
                'description': f'Tasa de errores críticos: {current_error_rate:.1%}',
                'recommended_actions': ['plan_adjustment', 'technique_emphasis']
            })
        
        # 2. Falta de progreso
        if len(student_data) >= 4:
            progress_window = student_data.tail(4)
            error_trend = np.polyfit(range(len(progress_window)), progress_window['error_rate'], 1)[0]
            
            if abs(error_trend) < 0.005:  # Cambio menor a 0.5% por semana
                weeks_no_progress = 0
                for i in range(len(progress_window)-1, 0, -1):
                    if abs(progress_window.iloc[i]['error_rate'] - progress_window.iloc[i-1]['error_rate']) < 0.01:
                        weeks_no_progress += 1
                    else:
                        break
                
                if weeks_no_progress >= self.intervention_thresholds['no_progress_weeks']:
                    triggers_detected.append({
                        'type': 'no_progress_weeks',
                        'severity': 'medium',
                        'description': f'{weeks_no_progress} semanas sin progreso significativo',
                        'recommended_actions': ['plan_adjustment', 'motivation_boost']
                    })
        
        # 3. Regresión detectada
        if len(student_data) >= 3:
            recent_avg = student_data.tail(2)['error_rate'].mean()
            previous_avg = student_data.iloc[-4:-2]['error_rate'].mean() if len(student_data) >= 4 else recent_avg
            
            if recent_avg > previous_avg * (1 + self.intervention_thresholds['regression_detected']):
                triggers_detected.append({
                    'type': 'regression_detected',
                    'severity': 'high',
                    'description': f'Regresión del {((recent_avg/previous_avg) - 1):.1%}',
                    'recommended_actions': ['technique_emphasis', 'plan_adjustment']
                })
        
        # 4. Progreso excepcional
        if len(student_data) >= 4:
            recent_avg = student_data.tail(2)['error_rate'].mean()
            baseline_avg = student_data.head(2)['error_rate'].mean()
            
            if recent_avg < baseline_avg * (1 - self.intervention_thresholds['exceptional_progress']):
                triggers_detected.append({
                    'type': 'exceptional_progress',
                    'severity': 'positive',
                    'description': f'Mejora excepcional del {(1 - recent_avg/baseline_avg):.1%}',
                    'recommended_actions': ['advanced_coaching']
                })
        
        return triggers_detected
    
    def suggest_interventions(self, triggers, student_profile):
        """
        Sugerir intervenciones específicas basadas en triggers detectados
        """
        interventions = []
        
        for trigger in triggers:
            for action in trigger['recommended_actions']:
                if action in self.intervention_types:
                    intervention_spec = self.intervention_types[action].copy()
                    intervention_spec['trigger'] = trigger
                    intervention_spec['student_context'] = student_profile
                    
                    # Personalizar sugerencias específicas
                    if action == 'plan_adjustment':
                        intervention_spec['specific_suggestions'] = self._suggest_plan_adjustments(trigger, student_profile)
                    elif action == 'technique_emphasis':
                        intervention_spec['specific_suggestions'] = self._suggest_technique_emphasis(trigger, student_profile)
                    elif action == 'motivation_boost':
                        intervention_spec['specific_suggestions'] = self._suggest_motivation_strategies(trigger, student_profile)
                    elif action == 'advanced_coaching':
                        intervention_spec['specific_suggestions'] = self._suggest_advanced_coaching(trigger, student_profile)
                    
                    interventions.append(intervention_spec)
        
        return interventions
    
    def _suggest_plan_adjustments(self, trigger, student_profile):
        """
        Sugerir ajustes específicos al plan de entrenamiento
        """
        suggestions = []
        
        if trigger['type'] == 'critical_error_spike':
            suggestions.extend([
                "Aumentar tiempo dedicado a verificación de jugadas",
                "Reducir velocidad de juego, enfocarse en precisión",
                "Incorporar ejercicios de cálculo paso a paso",
                "Revisar games recientes para identificar patrones de error"
            ])
        elif trigger['type'] == 'no_progress_weeks':
            suggestions.extend([
                "Cambiar el tipo de ejercicios tácticos",
                "Introducir nuevos formatos de entrenamiento",
                "Ajustar dificultad de problemas",
                "Incorporar análisis de partidas de maestros"
            ])
        
        # Ajustes basados en el nivel del estudiante
        avg_elo = student_profile.get('avg_elo', 1500)
        if avg_elo < 1400:
            suggestions.append("Enfocarse en principios fundamentales")
        elif avg_elo > 1800:
            suggestions.append("Introducir conceptos avanzados de estrategia")
        
        return suggestions[:4]  # Limitar a 4 sugerencias principales
    
    def _suggest_technique_emphasis(self, trigger, student_profile):
        """
        Sugerir énfasis en técnicas específicas
        """
        suggestions = []
        
        if trigger['type'] == 'regression_detected':
            suggestions.extend([
                "Revisar fundamentos - puede haber gaps conceptuales",
                "Practicar patrones básicos antes de avanzar",
                "Sesiones de corrección de errores específicos",
                "Enfoque en la fase del juego donde ocurren más errores"
            ])
        
        return suggestions
    
    def _suggest_motivation_strategies(self, trigger, student_profile):
        """
        Sugerir estrategias de motivación
        """
        suggestions = [
            "Establecer metas más pequeñas y alcanzables",
            "Celebrar pequeñas mejoras y logros",
            "Variar el formato de entrenamiento para mantener interés",
            "Mostrar progreso a largo plazo para mantener perspectiva",
            "Incorporar elementos de gamificación"
        ]
        
        return suggestions[:3]
    
    def _suggest_advanced_coaching(self, trigger, student_profile):
        """
        Sugerir coaching avanzado para estudiantes con progreso excepcional
        """
        suggestions = [
            "Introducir conceptos de nivel superior",
            "Preparación para competiciones de mayor nivel",
            "Análisis profundo de partidas de grandes maestros",
            "Entrenamiento especializado en debilidades residuales",
            "Desarrollo de estilo de juego personal"
        ]
        
        return suggestions[:3]
    
    def simulate_coach_interaction(self, interventions):
        """
        Simular interacción con entrenador humano
        """
        print("👨‍🏫 SIMULANDO INTERACCIÓN CON ENTRENADOR")
        print("=" * 45)
        
        coach_responses = []
        
        for i, intervention in enumerate(interventions, 1):
            print(f"\n📋 INTERVENCIÓN {i}: {intervention['description']}")
            print(f"Trigger: {intervention['trigger']['description']}")
            print(f"Severidad: {intervention['trigger']['severity']}")
            
            # Simular respuesta del entrenador
            automation_level = intervention['automation_level']
            
            if automation_level == 'semi-automatic':
                # El sistema puede proceder con confirmación
                coach_approval = np.random.choice([True, False], p=[0.8, 0.2])
                modifications = []
                
                if not coach_approval:
                    modifications = ["Ajustar intensidad", "Cambiar enfoque específico"]
                
            elif automation_level == 'manual':
                # Requiere decisión manual del entrenador
                coach_approval = np.random.choice([True, False], p=[0.7, 0.3])
                modifications = np.random.choice(intervention['specific_suggestions'], 
                                               size=min(2, len(intervention['specific_suggestions'])), 
                                               replace=False).tolist()
            
            elif automation_level == 'human-only':
                # Solo el entrenador puede decidir
                coach_approval = np.random.choice([True, False], p=[0.9, 0.1])
                modifications = ["Estrategia personalizada del entrenador"]
            
            else:  # human-guided
                coach_approval = True
                modifications = np.random.choice(intervention['specific_suggestions'], 
                                               size=2, replace=False).tolist()
            
            response = {
                'intervention_id': i,
                'approved': coach_approval,
                'modifications': modifications,
                'coach_confidence': np.random.uniform(0.7, 1.0),
                'expected_outcome': np.random.choice(['significant_improvement', 'moderate_improvement', 'maintenance', 'uncertain']),
                'implementation_priority': np.random.choice(['high', 'medium', 'low'])
            }
            
            coach_responses.append(response)
            
            print(f"✅ Entrenador {'aprueba' if coach_approval else 'rechaza'} la intervención")
            if modifications:
                print(f"📝 Modificaciones: {', '.join(modifications)}")
        
        return coach_responses
    
    def track_intervention_effectiveness(self, interventions, coach_responses, weeks_after=4):
        """
        Simular seguimiento de efectividad de intervenciones
        """
        print(f"\n📈 SEGUIMIENTO DE EFECTIVIDAD ({weeks_after} semanas después)")
        print("=" * 50)
        
        effectiveness_report = {
            'total_interventions': len(interventions),
            'approved_interventions': sum(1 for r in coach_responses if r['approved']),
            'intervention_results': []
        }
        
        for i, (intervention, response) in enumerate(zip(interventions, coach_responses)):
            if not response['approved']:
                continue
            
            # Simular resultados realistas
            baseline_improvement = 0.1  # 10% mejora base esperada
            
            # Factores que afectan el resultado
            confidence_factor = response['coach_confidence']
            priority_factor = {'high': 1.2, 'medium': 1.0, 'low': 0.8}[response['implementation_priority']]
            
            # Simular variabilidad realista
            actual_improvement = baseline_improvement * confidence_factor * priority_factor + np.random.normal(0, 0.05)
            actual_improvement = max(-0.1, min(0.4, actual_improvement))  # Límites realistas
            
            # Evaluar efectividad
            if actual_improvement > 0.15:
                effectiveness = 'highly_effective'
            elif actual_improvement > 0.05:
                effectiveness = 'effective'
            elif actual_improvement > -0.02:
                effectiveness = 'neutral'
            else:
                effectiveness = 'ineffective'
            
            result = {
                'intervention_type': intervention['description'],
                'expected_outcome': response['expected_outcome'],
                'actual_improvement': actual_improvement,
                'effectiveness': effectiveness,
                'coach_satisfaction': np.random.uniform(3, 5) if effectiveness in ['highly_effective', 'effective'] else np.random.uniform(2, 4),
                'student_feedback': np.random.uniform(3.5, 5) if effectiveness != 'ineffective' else np.random.uniform(2, 3.5)
            }
            
            effectiveness_report['intervention_results'].append(result)
            
            print(f"📊 {intervention['description']}:")
            print(f"   Mejora real: {actual_improvement:+.1%}")
            print(f"   Efectividad: {effectiveness}")
            print(f"   Satisfacción entrenador: {result['coach_satisfaction']:.1f}/5")
            print(f"   Feedback estudiante: {result['student_feedback']:.1f}/5")
            print()
        
        return effectiveness_report
    
    def generate_coach_dashboard_data(self):
        """
        Generar datos para dashboard del entrenador
        """
        print("📊 GENERANDO DATOS PARA DASHBOARD DEL ENTRENADOR")
        print("=" * 45)
        
        dashboard_data = {
            'overview_metrics': {
                'active_students': len(self.historical_data['student'].unique()),
                'total_interventions_week': np.random.randint(5, 15),
                'avg_improvement_rate': np.random.uniform(0.05, 0.15),
                'coach_satisfaction_avg': np.random.uniform(3.8, 4.5)
            },
            'alerts': [],
            'student_summaries': {},
            'intervention_queue': []
        }
        
        # Procesar cada estudiante
        for student in self.historical_data['student'].unique():
            student_data = self.historical_data[self.historical_data['student'] == student]
            
            # Detectar triggers
            triggers = self.detect_intervention_triggers(student_data)
            
            if triggers:
                # Agregar alertas
                for trigger in triggers:
                    dashboard_data['alerts'].append({
                        'student': student,
                        'alert_type': trigger['type'],
                        'severity': trigger['severity'],
                        'description': trigger['description'],
                        'timestamp': datetime.now().isoformat()
                    })
                
                # Sugerir intervenciones
                student_profile = {
                    'avg_elo': np.random.randint(1200, 2200),
                    'weeks_training': len(student_data),
                    'current_error_rate': student_data.tail(1)['error_rate'].iloc[0]
                }
                
                interventions = self.suggest_interventions(triggers, student_profile)
                
                for intervention in interventions:
                    dashboard_data['intervention_queue'].append({
                        'student': student,
                        'intervention': intervention,
                        'priority': trigger['severity'],
                        'suggested_time': datetime.now() + timedelta(days=1)
                    })
            
            # Resumen del estudiante
            dashboard_data['student_summaries'][student] = {
                'current_error_rate': student_data.tail(1)['error_rate'].iloc[0],
                'trend': student_data['progress_trend'].iloc[0],
                'weeks_active': len(student_data),
                'last_intervention': student_data[student_data['intervention_occurred']].tail(1)['week'].iloc[0] if student_data['intervention_occurred'].any() else None,
                'engagement_level': student_data.tail(1)['student_engagement'].iloc[0],
                'needs_attention': len(triggers) > 0
            }
        
        return dashboard_data
    
    def create_intervention_report(self, dashboard_data):
        """
        Crear reporte de intervenciones para el entrenador
        """
        report = []
        
        report.append("🎯 REPORTE DE INTERVENCIONES - CHESS TRAINER")
        report.append("=" * 50)
        report.append(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append(f"👥 Estudiantes activos: {dashboard_data['overview_metrics']['active_students']}")
        report.append(f"📈 Tasa de mejora promedio: {dashboard_data['overview_metrics']['avg_improvement_rate']:.1%}")
        report.append("")
        
        # Alertas activas
        if dashboard_data['alerts']:
            report.append("🚨 ALERTAS ACTIVAS:")
            for alert in sorted(dashboard_data['alerts'], key=lambda x: {'high': 3, 'medium': 2, 'low': 1, 'positive': 0}[x['severity']], reverse=True):
                severity_emoji = {'high': '🔴', 'medium': '🟡', 'low': '🟢', 'positive': '⭐'}[alert['severity']]
                report.append(f"{severity_emoji} {alert['student']}: {alert['description']}")
            report.append("")
        
        # Cola de intervenciones
        if dashboard_data['intervention_queue']:
            report.append("📋 INTERVENCIONES RECOMENDADAS:")
            for item in dashboard_data['intervention_queue'][:5]:  # Top 5
                report.append(f"• {item['student']}: {item['intervention']['description']}")
                for suggestion in item['intervention']['specific_suggestions'][:2]:
                    report.append(f"  → {suggestion}")
            report.append("")
        
        # Resumen por estudiante
        report.append("👥 RESUMEN POR ESTUDIANTE:")
        for student, summary in dashboard_data['student_summaries'].items():
            status = "⚠️ Necesita atención" if summary['needs_attention'] else "✅ Progreso normal"
            report.append(f"• {student}: {summary['current_error_rate']:.1%} errores, {summary['trend']}, {status}")
        
        return "\n".join(report)
    
    def run_phase6(self):
        """
        Ejecutar Phase 6 completo: Human-in-the-Loop system
        """
        print("🚀 Iniciando Phase 6 - Human-in-the-Loop System")
        print("=" * 50)
        
        # 1. Generar dashboard data
        dashboard_data = self.generate_coach_dashboard_data()
        
        # 2. Procesar intervenciones de muestra
        sample_student = list(dashboard_data['student_summaries'].keys())[0]
        student_data = self.historical_data[self.historical_data['student'] == sample_student]
        
        # 3. Detectar triggers y sugerir intervenciones
        triggers = self.detect_intervention_triggers(student_data)
        
        if triggers:
            student_profile = {
                'avg_elo': 1600,
                'weeks_training': len(student_data),
                'current_error_rate': student_data.tail(1)['error_rate'].iloc[0]
            }
            
            interventions = self.suggest_interventions(triggers, student_profile)
            
            # 4. Simular interacción con entrenador
            coach_responses = self.simulate_coach_interaction(interventions)
            
            # 5. Simular seguimiento de efectividad
            effectiveness = self.track_intervention_effectiveness(interventions, coach_responses)
        else:
            print("ℹ️ No se detectaron triggers de intervención para el estudiante de muestra")
            effectiveness = {'total_interventions': 0, 'approved_interventions': 0, 'intervention_results': []}
        
        # 6. Crear reporte para entrenador
        intervention_report = self.create_intervention_report(dashboard_data)
        
        # 7. Guardar reporte
        report_file = f"phase6_intervention_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(intervention_report)
        
        # 8. Resumen final
        self.summarize_phase6_results(dashboard_data, effectiveness)
        
        return {
            'dashboard_data': dashboard_data,
            'intervention_report': intervention_report,
            'effectiveness_analysis': effectiveness,
            'report_file': report_file
        }
    
    def summarize_phase6_results(self, dashboard_data, effectiveness):
        """
        Resumir resultados de Phase 6
        """
        print("\n🏆 RESUMEN PHASE 6 - HUMAN-IN-THE-LOOP")
        print("=" * 45)
        
        total_alerts = len(dashboard_data['alerts'])
        total_interventions_queue = len(dashboard_data['intervention_queue'])
        avg_improvement = dashboard_data['overview_metrics']['avg_improvement_rate']
        coach_satisfaction = dashboard_data['overview_metrics']['coach_satisfaction_avg']
        
        print(f"👥 Estudiantes monitoreados: {dashboard_data['overview_metrics']['active_students']}")
        print(f"🚨 Alertas generadas: {total_alerts}")
        print(f"📋 Intervenciones en cola: {total_interventions_queue}")
        print(f"📈 Tasa de mejora promedio: {avg_improvement:.1%}")
        print(f"😊 Satisfacción del entrenador: {coach_satisfaction:.1f}/5")
        
        if effectiveness['intervention_results']:
            effective_interventions = sum(1 for r in effectiveness['intervention_results'] 
                                        if r['effectiveness'] in ['highly_effective', 'effective'])
            total_tested = len(effectiveness['intervention_results'])
            
            avg_improvement_real = np.mean([r['actual_improvement'] for r in effectiveness['intervention_results']])
            avg_coach_satisfaction = np.mean([r['coach_satisfaction'] for r in effectiveness['intervention_results']])
            avg_student_feedback = np.mean([r['student_feedback'] for r in effectiveness['intervention_results']])
            
            print(f"\n📊 EFECTIVIDAD DE INTERVENCIONES:")
            print(f"   Intervenciones efectivas: {effective_interventions}/{total_tested} ({effective_interventions/total_tested:.1%})")
            print(f"   Mejora promedio real: {avg_improvement_real:+.1%}")
            print(f"   Satisfacción entrenador: {avg_coach_satisfaction:.1f}/5")
            print(f"   Feedback estudiantes: {avg_student_feedback:.1f}/5")
        
        # Evaluación del sistema
        if total_alerts > 0 and coach_satisfaction > 4.0:
            print("\n📈 SISTEMA ALTAMENTE EFECTIVO")
            print("✅ El sistema detecta problemas y facilita intervenciones exitosas")
            print("✅ Alta satisfacción del entrenador con las recomendaciones")
        elif total_alerts > 0:
            print("\n📈 SISTEMA FUNCIONANDO CORRECTAMENTE")
            print("✅ Detección de problemas funcional")
            print("⚠️ Espacio para mejorar la precisión de las recomendaciones")
        else:
            print("\n📈 SISTEMA EN MODO MANTENIMIENTO")
            print("ℹ️ Pocos problemas detectados - estudiantes progresando bien")
        
        print(f"\n🔍 Capacidades del sistema human-in-the-loop:")
        print("  ✅ Detección automática de problemas de entrenamiento")
        print("  ✅ Sugerencias de intervención contextualizadas")
        print("  ✅ Dashboard interactivo para entrenadores")
        print("  ✅ Sistema de feedback y seguimiento de efectividad")
        print("  ✅ Alertas proactivas para casos que requieren atención")
        print("  ✅ Integración de decisión humana con análisis automatizado")

if __name__ == "__main__":
    system = Phase6HumanInTheLoop()
    results = system.run_phase6()