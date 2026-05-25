#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 - Gradient Boosting Models
Challenger vs MLP_Basic champion (F1=0.992)

Testing: XGBoost, LightGBM, CatBoost with balanced sampling
Author: Chess Trainer ML Pipeline
Date: February 7, 2026
"""

import os
import sys
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.utils.class_weight import compute_sample_weight  
from sklearn.metrics import f1_score, accuracy_score, classification_report
import xgboost as xgb
import lightgbm as lgb
import catboost as cb

print("\n" + "="*70)
print("  PHASE 2 GRADIENT BOOSTING - vs MLP_Basic F1=0.992")
print("="*70)

# 1. Cargar datos (mismos que MLP)
print("\n[+] Cargando datos...")
engine = create_engine('postgresql://chess:chess_pass@localhost:5432/chess_trainer_db')
query = """
SELECT f.material_balance, f.material_total, f.num_pieces, f.branching_factor,
       f.self_mobility, f.opponent_mobility, f.has_castling_rights,
       f.is_repetition, f.is_low_mobility, f.is_center_controlled,
       f.is_pawn_endgame, f.score_diff, f.player_color,
       COALESCE(NULLIF(g.white_elo, ''), '1500')::int as white_elo, 
       COALESCE(NULLIF(g.black_elo, ''), '1500')::int as black_elo, 
       f.error_label
FROM features f JOIN games g ON f.game_id = g.game_id
WHERE f.error_label IS NOT NULL AND f.error_label != ''
"""
df = pd.read_sql_query(query, engine)
engine.dispose()
print(f"[OK] {len(df)} registros cargados")

# 2. Preparar datos - misma metodología que MLP
df = df.fillna(0)
X = df.drop('error_label', axis=1).values.astype(float)
y = df['error_label'].values

# Encode labels para los modelos que requieren numérico
le = LabelEncoder()
y_encoded = le.fit_transform(y)

X_scaled = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded)

# Compute sample weights (igual que MLP)  
sample_weights = compute_sample_weight('balanced', y_train)

print(f"[OK] Train: {len(X_train)}, Test: {len(X_test)}")
print("\n[*] Sample weights:")
for i, label in enumerate(le.classes_):
    mask = y_train == i
    print(f"   {label}: {sample_weights[mask].mean():.2f}")

# 3. Benchmark - MLP_Basic results to beat
mlp_f1 = 0.992
print(f"\n[TARGET] Beat MLP_Basic F1 = {mlp_f1:.3f}")

print("\n" + "="*70)

# 4. Gradient Boosting Models
models = [
    ('XGBoost', xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6, 
        learning_rate=0.1,
        random_state=42,
        eval_metric='mlogloss',
        n_jobs=-1
    )),
    ('LightGBM', lgb.LGBMClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1, 
        random_state=42,
        n_jobs=-1,
        verbosity=-1
    )),
    ('CatBoost', cb.CatBoostClassifier(
        iterations=100,
        depth=6,
        learning_rate=0.1,
        random_state=42,
        verbose=False
    ))
]

results = []
challenger_found = False

for name, model in models:
    print(f"\n[*] {name}...")
    
    # Train with sample weights
    model.fit(X_train, y_train, sample_weight=sample_weights)
    
    # Predict and evaluate
    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred, average='macro')
    acc = accuracy_score(y_test, y_pred)
    
    # Cross-validation (without sample_weight for simplicity)
    cv = cross_val_score(model, X_train, y_train, cv=5, scoring='f1_macro')
    
    # Compare vs MLP champion
    delta_vs_mlp = f1 - mlp_f1
    vs_mlp_status = "CHALLENGER!" if f1 > mlp_f1 else "not enough"
    
    if f1 > mlp_f1:
        challenger_found = True
    
    results.append({
        'Model': name, 
        'F1': f1, 
        'Acc': acc, 
        'CV': cv.mean(), 
        'Delta_vs_MLP': delta_vs_mlp,
        'Status': vs_mlp_status
    })
    
    print(f"   F1: {f1:.3f} ({delta_vs_mlp:+.3f} vs MLP) | Acc: {acc:.3f} | CV: {cv.mean():.3f}+/-{cv.std():.3f}")
    print(f"   vs MLP_Basic: {vs_mlp_status}")

print("\n" + "="*70)
print("PHASE 2 GRADIENT BOOSTING - FINAL RESULTS")
print("="*70)

# 5. Final comparison
print(f"MLP_Basic Champion: F1 = {mlp_f1:.3f}")
print("\nGradient Boosting Results:")
for result in results:
    status_color = "🏆" if result['Status'] == "CHALLENGER!" else "⚪"
    print(f"{status_color} {result['Model']:10} - F1={result['F1']:.3f} ({result['Delta_vs_MLP']:+.3f}) | {result['Status']}")

# 6. Summary
best_gb = max(results, key=lambda x: x['F1'])
print(f"\nBest Gradient Boosting: {best_gb['Model']} - F1={best_gb['F1']:.3f}")

if challenger_found:
    print("\n🎉 NEW CHALLENGER FOUND! Gradient Boosting beats MLP!")
    print("   → Consider ensemble methods with both approaches")
else:
    print("\n👑 MLP_Basic remains UNDEFEATED champion")  
    print("   → MLP F1=0.992 superior to all Gradient Boosting")
    print("   → Proceed to Phase 3 with MLP_Basic as base model")

print(f"\n[NEXT] Phase 2 Status: MLP=0.992 vs GB_Best={best_gb['F1']:.3f}")
print("[NEXT] Consider: Ensemble methods or declare Phase 2 complete")

print("\n" + "="*70)