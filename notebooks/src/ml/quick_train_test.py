"""
🎯 Entrenamiento Rápido sin MLflow para Prueba
Version simplificada para validar funcionalidad básica
"""

import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def quick_train():
    """Entrenamiento rápido para validar funcionalidad"""
    
    print("🚀 ENTRENAMIENTO RÁPIDO (SIN MLFLOW)")
    print("=" * 50)
    
    # Cargar dataset pequeño
    dataset_path = Path("data/export/unified_small_sources.parquet")
    
    if not dataset_path.exists():
        logger.error("❌ Dataset no encontrado")
        return
    
    logger.info(f"📊 Cargando: {dataset_path}")
    df = pd.read_parquet(dataset_path)
    
    # Tomar muestra pequeña para prueba rápida
    sample_size = min(10000, len(df))
    df_sample = df.sample(n=sample_size, random_state=42)
    logger.info(f"📏 Muestra: {len(df_sample)} registros")
    
    # Preparar datos
    exclude_cols = ['error_label', 'pgn', 'game_id', 'move_san', 'fen', 'uci']
    feature_cols = [col for col in df_sample.columns if col not in exclude_cols]
    
    # Verificar que tenemos target
    if 'error_label' not in df_sample.columns:
        logger.error("❌ No se encontró columna 'error_label'")
        return
    
    X = df_sample[feature_cols].copy()
    y = df_sample['error_label'].copy()
    
    logger.info(f"🔧 Features: {len(feature_cols)}")
    logger.info(f"🎯 Target classes: {y.nunique()}")
    
    # Rellenar valores faltantes rápidamente
    X = X.fillna(0)
    
    # Verificar distribución del target
    target_dist = y.value_counts()
    logger.info("🎯 Distribución del target:")
    for label, count in target_dist.items():
        logger.info(f"   {label}: {count} ({count/len(y)*100:.1f}%)")
    
    # Split datos
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"📊 Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Modelo simple
    model = RandomForestClassifier(
        n_estimators=50,  # Reducido para velocidad
        max_depth=5,      # Reducido para velocidad
        random_state=42,
        n_jobs=-1
    )
    
    # Entrenar
    logger.info("🔄 Entrenando modelo...")
    model.fit(X_train, y_train)
    
    # Evaluar
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Resultados
    print("\n📊 RESULTADOS")
    print("=" * 30)
    print(f"🎯 Accuracy: {accuracy:.4f}")
    print("\n📈 Reporte por clase:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    feature_importance = dict(zip(feature_cols, model.feature_importances_))
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("\n🔧 Top 10 Features:")
    for i, (feature, importance) in enumerate(top_features, 1):
        print(f"   {i:2}. {feature}: {importance:.4f}")
    
    # Verificar features importantes
    important_features = [f for f, imp in top_features if imp > 0.05]
    logger.info(f"🔍 Features importantes (>5%): {len(important_features)}")
    
    if accuracy > 0.3:  # Umbral básico
        print("\n✅ ENTRENAMIENTO EXITOSO")
        print("🚀 El modelo básico funciona correctamente")
        print("📈 Puedes proceder con MLflow tracking")
    else:
        print("\n⚠️ ACCURACY BAJA")
        print("🔍 Revisar calidad de datos o preprocesamiento")
    
    return model, accuracy

if __name__ == "__main__":
    quick_train()
