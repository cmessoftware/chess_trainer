#!/usr/bin/env python3
"""
REAL DATA ANALYSIS - Chess.com Users Comparison
==============================================

Usuarios reales para análisis:
- cmess1315/cmess4401: Usuario ~1400 ELO 
- Th3_hound: Entrenador humano ~2200 ELO FIDE

OBJETIVO: Validación honesta con datos REALES de PostgreSQL
¿Pueden nuestros modelos realmente distinguir entre 1400 vs 2200 ELO?
"""
import numpy as np
import pandas as pd
import os
import dotenv
from sqlalchemy import create_engine, text
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
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

def load_real_chess_data_from_db():
    """
    Carga datos REALES desde PostgreSQL para los usuarios específicos
    NO usa datos sintéticos - conecta directamente a la base de datos
    """
    
    print("🔍 CONECTANDO A POSTGRESQL PARA DATOS REALES...")
    print("   👤 cmess1315/cmess4401 (~1400 ELO)")  
    print("   🎯 Th3_hound (~2200 ELO FIDE)")
    
    # Connection to PostgreSQL
    DATABASE_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db")
    engine = create_engine(DATABASE_URL)
    
    try:
        # Query to find games for these exact players
        users_query = text("""
            SELECT 
                g.game_id,
                g.white_player, 
                g.black_player,
                g.white_elo,
                g.black_elo,
                g.result,
                g.time_control,
                g.source,
                g.date_played
            FROM games g 
            WHERE 
                (g.white_player IN ('cmess1315', 'cmess4401', 'Th3_hound') OR 
                 g.black_player IN ('cmess1315', 'cmess4401', 'Th3_hound'))
            ORDER BY g.date_played DESC
            LIMIT 1000;
        """)
        
        print("\n📊 Buscando partidas en PostgreSQL...")
        games_df = pd.read_sql(users_query, engine)
        
        if len(games_df) == 0:
            print("❌ No se encontraron partidas para estos usuarios")
            print("   Verificar nombres de usuario en la base de datos")
            return None
            
        print(f"   ✅ Encontradas {len(games_df)} partidas")
        
        # Show sample of found games
        print(f"\n🎮 PARTIDAS ENCONTRADAS:")
        for _, game in games_df.head(5).iterrows():
            white_player = game['white_player']
            black_player = game['black_player'] 
            white_elo = game['white_elo'] or 'N/A'
            black_elo = game['black_elo'] or 'N/A'
            print(f"   {white_player} ({white_elo}) vs {black_player} ({black_elo})")
        
        # Extract game_ids for feature lookup
        game_ids = games_df['game_id'].tolist()
        game_ids_str = "'" + "', '".join(game_ids) + "'"
        
        # Query features for these games
        features_query = text(f"""
            SELECT 
                f.*,
                -- Classify player type based on ELO estimation
                CASE 
                    WHEN f.white_player IN ('cmess1315', 'cmess4401') OR 
                         f.black_player IN ('cmess1315', 'cmess4401') THEN 'elo_1400'
                    WHEN f.white_player = 'Th3_hound' OR 
                         f.black_player = 'Th3_hound' THEN 'elo_2200'
                    ELSE 'unknown'
                END as player_type
            FROM features f
            WHERE f.game_id IN ({game_ids_str})
              AND f.error_label IS NOT NULL
            ORDER BY f.game_id, f.move_number;
        """)
        
        print(f"\n🔄 Cargando features calculadas de Stockfish...")
        features_df = pd.read_sql(features_query, engine)
        
        if len(features_df) == 0:
            print("❌ No se encontraron features para estas partidas")
            print("   Ejecutar generate_features_with_tactics.py primero")
            return None
            
        print(f"   ✅ Cargadas {len(features_df):,} features (movimientos)")
        
        # Summary by player type
        player_summary = features_df['player_type'].value_counts()
        print(f"\n📊 DISTRIBUCIÓN POR NIVEL:")
        for player_type, count in player_summary.items():
            if player_type != 'unknown':
                label = "1400 ELO" if player_type == "elo_1400" else "2200 ELO"
                print(f"   {label}: {count:,} movimientos")
        
        # Error distribution
        error_summary = features_df.groupby('player_type')['error_label'].value_counts(normalize=True)
        print(f"\n🎯 DISTRIBUCIÓN DE ERRORES REAL:")
        for player_type in ['elo_1400', 'elo_2200']:
            if player_type in player_summary:
                label = "1400 ELO" if player_type == "elo_1400" else "2200 ELO"
                print(f"   {label}:")
                if player_type in error_summary.index.get_level_values(0):
                    player_errors = error_summary[player_type]
                    for error_type, percentage in player_errors.items():
                        print(f"      {error_type}: {percentage*100:.1f}%")
        
        engine.dispose()
        return features_df
        
    except Exception as e:
        print(f"❌ ERROR conectando a PostgreSQL: {e}")
        print(f"   Verificar variable CHESS_TRAINER_DB_URL")
        print(f"   Verificar que PostgreSQL esté corriendo")
        engine.dispose()
        return None

def analyze_real_data_patterns(df):
    """Analiza patrones reales cargados desde PostgreSQL"""
    
    print("\n🔍 ANÁLISIS DE PATRONES REALES DE POSTGRESQL:")
    
    # Filter out unknown players
    df_filtered = df[df['player_type'] != 'unknown'].copy()
    
    if len(df_filtered) == 0:
        print("❌ No hay datos válidos para analizar")
        return
    
    # Comparación por nivel de ELO
    elo_comparison = df_filtered.groupby('player_type')['error_label'].value_counts(normalize=True).unstack(fill_value=0)
    
    print(f"\n📊 DISTRIBUCIÓN DE ERRORES POR NIVEL (DATOS REALES):")
    print(f"{'Tipo Error':<12} {'1400 ELO':<10} {'2200 ELO':<10} {'Diferencia':<10}")
    print("-" * 50)
    
    for error_type in ['good', 'inaccuracy', 'mistake', 'blunder']:
        if error_type in elo_comparison.columns:
            elo_1400_pct = elo_comparison.loc['elo_1400', error_type] * 100 if 'elo_1400' in elo_comparison.index else 0
            elo_2200_pct = elo_comparison.loc['elo_2200', error_type] * 100 if 'elo_2200' in elo_comparison.index else 0
            difference = elo_2200_pct - elo_1400_pct
            
            print(f"{error_type:<12} {elo_1400_pct:>6.1f}%   {elo_2200_pct:>6.1f}%   {difference:>+6.1f}%")
    
    # Análisis por fase del juego usando move_number como proxy
    print(f"\n🎯 ANÁLISIS POR FASE DEL JUEGO (BASADO EN NÚMERO DE MOVIMIENTO):")
    
    for player_type in ['elo_1400', 'elo_2200']:
        player_data = df_filtered[df_filtered['player_type'] == player_type]
        
        if len(player_data) == 0:
            continue
            
        # Dividir por fases basado en número de movimiento
        opening = player_data[player_data['move_number'] <= 15]['error_label'].value_counts(normalize=True)
        middlegame = player_data[(player_data['move_number'] > 15) & (player_data['move_number'] <= 40)]['error_label'].value_counts(normalize=True)
        endgame = player_data[player_data['move_number'] > 40]['error_label'].value_counts(normalize=True)
        
        player_display = "1400 ELO" if player_type == 'elo_1400' else "2200 ELO"
        print(f"\n   🎮 {player_display}:")
        
        print(f"      Apertura (1-15): {opening.get('mistake', 0)*100:.1f}% mistakes, {opening.get('blunder', 0)*100:.1f}% blunders")
        print(f"      Medio juego (16-40): {middlegame.get('mistake', 0)*100:.1f}% mistakes, {middlegame.get('blunder', 0)*100:.1f}% blunders") 
        print(f"      Final (40+): {endgame.get('mistake', 0)*100:.1f}% mistakes, {endgame.get('blunder', 0)*100:.1f}% blunders")
    
    # Game statistics
    print(f"\n📈 ESTADÍSTICAS GENERALES:")
    game_stats = df_filtered.groupby('player_type')['game_id'].nunique()
    for player_type, count in game_stats.items():
        label = "1400 ELO" if player_type == "elo_1400" else "2200 ELO"
        total_moves = len(df_filtered[df_filtered['player_type'] == player_type])
        avg_moves = total_moves / count if count > 0 else 0
        print(f"   {label}: {count} partidas, {avg_moves:.1f} movimientos promedio por partida")

def train_realistic_models(df):
    """Entrena modelos con datos REALES de PostgreSQL y evalúa rendimiento honesto"""
    
    print(f"\n🤖 ENTRENAMIENTO CON DATOS REALES DE POSTGRESQL:")
    
    # Filter out unknown players
    df_filtered = df[df['player_type'] != 'unknown'].copy()
    
    if len(df_filtered) == 0:
        print("❌ No hay datos válidos para entrenamiento")
        return {}, None
    
    # Usar columnas reales de la tabla features de PostgreSQL
    feature_cols = [
        'material_balance', 'material_total', 'num_pieces', 'branching_factor',
        'self_mobility', 'opponent_mobility', 'has_castling_rights', 'is_repetition',
        'is_low_mobility', 'is_center_controlled', 'is_pawn_endgame', 'score_diff',
        'player_color', 'move_number', 'move_number_global'
    ]
    
    # Filter only existing columns
    available_cols = [col for col in feature_cols if col in df_filtered.columns]
    
    if len(available_cols) < 5:
        print(f"❌ Insuficientes features disponibles: {available_cols}")
        return {}, None
    
    print(f"   📊 Features utilizadas: {len(available_cols)} de {len(feature_cols)}")
    for col in available_cols:
        print(f"      - {col}")
    
    X = df_filtered[available_cols].fillna(0)
    y = df_filtered['error_label']
    
    # Check class distribution
    class_counts = y.value_counts()
    print(f"\n   📊 Distribución de clases:")
    for class_name, count in class_counts.items():
        print(f"      {class_name}: {count} movimientos ({count/len(y)*100:.1f}%)")
    
    # Label encoding
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    # Split estratificado
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.3, random_state=42, stratify=y_encoded
        )
    except ValueError as e:
        print(f"❌ Error en split estratificado: {e}")
        # Fallback sin estratificar
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.3, random_state=42
        )
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Sample weights para balance
    try:
        sample_weights = compute_sample_weight('balanced', y_train)
    except ValueError:
        # Si falla, usar pesos uniformes
        sample_weights = None
    
    print(f"   📊 Dataset: {len(X_train)} train, {len(X_test)} test")
    
    # Modelos a probar
    models = {
        'Random Forest': RandomForestClassifier(
            n_estimators=100, max_depth=10, random_state=42, 
            class_weight='balanced'
        ),
        'MLP Neural Network': MLPClassifier(
            hidden_layer_sizes=(128, 64), max_iter=300, random_state=42,
            alpha=0.01, early_stopping=True
        )
    }
    
    results = {}
    
    for name, model in models.items():
        print(f"\n   🔄 Entrenando {name}...")
        
        try:
            # Train
            if name == 'MLP Neural Network':
                model.fit(X_train_scaled, y_train)
                y_pred = model.predict(X_test_scaled)
            else:
                if sample_weights is not None:
                    model.fit(X_train, y_train, sample_weight=sample_weights)
                else:
                    model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            
            # Evaluate
            f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
            accuracy = accuracy_score(y_test, y_pred)
            
            # Per-class F1
            f1_per_class = f1_score(y_test, y_pred, average=None, zero_division=0)
            classes = label_encoder.classes_
            
            results[name] = {
                'f1_macro': f1_macro,
                'accuracy': accuracy,
                'f1_per_class': dict(zip(classes, f1_per_class))
            }
            
            print(f"      F1 Macro: {f1_macro:.4f}")
            print(f"      Accuracy: {accuracy:.4f}")
            
        except Exception as e:
            print(f"      ❌ Error entrenando {name}: {e}")
            results[name] = {
                'f1_macro': 0.0,
                'accuracy': 0.0,
                'f1_per_class': {}
            }
    
    return results, label_encoder

def realistic_performance_analysis(results):
    """Análisis honesto del rendimiento en datos reales de PostgreSQL"""
    
    print(f"\n" + "="*70)
    print("  RESULTADOS REALES vs EXPECTATIVAS SINTÉTICAS")
    print("="*70)
    
    print(f"\n🎯 COMPARACIÓN BRUTAL DE HONESTIDAD:")
    
    synthetic_f1 = 1.0000  # Nuestro resultado anterior "perfecto"
    
    for model_name, performance in results.items():
        real_f1 = performance['f1_macro']
        reality_gap = real_f1 - synthetic_f1
        
        print(f"\n   🤖 {model_name}:")
        print(f"      Datos Sintéticos: F1 = {synthetic_f1:.4f} (Artificial)")
        print(f"      Datos Reales PostgreSQL: F1 = {real_f1:.4f} (Real)")
        print(f"      Gap de Realidad:  {reality_gap:+.4f} ({reality_gap/synthetic_f1*100:+.1f}%)")
        
        # Por clase
        print(f"      F1 por clase:")
        for error_type, f1_class in performance['f1_per_class'].items():
            print(f"         {error_type:12}: {f1_class:.4f}")
    
    # Análisis de ambigüedad en 'inaccuracy'
    if results:
        best_model = max(results.keys(), key=lambda k: results[k]['f1_macro'])
        inaccuracy_f1 = results[best_model]['f1_per_class'].get('inaccuracy', 0)
        
        print(f"\n💡 ANÁLISIS DE AMBIGÜEDAD:")
        print(f"   ❓ 'inaccuracy' F1: {inaccuracy_f1:.4f}")
        
        if inaccuracy_f1 < 0.7:
            print(f"   ✅ CONFIRMADO: 'inaccuracy' es ambigua (F1 < 0.7)")
            print(f"   🎯 Esto valida la crítica original del usuario")
        elif inaccuracy_f1 > 0.85:
            print(f"   ⚠️ Sorprendentemente alto - revisar datos")
        else:
            print(f"   📊 Performance moderada - esperada para categoría ambigua")

# Ejecución principal
if __name__ == "__main__":
    print("="*80)
    print("  ANÁLISIS REAL: cmess1315/cmess4401 (1400) vs Th3_hound (2200)")
    print("="*80)
    
    print(f"\n✋ RECONOCIMIENTO DE HUMILDAD:")
    print(f"   Usuario tenía razón - datos sintéticos eran condescendientes")
    print(f"   Ahora usando datos REALES de PostgreSQL con features de Stockfish...")
    print(f"   Conectándose a base de datos para cmess1315/cmess4401 y Th3_hound")
    
    try:
        # 1. Cargar datos REALES de PostgreSQL
        df_real = load_real_chess_data_from_db()
        
        if df_real is None:
            print("\n❌ No se pudieron cargar datos reales")
            print("   Verificar:")
            print("   - PostgreSQL está corriendo (docker-compose up postgres)")
            print("   - Variables de entorno configuradas")
            print("   - Usuarios existen en la base de datos")
            sys.exit(1)
        
        # 2. Analizar patrones reales
        analyze_real_data_patterns(df_real)
        
        # 3. Entrenar modelos con datos reales
        results, label_encoder = train_realistic_models(df_real)
        
        if not results:
            print("\n❌ No se pudieron entrenar modelos")
            sys.exit(1)
    
        # 4. Análisis honesto con datos reales
        realistic_performance_analysis(results)
        
        # 5. Conclusión final
        print(f"\n" + "="*70)
        print("  CONCLUSIÓN HONESTA")
        print("="*70)
        
        best_f1 = max(result['f1_macro'] for result in results.values())
        
        print(f"\n🎯 RENDIMIENTO REAL:")
        print(f"   Mejor F1 Macro: {best_f1:.4f} (vs 1.0000 artificial)")
        print(f"   Gap de Realidad: {best_f1 - 1.0:.4f} ({(best_f1 - 1.0)*100:.1f}%)")
        
        if best_f1 > 0.75:
            print(f"\n✅ RESULTADO: Performance sólida en datos realistas")
            print(f"   F1 > 0.75 es excelente para ajedrez real con ambigüedad")
        elif best_f1 > 0.65:
            print(f"\n📊 RESULTADO: Performance aceptable pero mejorable")
            print(f"   F1 > 0.65 es realista, especialmente para 'inaccuracy'")
        else:
            print(f"\n⚠️ RESULTADO: Performance necesita mejoras significativas")
            print(f"   F1 < 0.65 sugiere limitaciones del enfoque actual")
        
        print(f"\n🙏 LECCIÓN APRENDIDA:")
        print(f"   Humildad científica > Métricas artificiales perfectas")
        print(f"   Datos reales revelan verdaderas capacidades del modelo")
        print(f"   Gracias al usuario por la crítica constructiva necesaria")
        
    except Exception as e:
        print(f"[ERROR] Análisis falló: {e}")
        import traceback
        traceback.print_exc()
        traceback.print_exc()