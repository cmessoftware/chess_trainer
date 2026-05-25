"""
🔥 Prueba Corregida - Sin None values
"""

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Cargar datos
print("🚀 Cargando datos...")
df = pd.read_parquet('data/export/unified_small_sources.parquet')
print(f"📊 Shape original: {df.shape}")

# Filtrar solo filas con error_label válido
df_valid = df[df['error_label'].notna()]
print(f"📊 Shape después de filtrar None: {df_valid.shape}")

# Verificar error_label
print(f"🎯 Error label values: {df_valid['error_label'].value_counts()}")

# Tomar muestra manejable
sample_size = min(10000, len(df_valid))
df_sample = df_valid.sample(n=sample_size, random_state=42)
print(f"📏 Muestra final: {len(df_sample)}")

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
print(f"🎯 Clases únicas en y: {y.unique()}")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"📊 Train: {len(X_train)}, Test: {len(X_test)}")

# Entrenar
print("🔄 Entrenando...")
model = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Evaluar
print("🔮 Prediciendo...")
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n🎯 RESULTADOS")
print("=" * 30)
print(f"🎯 Accuracy: {accuracy:.4f}")

print(f"\n📈 Reporte detallado:")
print(classification_report(y_test, y_pred))

# Feature importance
print(f"\n🔧 Feature Importance:")
for feature, importance in zip(available_features, model.feature_importances_):
    if importance > 0.05:  # Solo features importantes
        print(f"   {feature}: {importance:.4f}")

print("\n✅ ¡ENTRENAMIENTO EXITOSO!")

# Hacer algunas predicciones de ejemplo
print(f"\n🔮 Ejemplos de predicción:")
sample_predictions = model.predict(X_test[:5])
sample_probabilities = model.predict_proba(X_test[:5])
for i, (pred, probs) in enumerate(zip(sample_predictions, sample_probabilities)):
    confidence = max(probs)
    print(f"   Ejemplo {i+1}: {pred} (confianza: {confidence:.3f})")

if accuracy > 0.5:
    print(f"\n🚀 LISTO PARA MLFLOW!")
    print("   Accuracy > 50% - El modelo básico funciona")
    print("   Puedes proceder con entrenamiento completo")
else:
    print(f"\n⚠️ Accuracy baja - revisar datos")
