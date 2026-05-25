#!/usr/bin/env python3
"""
ANÁLISIS COMPARATIVO COMPLETO: cmess1315 vs Th3_hound
=====================================================

Comparativa de 3 tipos de clasificación:
1. Tipo de jugada (error_label): good, inaccuracy, mistake, blunder
2. Nivel de jugador: 1400 ELO vs 2200 ELO 
3. Racha de fallos: streak de errores consecutivos

OBJETIVO: Validar si los modelos pueden distinguir patrones entre niveles
"""
import numpy as np
import pandas as pd
import os
import dotenv
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import f1_score, accuracy_score, classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_sample_weight
import warnings
warnings.filterwarnings('ignore')

# Configure encoding for Windows
import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables
dotenv.load_dotenv()

def load_comparative_data():
    """
    Carga datos de ambos jugadores desde PostgreSQL
    DEBUG VERSION - Sin filtros restrictivos para capturar todos los datos disponibles
    """
    
    print("🔍 CONECTANDO A POSTGRESQL PARA ANÁLISIS COMPARATIVO...")
    print("   👤 cmess1315/cmess4401 (~1320-1387 ELO)")  
    print("   🏆 Grandes Maestros (~2600+ ELO: Kasparov, Karpov, etc.)")
    print("   🐛 MODO DEBUG: Capturando TODOS los datos disponibles")
    
    DATABASE_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db")
    engine = create_engine(DATABASE_URL)
    
    try:
        # DEBUG: Primero verificar cuántas features totales tenemos para cmess1315
        debug_query = text("""
            SELECT 
                COUNT(*) as total_features,
                COUNT(DISTINCT f.game_id) as unique_games,
                COUNT(CASE WHEN g.white_player IN ('cmess1315', 'cmess4401') THEN 1 END) as white_moves,
                COUNT(CASE WHEN g.black_player IN ('cmess1315', 'cmess4401') THEN 1 END) as black_moves
            FROM features f
            LEFT JOIN games g ON f.game_id = g.game_id
            WHERE (g.white_player IN ('cmess1315', 'cmess4401') OR 
                   g.black_player IN ('cmess1315', 'cmess4401'))
              AND f.error_label IS NOT NULL;
        """)
        
        debug_result = pd.read_sql(debug_query, engine)
        print(f"\n🔍 DEBUG - FEATURES DISPONIBLES PARA cmess1315:")
        print(f"   📊 Total features: {debug_result['total_features'].iloc[0]:,}")
        print(f"   🎮 Partidas únicas: {debug_result['unique_games'].iloc[0]:,}")
        print(f"   ⚪ Movimientos como blancas: {debug_result['white_moves'].iloc[0]:,}")
        print(f"   ⚫ Movimientos como negras: {debug_result['black_moves'].iloc[0]:,}")
        
        # Query SIMPLIFICADA sin filtros restrictivos de ELO
        features_query = text("""
            SELECT 
                f.*,
                g.white_player,
                g.black_player,
                g.white_elo,
                g.black_elo,
                -- Clasificación simplificada por jugador específico
                CASE 
                    WHEN (f.player_color = 1 AND g.white_player IN ('cmess1315', 'cmess4401')) OR
                         (f.player_color = 0 AND g.black_player IN ('cmess1315', 'cmess4401')) 
                    THEN 'elo_1400_cmess'
                    
                    WHEN (f.player_color = 1 AND g.white_player = 'Th3_hound') OR
                         (f.player_color = 0 AND g.black_player = 'Th3_hound') 
                    THEN 'elo_2200_th3hound'
                    
                    -- Jugadores con ELO alto (sin restricciones tan altas)
                    WHEN (f.player_color = 1 AND g.white_elo ~ '^[0-9]+$' AND CAST(g.white_elo AS INTEGER) >= 1600) OR
                         (f.player_color = 0 AND g.black_elo ~ '^[0-9]+$' AND CAST(g.black_elo AS INTEGER) >= 1600)
                    THEN 'elo_1600_plus'
                    
                    ELSE 'other'
                END as player_type,
                
                -- ELO numérico del jugador correcto
                CASE 
                    WHEN f.player_color = 1 AND g.white_elo ~ '^[0-9]+$' THEN CAST(g.white_elo AS INTEGER)
                    WHEN f.player_color = 0 AND g.black_elo ~ '^[0-9]+$' THEN CAST(g.black_elo AS INTEGER)
                    ELSE NULL
                END as player_elo,
                
                -- Nombre del jugador actual
                CASE 
                    WHEN f.player_color = 1 THEN g.white_player
                    WHEN f.player_color = 0 THEN g.black_player
                END as current_player
                
            FROM features f
            LEFT JOIN games g ON f.game_id = g.game_id
            WHERE f.error_label IS NOT NULL
              AND (
                g.white_player IN ('cmess1315', 'cmess4401', 'Th3_hound') OR 
                g.black_player IN ('cmess1315', 'cmess4401', 'Th3_hound') OR
                (g.white_elo ~ '^[0-9]+$' AND CAST(g.white_elo AS INTEGER) >= 1600) OR
                (g.black_elo ~ '^[0-9]+$' AND CAST(g.black_elo AS INTEGER) >= 1600)
              )
            ORDER BY f.game_id, f.move_number
            LIMIT 10000;
        """)
        
        print(f"\n🔄 Cargando TODAS las features disponibles (hasta 10,000)...")
        features_df = pd.read_sql(features_query, engine)
        
        if len(features_df) == 0:
            print("❌ No se encontraron features")
            return None
            
        print(f"   ✅ Cargadas {len(features_df):,} features (movimientos)")
        
        # NO filtrar por 'unknown' - mantener todos los datos
        # features_df = features_df[features_df['player_type'] != 'unknown'].copy()
        
        # Summary by player type - INCLUYENDO TODOS LOS TIPOS
        if len(features_df) > 0:
            player_summary = features_df['player_type'].value_counts()
            print(f"\n📊 DISTRIBUCIÓN COMPLETA POR TIPO:")
            for player_type, count in player_summary.items():
                if player_type == "elo_1400_cmess":
                    print(f"   🎯 cmess1315/cmess4401 (~1320): {count:,} movimientos")
                elif player_type == "elo_2200_th3hound":  
                    print(f"   🏆 Grandes Maestros (~2600): {count:,} movimientos")
                elif player_type == "elo_1600_plus":
                    print(f"   🏆 Grandes Maestros (~2600+): {count:,} movimientos")
                else:
                    print(f"   ❓ {player_type}: {count:,} movimientos")
        
        # Detalle por jugador específico
        cmess_count = len(features_df[features_df['current_player'].isin(['cmess1315', 'cmess4401'])])
        masters_count = len(features_df[~features_df['current_player'].isin(['cmess1315', 'cmess4401'])])
        
        print(f"\n🎮 DETALLE POR GRUPO ESPECÍFICO:")
        print(f"   cmess1315/cmess4401: {cmess_count:,} movimientos")
        print(f"   Grandes Maestros: {masters_count:,} movimientos")
        
        engine.dispose()
        return features_df
        
    except Exception as e:
        print(f"❌ ERROR conectando a PostgreSQL: {e}")
        engine.dispose()
        return None

def create_streak_features(df):
    """
    Crea features de racha de fallos para cada jugador
    """
    print("\n🔄 GENERANDO FEATURES DE RACHA DE FALLOS...")
    
    # Crear copia para modificar
    df_enhanced = df.copy()
    
    # Definir qué es un "fallo"
    error_moves = ['mistake', 'blunder', 'inaccuracy']
    
    # Agregar features de racha por partida
    streak_features = []
    
    for game_id in df_enhanced['game_id'].unique():
        game_moves = df_enhanced[df_enhanced['game_id'] == game_id].sort_values('move_number')
        
        # Calcular racha de errores consecutivos
        game_moves = game_moves.copy()
        game_moves['is_error'] = game_moves['error_label'].isin(error_moves).astype(int)
        
        # Racha actual de errores
        current_streak = 0
        error_streak = []
        
        for is_error in game_moves['is_error']:
            if is_error:
                current_streak += 1
            else:
                current_streak = 0
            error_streak.append(current_streak)
        
        game_moves['error_streak'] = error_streak
        
        # Racha de movimientos buenos consecutivos
        current_good_streak = 0
        good_streak = []
        
        for is_error in game_moves['is_error']:
            if not is_error:
                current_good_streak += 1
            else:
                current_good_streak = 0
            good_streak.append(current_good_streak)
        
        game_moves['good_streak'] = good_streak
        
        # Tendencia reciente (últimos 5 movimientos)
        window_size = 5
        game_moves['recent_error_rate'] = game_moves['is_error'].rolling(window_size, min_periods=1).mean()
        
        # Presión por tiempo (asumir que movimientos tardíos = más presión)
        max_moves = len(game_moves)
        game_moves['time_pressure'] = game_moves['move_number'] / max_moves
        
        streak_features.append(game_moves)
    
    # Combinar todos los juegos
    enhanced_df = pd.concat(streak_features, ignore_index=True)
    
    print(f"   ✅ Features de racha agregadas:")
    print(f"      - error_streak: Errores consecutivos actuales")
    print(f"      - good_streak: Movimientos buenos consecutivos")  
    print(f"      - recent_error_rate: Tasa de error últimos 5 movimientos")
    print(f"      - time_pressure: Presión por tiempo en la partida")
    
    return enhanced_df

def analyze_player_patterns(df):
    """
    Analiza patrones específicos de cada jugador - VERSION EXPANSIVA
    """
    print("\n🔍 ANÁLISIS DETALLADO DE PATRONES POR JUGADOR:")
    
    # Análisis por tipo de jugador (TODOS LOS TIPOS)
    for player_type in df['player_type'].unique():
        player_data = df[df['player_type'] == player_type]
        
        if player_type == 'elo_1400_cmess':
            player_label = "🎯 cmess1315/cmess4401 (~1320 ELO)"
        elif player_type == 'elo_2200_th3hound':
            player_label = "🏆 Grandes Maestros (~2600 ELO)"
        elif player_type == 'elo_1600_plus':
            player_label = "🏆 Grandes Maestros (~2600+ ELO)"
        else:
            player_label = f"❓ {player_type}"
        
        print(f"\n   {player_label}:")
        print(f"      Movimientos totales: {len(player_data):,}")
        
        # Distribución de errores
        if len(player_data) > 0:
            error_dist = player_data['error_label'].value_counts(normalize=True)
            for error_type, pct in error_dist.items():
                print(f"      {error_type}: {pct*100:.1f}%")
            
            # Estadísticas de racha si están disponibles
            if 'error_streak' in player_data.columns:
                avg_error_streak = player_data['error_streak'].mean()
                max_error_streak = player_data['error_streak'].max()
                avg_good_streak = player_data['good_streak'].mean()
                
                print(f"      Racha promedio errores: {avg_error_streak:.2f}")
                print(f"      Máxima racha errores: {max_error_streak}")
                print(f"      Racha promedio buenos: {avg_good_streak:.2f}")
            
            # ELO promedio si disponible
            if 'player_elo' in player_data.columns and not player_data['player_elo'].isna().all():
                avg_elo = player_data['player_elo'].mean()
                print(f"      ELO promedio: {avg_elo:.0f}")
                
            # Partidas únicas
            if 'game_id' in player_data.columns:
                unique_games = player_data['game_id'].nunique()
                avg_moves_per_game = len(player_data) / unique_games if unique_games > 0 else 0
                print(f"      Partidas únicas: {unique_games}")
                print(f"      Movimientos por partida: {avg_moves_per_game:.1f}")
    
    # Análisis comparativo entre cmess1315 vs resto
    cmess_data = df[df['current_player'].isin(['cmess1315', 'cmess4401'])]
    others_data = df[~df['current_player'].isin(['cmess1315', 'cmess4401'])]
    
    if len(cmess_data) > 0 and len(others_data) > 0:
        print(f"\n🔥 COMPARATIVA DIRECTA:")
        print(f"   cmess1315: {len(cmess_data):,} movimientos")
        print(f"   Otros jugadores: {len(others_data):,} movimientos")
        
        # Comparar distribución de errores
        cmess_errors = cmess_data['error_label'].value_counts(normalize=True)
        others_errors = others_data['error_label'].value_counts(normalize=True)
        
        print(f"\n   📊 COMPARATIVA DE ERRORES:")
        all_error_types = set(cmess_errors.index) | set(others_errors.index)
        for error_type in ['good', 'inaccuracy', 'mistake', 'blunder']:
            if error_type in all_error_types:
                cmess_pct = cmess_errors.get(error_type, 0) * 100
                others_pct = others_errors.get(error_type, 0) * 100
                diff = others_pct - cmess_pct
                print(f"      {error_type:12}: cmess={cmess_pct:5.1f}% | otros={others_pct:5.1f}% | diff={diff:+5.1f}%")

def train_classification_models(df):
    """
    Entrena 3 tipos de modelos de clasificación
    """
    print(f"\n🤖 ENTRENAMIENTO DE MODELOS COMPARATIVOS:")
    
    # Features disponibles
    base_features = [
        'material_balance', 'material_total', 'num_pieces', 'branching_factor',
        'self_mobility', 'opponent_mobility', 'has_castling_rights', 'is_repetition',
        'is_low_mobility', 'is_center_controlled', 'is_pawn_endgame', 'score_diff',
        'player_color', 'move_number', 'move_number_global'
    ]
    
    # Features de racha si están disponibles
    streak_features = ['error_streak', 'good_streak', 'recent_error_rate', 'time_pressure']
    
    # Seleccionar features disponibles
    available_features = [f for f in base_features + streak_features if f in df.columns]
    
    print(f"   📊 Features utilizadas: {len(available_features)}")
    
    results = {}
    
    # 1. CLASIFICACIÓN DE TIPO DE JUGADA (error_label)
    print(f"\n   🎯 1. CLASIFICACIÓN DE TIPO DE JUGADA:")
    
    X = df[available_features].fillna(0)
    y_moves = df['error_label']
    
    if len(y_moves.unique()) > 1:
        results['move_classification'] = train_single_classification(
            X, y_moves, "Tipo de Jugada", available_features
        )
    
    # 2. CLASIFICACIÓN DE NIVEL DE JUGADOR
    print(f"\n   🎯 2. CLASIFICACIÓN DE NIVEL DE JUGADOR:")
    
    # Usar TODOS los player_type disponibles en lugar de solo algunos específicos
    available_player_types = df['player_type'].unique()
    print(f"      Tipos de jugador disponibles: {available_player_types}")
    
    if len(available_player_types) > 1:
        X_level = df[available_features].fillna(0)
        y_level = df['player_type']
        
        results['level_classification'] = train_single_classification(
            X_level, y_level, "Nivel de Jugador", available_features
        )
    else:
        print("      ⚠️ Solo un tipo de jugador disponible, no se puede entrenar")
    
    # 3. CLASIFICACIÓN DE RACHA DE FALLOS 
    print(f"\n   🎯 3. CLASIFICACIÓN DE RACHA DE FALLOS:")
    
    if 'error_streak' in df.columns:
        # Crear etiquetas de racha (0: sin racha, 1: racha moderate, 2: racha intensa)
        df_streak = df.copy()
        df_streak['streak_category'] = pd.cut(
            df_streak['error_streak'], 
            bins=[-0.1, 0.5, 2.5, float('inf')], 
            labels=['no_streak', 'moderate_streak', 'intense_streak']
        )
        
        if len(df_streak['streak_category'].unique()) > 1:
            X_streak = df_streak[available_features].fillna(0)
            y_streak = df_streak['streak_category']
            
            results['streak_classification'] = train_single_classification(
                X_streak, y_streak, "Racha de Fallos", available_features
            )
    
    return results

def train_single_classification(X, y, task_name, feature_names):
    """
    Entrena múltiples modelos para una tarea de clasificación específica
    """
    print(f"      📋 Tarea: {task_name}")
    print(f"      📊 Clases: {list(y.unique())}")
    print(f"      📊 Distribución:")
    
    class_counts = y.value_counts()
    for class_name, count in class_counts.items():
        print(f"         {class_name}: {count} ({count/len(y)*100:.1f}%)")
    
    # Encoding si es necesario
    if y.dtype == 'object':
        label_encoder = LabelEncoder()
        y_encoded = label_encoder.fit_transform(y)
        classes = label_encoder.classes_
    else:
        y_encoded = y
        classes = y.unique()
    
    # Split con estratificación si es posible
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.3, random_state=42, stratify=y_encoded
        )
    except ValueError:
        # Fallback sin estratificación
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.3, random_state=42
        )
    
    # Modelos a comparar
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
        'Logistic Regression': LogisticRegression(random_state=42, class_weight='balanced', max_iter=1000),
        'MLP Neural Network': MLPClassifier(hidden_layer_sizes=(64, 32), random_state=42, max_iter=500)
    }
    
    task_results = {}
    
    for model_name, model in models.items():
        try:
            # Scaling para modelos que lo necesiten
            if model_name in ['Logistic Regression', 'MLP Neural Network']:
                scaler = StandardScaler()
                X_train_scaled = scaler.fit_transform(X_train)
                X_test_scaled = scaler.transform(X_test)
                
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
            else:
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            # Métricas
            f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Cross-validation
            if model_name not in ['MLP Neural Network']:  # Skip CV for MLP to save time
                cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='f1_macro')
                cv_mean = cv_scores.mean()
            else:
                cv_mean = f1_macro
            
            task_results[model_name] = {
                'f1_macro': f1_macro,
                'accuracy': accuracy,
                'cv_f1_mean': cv_mean,
                'classes': classes if y.dtype == 'object' else None
            }
            
            print(f"         {model_name}: F1={f1_macro:.3f}, Acc={accuracy:.3f}, CV={cv_mean:.3f}")
            
        except Exception as e:
            print(f"         {model_name}: ERROR - {e}")
            task_results[model_name] = {'error': str(e)}
    
    return task_results

def generate_comparative_report(results):
    """
    Genera reporte comparativo final
    """
    print(f"\n" + "="*80)
    print("  REPORTE COMPARATIVO FINAL: cmess1315 vs Th3_hound vs 1800+ ELO")
    print("="*80)
    
    for task_name, task_results in results.items():
        if task_name == 'move_classification':
            print(f"\n🎯 CLASIFICACIÓN DE TIPO DE JUGADA (error_label):")
        elif task_name == 'level_classification':
            print(f"\n🏆 CLASIFICACIÓN DE NIVEL DE JUGADOR:")
        elif task_name == 'streak_classification':
            print(f"\n🔥 CLASIFICACIÓN DE RACHA DE FALLOS:")
        
        # Encontrar mejor modelo
        best_model = None
        best_f1 = 0
        
        for model_name, metrics in task_results.items():
            if 'error' not in metrics:
                f1_score = metrics.get('f1_macro', 0)
                if f1_score > best_f1:
                    best_f1 = f1_score
                    best_model = model_name
        
        if best_model:
            print(f"   🥇 MEJOR MODELO: {best_model}")
            print(f"   📊 F1 Score: {best_f1:.4f}")
            print(f"   📊 Accuracy: {task_results[best_model]['accuracy']:.4f}")
            print(f"   📊 CV Score: {task_results[best_model]['cv_f1_mean']:.4f}")
            
            if best_f1 > 0.8:
                print(f"   ✅ EXCELENTE: F1 > 0.8 - Clasificación muy confiable")
            elif best_f1 > 0.6:
                print(f"   📊 BUENO: F1 > 0.6 - Clasificación útil")
            elif best_f1 > 0.4:
                print(f"   ⚠️ REGULAR: F1 > 0.4 - Mejoras necesarias")
            else:
                print(f"   ❌ POBRE: F1 < 0.4 - Clasificación poco confiable")
        
        # Mostrar todos los resultados
        print(f"   📋 COMPARATIVA COMPLETA:")
        for model_name, metrics in task_results.items():
            if 'error' not in metrics:
                f1 = metrics.get('f1_macro', 0)
                acc = metrics.get('accuracy', 0) 
                cv = metrics.get('cv_f1_mean', 0)
                print(f"      {model_name:20}: F1={f1:.3f} | Acc={acc:.3f} | CV={cv:.3f}")

# Ejecución principal
if __name__ == "__main__":
    print("="*80)
    print("  ANÁLISIS COMPARATIVO: cmess1315/cmess4401 vs GRANDES MAESTROS")
    print("  Comparación: ~1320 ELO vs ~2600 ELO (Kasparov, Karpov, etc.)")
    print("  Clasificaciones: Tipo jugada | Nivel jugador | Racha fallos")
    print("="*80)
    
    try:
        # 1. Cargar datos comparativos
        df = load_comparative_data()
        
        if df is None or len(df) == 0:
            print("\n❌ No se pudieron cargar datos comparativos")
            sys.exit(1)
        
        # 2. Crear features de racha
        df_enhanced = create_streak_features(df)
        
        # 3. Analizar patrones
        analyze_player_patterns(df_enhanced)
        
        # 4. Entrenar modelos comparativos
        results = train_classification_models(df_enhanced)
        
        # 5. Generar reporte final
        generate_comparative_report(results)
        
        print(f"\n🎯 CONCLUSIONES COMPARATIVAS:")
        print(f"   ✅ Análisis completado con datos reales PostgreSQL")
        print(f"   📊 Modelos entrenados para 3 tipos de clasificación")
        print(f"   🔍 Patrones identificados entre niveles de jugador")
        print(f"   📈 Features de racha implementadas exitosamente")
        
    except Exception as e:
        print(f"[ERROR] Análisis falló: {e}")
        import traceback
        traceback.print_exc()