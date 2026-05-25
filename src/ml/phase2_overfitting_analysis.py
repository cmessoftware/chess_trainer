#!/usr/bin/env python3
"""
Phase 2 Overfitting Analysis
Analizar si los resultados de 99% accuracy indican overfitting
"""
import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, validation_curve, learning_curve
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, accuracy_score, classification_report
from sklearn.utils.class_weight import compute_sample_weight
from sqlalchemy import create_engine
import matplotlib.pyplot as plt

print("="*70)
print("  PHASE 2 - OVERFITTING ANALYSIS")
print("="*70)

# 1. Cargar datos (mismo query que phase2_mlp_quick.py)
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

# 2. Preparar datos
df = df.fillna(0)
X = df.drop('error_label', axis=1).values.astype(float)
y = df['error_label'].values
X_scaled = StandardScaler().fit_transform(X)

# 3. Análisis de distribución de clases
print("\n[*] Distribución de clases:")
unique, counts = np.unique(y, return_counts=True)
total = len(y)
for label, count in zip(unique, counts):
    pct = count/total*100
    print(f"   {label:12}: {count:6} ({pct:5.1f}%)")

# Calcular baseline accuracy (predecir siempre la clase mayoritaria)
baseline_acc = max(counts) / total
print(f"\n[!] Baseline accuracy (clase mayoritaria): {baseline_acc:.4f} ({baseline_acc*100:.1f}%)")

# 4. Split datos
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)
sample_weights = compute_sample_weight('balanced', y_train)

# 5. Entrenar modelo MLP_Basic (el mejor)
print("\n[*] Entrenando MLP_Basic para análisis de overfitting...")
model = MLPClassifier(hidden_layer_sizes=(100,), max_iter=300, random_state=42)
model.fit(X_train, y_train, sample_weight=sample_weights)

# 6. Evaluar train vs test accuracy
train_pred = model.predict(X_train)
test_pred = model.predict(X_test)

train_acc = accuracy_score(y_train, train_pred)
test_acc = accuracy_score(y_test, test_pred)
train_f1 = f1_score(y_train, train_pred, average='macro')
test_f1 = f1_score(y_test, test_pred, average='macro')

print("\n" + "="*50)
print("  ANÁLISIS OVERFITTING")
print("="*50)
print(f"Train Accuracy: {train_acc:.4f} ({train_acc*100:.1f}%)")
print(f"Test Accuracy:  {test_acc:.4f} ({test_acc*100:.1f}%)")
print(f"Diferencia:     {train_acc - test_acc:.4f}")
print()
print(f"Train F1:       {train_f1:.4f}")
print(f"Test F1:        {test_f1:.4f}")
print(f"Diferencia:     {train_f1 - test_f1:.4f}")

# 7. Evaluar overfitting
gap_acc = train_acc - test_acc
gap_f1 = train_f1 - test_f1

print(f"\n[?] ¿Hay overfitting?")
if gap_acc > 0.05 or gap_f1 > 0.05:
    print(f"   ❌ SÍ - Gap significativo: ACC={gap_acc:.4f}, F1={gap_f1:.4f}")
elif gap_acc > 0.02 or gap_f1 > 0.02:
    print(f"   ⚠️  POSIBLE - Gap moderado: ACC={gap_acc:.4f}, F1={gap_f1:.4f}")
else:
    print(f"   ✅ NO - Gap aceptable: ACC={gap_acc:.4f}, F1={gap_f1:.4f}")

# 8. Análisis por clases (¿está memorizando?)
print(f"\n[*] Classification Report (Test):")
print(classification_report(y_test, test_pred))

# 9. Verificar si es "demasiado fácil" el dataset
print(f"\n[*] ¿Es el dataset 'demasiado fácil'?")
print(f"   Baseline (clase mayoritaria): {baseline_acc*100:.1f}%")
print(f"   Nuestro modelo (test):       {test_acc*100:.1f}%")
improvement = (test_acc - baseline_acc) * 100
print(f"   Mejora sobre baseline:       +{improvement:.1f} puntos")

if improvement < 10:
    print("   ❌ Mejora marginal - posible dataset simple")
elif improvement < 20:
    print("   ⚠️  Mejora moderada")
else:
    print("   ✅ Mejora significativa - modelo está aprendiendo")

print(f"\n[*] Conclusión:")
if test_acc > 0.98 and gap_acc < 0.02 and improvement > 15:
    print("   ✅ ACC alto pero NO overfitting - dataset bien separable")
elif test_acc > 0.98 and gap_acc > 0.05:
    print("   ❌ ACC alto con overfitting - reducir complejidad")
else:
    print("   📊 Análisis case-by-case necesario")

print(f"\n[+] Recomendaciones:")
print(f"   1. Validar en datos completamente nuevos (out-of-time)")
print(f"   2. Verificar que features no tengan 'data leakage'")
print(f"   3. Considerar regularización adicional si gap > 0.05")