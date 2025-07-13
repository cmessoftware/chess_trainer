"""
🔥 Prueba Súper Simple
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# Cargar datos
print("🚀 Cargando datos...")
df = pd.read_parquet('data/export/unified_small_sources.parquet')
print(f"📊 Shape: {df.shape}")

# Verificar error_label
print(f"🎯 Error label values: {df['error_label'].value_counts()}")

# Tomar muestra pequeña
df_sample = df.sample(n=5000, random_state=42)
print(f"📏 Muestra: {len(df_sample)}")

# Features numéricas básicas
numeric_features = ['material_balance', 'material_total', 'num_pieces', 
                   'branching_factor', 'self_mobility', 'opponent_mobility',
                   'score_diff', 'move_number', 'white_elo', 'black_elo']

# Verificar que existen
available_features = [f for f in numeric_features if f in df_sample.columns]
print(f"🔧 Features disponibles: {available_features}")

# Preparar datos
X = df_sample[available_features].fillna(0)
y = df_sample['error_label']

print(f"✅ X shape: {X.shape}, y shape: {y.shape}")

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entrenar
print("🔄 Entrenando...")
model = RandomForestClassifier(n_estimators=10, random_state=42)
model.fit(X_train, y_train)

# Evaluar
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"🎯 Accuracy: {accuracy:.4f}")
print("✅ ¡Funciona!")
