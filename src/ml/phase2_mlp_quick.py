#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 2 MLP - Quick test sin MLflow"""
import os, sys, pandas as pd, numpy as np
from pathlib import Path
from datetime import datetime
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix
from sklearn.utils.class_weight import compute_sample_weight
from sqlalchemy import create_engine

# Windows encoding fix
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

np.random.seed(42)
print("\n" + "="*70)
print("  PHASE 2 MLP - QUICK TEST")
print("="*70)

# 1. Cargar datos
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

# 2. Preparar datos - manejar valores faltantes
df = df.fillna(0)  # Llenar cualquier NaN restante con 0
X = df.drop('error_label', axis=1).values.astype(float)
y = df['error_label'].values
X_scaled = StandardScaler().fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42, stratify=y)
sample_weights = compute_sample_weight('balanced', y_train)

print(f"[OK] Train: {len(X_train)}, Test: {len(X_test)}")
print("\n[*] Sample weights:")
for label in np.unique(y_train):
    print(f"   {label}: {sample_weights[y_train == label].mean():.2f}")

# 3. Entrenar
phase1_f1 = 0.890
models = [
    ('MLP_Basic', MLPClassifier(hidden_layer_sizes=(100,), max_iter=300, random_state=42)),
    ('MLP_Medium', MLPClassifier(hidden_layer_sizes=(100,50), alpha=0.01, max_iter=300, random_state=42)),
]

print("\n" + "="*70)
results = []
for name, model in models:
    print(f"\n[*] {name}...")
    model.fit(X_train, y_train, sample_weight=sample_weights)
    y_pred = model.predict(X_test)
    f1 = f1_score(y_test, y_pred, average='macro')
    acc = accuracy_score(y_test, y_pred)
    cv = cross_val_score(model, X_train, y_train, cv=5, scoring='f1_macro')
    delta = f1 - phase1_f1
    results.append({'Model': name, 'F1': f1, 'Acc': acc, 'CV': cv.mean(), 'Delta_F1': delta, 'Iters': model.n_iter_})
    print(f"   F1: {f1:.3f} ({delta:+.3f}) | Acc: {acc:.3f} | CV: {cv.mean():.3f}+/-{cv.std():.3f} | Iter: {model.n_iter_}")

print("\n" + "="*70)
print(f"Baseline Phase1: F1 = {phase1_f1:.3f}")
best = max(results, key=lambda x: x['F1'])
print(f"Best: {best['Model']} - F1={best['F1']:.3f} ({best['Delta_F1']:+.3f})")
if best['F1'] > phase1_f1:
    print("[OK] MLP SUPERA baseline!")
else:
    print("[!] MLP NO supera baseline")
print("="*70 + "\n")
