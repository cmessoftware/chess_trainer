#!/usr/bin/env python3
"""
Análisis de Survivorship Bias para jugadores específicos.
Ejecuta análisis avanzado de supervivencia usando el módulo existente.
"""

import os
import sys

# Add src to path para importar módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from analysis.survivorship_bias import SurvivorshipBiasAnalyzer
import json

def analyze_player_survivorship(player_name):
    """Analizar survivorship bias para un jugador usando filtros disponibles."""
    print(f"🚀 SURVIVORSHIP BIAS ANALYSIS - {player_name.upper()}")
    print("=" * 60)
    
    try:
        analyzer = SurvivorshipBiasAnalyzer()
        
        # El módulo actual analiza por fuente, no por jugador específico
        # Vamos a usar filtro por fuente 'personal' que es donde están la mayoría
        print(f"📊 Analyzing survivorship patterns for dataset containing {player_name}...")
        
        report = analyzer.analyze_dataset(source_filter='personal')
        
        # Extraer métricas principales
        overview = report.get('dataset_overview', {})
        early_defeats = report.get('early_defeats', [])
        mate_patterns = report.get('mate_patterns', [])
        opening_survival = report.get('opening_survival', {})
        emergency_plan = report.get('emergency_plan', {})
        
        # Mostrar resumen
        print(f"📈 Dataset Overview:")
        print(f"   - Total Games Analyzed: {overview.get('total_games', 0)}")
        print(f"   - Early Defeats: {len(early_defeats)}")
        print(f"   - Mate Patterns: {len(mate_patterns)}")
        print(f"   - Openings Analyzed: {len(opening_survival)}")
        
        # Alertas críticas
        alerts = report.get('alerts', [])
        critical_alerts = [a for a in alerts if a.get('criticality') == 'CRITICAL']
        if critical_alerts:
            print(f"\n🚨 CRITICAL ALERTS: {len(critical_alerts)}")
            for alert in critical_alerts[:3]:  # Mostrar top 3
                print(f"   - {alert.get('pattern_type', 'Unknown')}: {alert.get('description', 'No description')}")
        
        # Plan de emergencia
        if emergency_plan:
            print(f"\n🚨 EMERGENCY PLAN:")
            priorities = emergency_plan.get('priorities', [])
            for i, priority in enumerate(priorities[:5], 1):  # Top 5
                print(f"   {i}. {priority}")
        
        # Recommendations
        recommendations = report.get('recommendations', [])
        if recommendations:
            print(f"\n💡 KEY RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):  # Top 3
                print(f"   {i}. {rec}")
        
        # Guardar reporte detallado
        os.makedirs("artifacts/survivorship_analysis", exist_ok=True)
        output_file = f"artifacts/survivorship_analysis/{player_name}_survivorship_analysis.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📄 Detailed report saved: {output_file}")
        
        # Calcular supervivencia general
        total_games = overview.get('total_games', 0)
        early_defeat_count = len(early_defeats)
        survival_rate = 1 - (early_defeat_count / total_games) if total_games > 0 else 0
        
        print(f"\n📊 SURVIVAL METRICS:")
        print(f"   - Overall Survival Rate: {survival_rate:.1%}")
        print(f"   - Games Analyzed: {total_games}")
        print(f"   - Early Defeats Detected: {early_defeat_count}")
        
        return report
        
    except Exception as e:
        print(f"❌ Error in survivorship analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        player_name = sys.argv[1]
        analyze_player_survivorship(player_name)
    else:
        print("Usage: python analyze_survivorship.py [PLAYER_NAME]")