#!/usr/bin/env python3
"""
PHASE 3 - Análisis Temporal (Errores en Cadena) - UPDATED
=========================================================

Post Phase 2 Success: Building on MLP F1=0.992 baseline
Target: F1 >0.995 using temporal sequence analysis

Features: Sliding windows of 5-7 moves with temporal features
Models: 1D-CNN, GRU, Hybrid CNN+GRU  
Objetivo: Detect error patterns in sequences, predict collapse risk
"""
import os
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score, classification_report
from sklearn.utils.class_weight import compute_sample_weight
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# Configure encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("="*70)
print("  PHASE 3 TEMPORAL ANALYSIS - UPDATED")
print("="*70)

# Baseline results from Phase 2
PHASE2_BASELINE = {
    'model': 'MLP_Basic',
    'f1_macro': 0.992,
    'accuracy': 0.998,
    'features_count': 15,
    'samples': 328283
}

print(f"\n[BASELINE] Phase 2 MLP: F1={PHASE2_BASELINE['f1_macro']:.3f}")
print(f"[TARGET] Phase 3 Temporal: F1 >{PHASE2_BASELINE['f1_macro']:.3f}")

# 1. Load Sequential Data
print("\n[+] Cargando datos secuenciales...")
engine = create_engine('postgresql://chess:chess_pass@localhost:5432/chess_trainer_db')

# Enhanced query with temporal ordering
query = """
SELECT 
    f.game_id,
    f.move_number,
    f.material_balance, f.material_total, f.num_pieces,
    f.branching_factor, f.self_mobility, f.opponent_mobility,
    f.has_castling_rights, f.is_repetition, f.is_low_mobility,
    f.is_center_controlled, f.is_pawn_endgame, f.score_diff,
    f.player_color, f.error_label
FROM features f 
WHERE f.error_label IS NOT NULL 
    AND f.error_label != ''
    AND f.game_id IN (
        SELECT game_id FROM features 
        WHERE error_label IS NOT NULL 
        GROUP BY game_id 
        HAVING COUNT(*) >= 7  -- At least 7 moves for sequences
    )
ORDER BY f.game_id, f.move_number
"""

df_sequential = pd.read_sql(query, engine)
engine.dispose()

print(f"[OK] {len(df_sequential)} registros de {df_sequential['game_id'].nunique()} partidas")
print(f"[INFO] Promedio {len(df_sequential)/df_sequential['game_id'].nunique():.1f} movimientos por partida")

# 2. Generate Temporal Features
print("\n[+] Generando features temporales...")

def create_temporal_features(df):
    """Create advanced temporal features for sequence analysis"""
    
    temporal_df = []
    
    for game_id in df['game_id'].unique():
        game_data = df[df['game_id'] == game_id].copy().sort_values('move_number')
        
        if len(game_data) < 5:  # Skip games too short
            continue
            
        # Score evolution features
        game_data['score_diff_lag1'] = game_data['score_diff'].shift(1).fillna(0)
        game_data['score_diff_lag2'] = game_data['score_diff'].shift(2).fillna(0)
        game_data['score_cp_change'] = game_data['score_diff'] - game_data['score_diff_lag1']
        game_data['score_acceleration'] = game_data['score_cp_change'].diff().fillna(0)
        
        # Error sequence features
        error_map = {'good': 0, 'inaccuracy': 1, 'mistake': 2, 'blunder': 3}
        game_data['error_numeric'] = game_data['error_label'].map(error_map)
        game_data['is_error'] = (game_data['error_numeric'] >= 1).astype(int)
        
        # Rolling error statistics
        game_data['errors_last_3'] = game_data['is_error'].rolling(3, min_periods=1).sum()
        game_data['errors_last_5'] = game_data['is_error'].rolling(5, min_periods=1).sum()
        game_data['max_error_last_3'] = game_data['error_numeric'].rolling(3, min_periods=1).max()
        
        # Consecutive error counting
        game_data['consecutive_errors'] = (
            game_data['is_error'] * 
            (game_data['is_error'].groupby((game_data['is_error'] == 0).cumsum()).cumcount() + 1)
        ).fillna(0)
        
        # Trending features
        game_data['score_trend_3'] = game_data['score_diff'].rolling(3, min_periods=1).mean()
        game_data['score_volatility'] = game_data['score_diff'].rolling(3, min_periods=1).std().fillna(0)
        game_data['declining_position'] = (game_data['score_trend_3'].diff() < -30).astype(int)
        
        # Time pressure simulation (based on move number and game length)
        max_moves = len(game_data)
        game_data['game_progress'] = game_data['move_number'] / max_moves
        game_data['time_pressure'] = (game_data['game_progress'] > 0.6).astype(int)
        game_data['endgame_phase'] = (game_data['game_progress'] > 0.8).astype(int)
        
        # Momentum features
        game_data['momentum_lost'] = (
            (game_data['score_cp_change'] < -50) & 
            (game_data['score_diff_lag1'] > 0)
        ).astype(int)
        
        game_data['critical_moment'] = (
            (game_data['score_volatility'] > 100) | 
            (game_data['errors_last_3'] >= 2)
        ).astype(int)
        
        temporal_df.append(game_data)
    
    result = pd.concat(temporal_df, ignore_index=True)
    
    new_features = [
        'score_diff_lag1', 'score_diff_lag2', 'score_cp_change', 'score_acceleration',
        'errors_last_3', 'errors_last_5', 'max_error_last_3', 'consecutive_errors',
        'score_trend_3', 'score_volatility', 'declining_position',
        'game_progress', 'time_pressure', 'endgame_phase', 
        'momentum_lost', 'critical_moment'
    ]
    
    print(f"[OK] {len(new_features)} features temporales creadas")
    return result, new_features

df_temporal, temporal_feature_names = create_temporal_features(df_sequential)

print(f"[OK] Dataset temporal: {len(df_temporal)} registros")
print(f"[INFO] Distribución de etiquetas:")
label_dist = df_temporal['error_label'].value_counts()
for label, count in label_dist.items():
    pct = count/len(df_temporal)*100
    print(f"   {label:12}: {count:6} ({pct:5.1f}%)")

# 3. Create Sequence Sliding Windows
print("\n[+] Creando ventanas secuenciales...")

def create_sequence_windows(df, window_size=5):
    """Create sliding windows for temporal analysis"""
    
    # Original features + temporal features
    feature_cols = [
        'material_balance', 'material_total', 'num_pieces',
        'branching_factor', 'self_mobility', 'opponent_mobility',
        'has_castling_rights', 'is_repetition', 'is_low_mobility',
        'is_center_controlled', 'is_pawn_endgame', 'score_diff', 'player_color'
    ] + temporal_feature_names
    
    sequences = []
    labels = []
    
    for game_id in df['game_id'].unique():
        game_data = df[df['game_id'] == game_id].sort_values('move_number')
        
        if len(game_data) < window_size:
            continue
            
        # Create sliding windows
        for i in range(len(game_data) - window_size + 1):
            window = game_data.iloc[i:i + window_size]
            
            # Features: flatten window (window_size × n_features)
            X_window = window[feature_cols].values.flatten()
            
            # Label: predict label of the LAST move in window
            y_window = window.iloc[-1]['error_label']
            
            sequences.append(X_window)
            labels.append(y_window)
    
    X = np.array(sequences)
    y = np.array(labels)
    
    print(f"[OK] {len(X)} secuencias creadas")
    print(f"[INFO] Shape: {X.shape} (samples, features_per_window)")
    
    return X, y, len(feature_cols)

# Create sequences
WINDOW_SIZE = 5
X_seq, y_seq, n_features = create_sequence_windows(df_temporal, WINDOW_SIZE)

print(f"\n[INFO] Secuencias: {X_seq.shape}")
print(f"[INFO] Features por movimiento: {n_features}")
print(f"[INFO] Features totales: {X_seq.shape[1]} ({n_features} × {WINDOW_SIZE})")

# 4. Data Preparation
print("\n[+] Preparando datos...")

# Fill NaN values
X_seq = np.nan_to_num(X_seq, nan=0.0)

# Standard scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_seq)

# Train/Test split stratified
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y_seq, test_size=0.2, random_state=42, stratify=y_seq
)

# Sample weights for class balance (same as Phase 2)
sample_weights = compute_sample_weight('balanced', y_train)

print(f"[OK] Train: {len(X_train)}, Test: {len(X_test)}")
print("\n[*] Sample weights:")
for label in np.unique(y_train):
    weight = sample_weights[y_train == label].mean()
    print(f"   {label:12}: {weight:.2f}")

# 5. Models for Temporal Analysis
print("\n" + "="*70)
print("  PHASE 3 TEMPORAL MODELS")  
print("="*70)

# We'll use sklearn models first (like Phase 2), then potentially add deep learning

from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.linear_model import LogisticRegression

# Model configurations optimized for temporal sequences
models = [
    ('Logistic_Temporal', LogisticRegression(
        random_state=42, max_iter=1000, class_weight='balanced'
    )),
    ('RF_Temporal', RandomForestClassifier(
        n_estimators=200, max_depth=15, random_state=42, 
        class_weight='balanced', n_jobs=-1
    )),
    ('MLP_Temporal_Small', MLPClassifier(
        hidden_layer_sizes=(100,), max_iter=300, random_state=42
    )),
    ('MLP_Temporal_Deep', MLPClassifier(
        hidden_layer_sizes=(200, 100, 50), max_iter=500, random_state=42,
        alpha=0.01  # More regularization for deeper network
    )),
]

# 6. Training and Evaluation
results = []

for name, model in models:
    print(f"\n[*] {name}...")
    
    model.fit(X_train, y_train, sample_weight=sample_weights)
    
    # Predictions
    y_pred = model.predict(X_test)
    
    # Metrics
    f1 = f1_score(y_test, y_pred, average='macro')
    acc = accuracy_score(y_test, y_pred)
    
    # Cross validation
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='f1_macro')
    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()
    
    # Compare with Phase 2 baseline
    delta_f1 = f1 - PHASE2_BASELINE['f1_macro']
    
    results.append({
        'Model': name,
        'F1_Macro': f1,
        'Accuracy': acc,
        'CV_Mean': cv_mean,
        'CV_Std': cv_std,
        'Delta_vs_Phase2': delta_f1,
        'Improved': delta_f1 > 0
    })
    
    # Display results
    print(f"   F1 Macro: {f1:.4f} ({delta_f1:+.4f} vs Phase 2)")
    print(f"   Accuracy: {acc:.4f}")
    print(f"   CV: {cv_mean:.4f} ± {cv_std:.4f}")
    if delta_f1 > 0:
        print(f"   ✅ MEJORA sobre Phase 2!")
    else:
        print(f"   ❌ No supera Phase 2")

# 7. Results Summary
print("\n" + "="*70)
print("  PHASE 3 TEMPORAL - RESULTADOS FINALES")
print("="*70)

# Convert results to DataFrame for better display
results_df = pd.DataFrame(results)
results_df = results_df.sort_values('F1_Macro', ascending=False)

print(f"\nPhase 2 Baseline: F1={PHASE2_BASELINE['f1_macro']:.4f} (MLP_Basic)")
print("\nPhase 3 Temporal Results:")
print(results_df.to_string(index=False, float_format="%.4f"))

# Best model
best_model = results_df.iloc[0]
print(f"\n🏆 MEJOR MODELO: {best_model['Model']}")
print(f"   F1 Macro: {best_model['F1_Macro']:.4f}")
print(f"   Delta: {best_model['Delta_vs_Phase2']:+.4f}")
print(f"   Status: {'✅ SUPERA Phase 2' if best_model['Improved'] else '❌ NO supera Phase 2'}")

# 8. Detailed Analysis of Best Model
if best_model['Improved']:
    print(f"\n🎯 ANÁLISIS DETALLADO - {best_model['Model']}")
    
    # Find the best model instance
    best_model_name = best_model['Model']
    best_model_instance = None
    for name, model in models:
        if name == best_model_name:
            best_model_instance = model
            break
    
    if best_model_instance:
        y_pred_best = best_model_instance.predict(X_test)
        
        print(f"\nClassification Report:")
        print(classification_report(y_test, y_pred_best))
        
        # Temporal-specific analysis
        print(f"\n🕐 ANÁLISIS TEMPORAL ESPECÍFICO:")
        
        # Find cases where temporal model outperforms individual predictions
        print(f"   Dataset: {len(X_test)} secuencias de test")
        print(f"   Window size: {WINDOW_SIZE} movimientos")
        print(f"   Features temporales: {len(temporal_feature_names)}")
        print(f"   Total features: {X_seq.shape[1]} (flattened)")
        
        # Error type analysis
        error_analysis = pd.DataFrame({
            'true': y_test,
            'pred': y_pred_best
        })
        
        print(f"\n📊 Análisis por tipo de error:")
        for error_type in ['good', 'inaccuracy', 'mistake', 'blunder']:
            if error_type in error_analysis['true'].values:
                mask = error_analysis['true'] == error_type
                if mask.sum() > 0:
                    accuracy = (error_analysis.loc[mask, 'true'] == error_analysis.loc[mask, 'pred']).mean()
                    count = mask.sum()
                    print(f"   {error_type:12}: {accuracy:.3f} accuracy ({count} samples)")

else:
    print(f"\n⚠️ PHASE 3 NO SUPERÓ PHASE 2")
    print(f"   Phase 2 MLP sigue siendo el mejor modelo")
    print(f"   Mejor temporal: {best_model['F1_Macro']:.4f}")
    print(f"   Diferencia: {best_model['Delta_vs_Phase2']:.4f}")

# 9. Conclusions and Next Steps
print(f"\n🔍 CONCLUSIONES:")
print(f"1. Datos secuenciales: {len(X_seq)} ventanas de {WINDOW_SIZE} movimientos")
print(f"2. Features temporales: {len(temporal_feature_names)} nuevas características")
print(f"3. Mejor modelo temporal: {best_model['Model']} (F1={best_model['F1_Macro']:.4f})")

if best_model['Improved']:
    print(f"4. ✅ ÉXITO: Phase 3 supera Phase 2 en {best_model['Delta_vs_Phase2']:+.4f} puntos F1")
    print(f"5. 🚀 Recomendación: Implementar modelo temporal en producción")
else:
    print(f"4. ❌ Phase 3 no supera Phase 2 baseline")
    print(f"5. 🤔 Posibles mejoras: Deep learning (CNN/GRU), más features temporales")

print(f"\n📁 Próximos pasos:")
print(f"   - Documentar resultados en docs/PHASE3_RESULTS.md")
print(f"   - Si exitoso: Proceder con Phase 4 (Embeddings)")  
print(f"   - Si no exitoso: Refinar features temporales o deep learning")

print(f"\n{'='*70}")
print(f"  PHASE 3 TEMPORAL ANALYSIS - COMPLETADO")
print(f"{'='*70}")