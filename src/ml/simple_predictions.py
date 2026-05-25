"""
🔮 Predicciones Simples (Sin MLflow)
Hacer predicciones usando el modelo entrenado localmente
"""

import pandas as pd
import pickle
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_and_save_model():
    """Entrenar modelo y guardarlo localmente"""
    
    logger.info("🎯 Entrenando modelo para predicciones...")
    
    # Cargar datos
    df = pd.read_parquet('data/processed/unified_small_sources.parquet')
    df_valid = df[df['error_label'].notna()]
    
    # Features
    features = [
        'material_balance', 'material_total', 'num_pieces', 
        'branching_factor', 'self_mobility', 'opponent_mobility',
        'score_diff', 'move_number', 'white_elo', 'black_elo'
    ]
    
    X = df_valid[features].fillna(0)
    y = df_valid['error_label']
    
    # Entrenar modelo completo
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X, y)
    
    # Guardar modelo
    model_path = Path("models/chess_error_classifier.pkl")
    model_path.parent.mkdir(exist_ok=True)
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Guardar lista de features
    with open("models/feature_names.pkl", 'wb') as f:
        pickle.dump(features, f)
    
    logger.info(f"✅ Modelo guardado en: {model_path}")
    return model, features

def load_model():
    """Cargar modelo guardado"""
    
    model_path = Path("models/chess_error_classifier.pkl")
    features_path = Path("models/feature_names.pkl")
    
    if not model_path.exists():
        logger.info("🔄 Modelo no encontrado, entrenando nuevo...")
        return train_and_save_model()
    
    logger.info(f"📦 Cargando modelo desde: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    with open(features_path, 'rb') as f:
        features = pickle.load(f)
    
    return model, features

def make_predictions_on_dataset(model, features, dataset_path):
    """Hacer predicciones en un dataset"""
    
    logger.info(f"🔮 Haciendo predicciones en: {dataset_path}")
    
    # Cargar datos
    df = pd.read_parquet(dataset_path)
    logger.info(f"📊 Dataset shape: {df.shape}")
    
    # Preparar features
    X = df[features].fillna(0)
    
    # Hacer predicciones
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    confidence = probabilities.max(axis=1)
    
    # Agregar predicciones al DataFrame
    df_results = df.copy()
    df_results['predicted_error'] = predictions
    df_results['prediction_confidence'] = confidence
    
    # Agregar probabilidades por clase
    classes = model.classes_
    for i, class_name in enumerate(classes):
        df_results[f'prob_{class_name}'] = probabilities[:, i]
    
    logger.info(f"✅ Predicciones completadas para {len(predictions)} muestras")
    
    return df_results

def analyze_predictions(df_results):
    """Analizar resultados de predicciones"""
    
    print("\n🔍 ANÁLISIS DE PREDICCIONES")
    print("=" * 50)
    
    # Distribución de predicciones
    pred_dist = df_results['predicted_error'].value_counts()
    print("📊 Distribución de predicciones:")
    for pred_class, count in pred_dist.items():
        print(f"   {pred_class}: {count} ({count/len(df_results)*100:.1f}%)")
    
    # Estadísticas de confianza
    confidence = df_results['prediction_confidence']
    print("\n🎯 Estadísticas de confianza:")
    print(f"   Promedio: {confidence.mean():.3f}")
    print(f"   Mediana: {confidence.median():.3f}")
    print(f"   Mínimo: {confidence.min():.3f}")
    print(f"   Máximo: {confidence.max():.3f}")
    
    # Predicciones de alta confianza
    high_conf = df_results[df_results['prediction_confidence'] > 0.9]
    print(f"\n✨ Predicciones de alta confianza (>90%): {len(high_conf)} ({len(high_conf)/len(df_results)*100:.1f}%)")
    
    # Predicciones inciertas
    low_conf = df_results[df_results['prediction_confidence'] < 0.6]
    print(f"⚠️  Predicciones inciertas (<60%): {len(low_conf)} ({len(low_conf)/len(df_results)*100:.1f}%)")
    
    # Si tenemos jugadas, mostrar ejemplos
    if 'move_san' in df_results.columns:
        print("\n🔍 Ejemplos de predicciones:")
        
        # Ejemplos de alta confianza
        if len(high_conf) > 0:
            print("   🎯 Alta confianza:")
            for i, (_, row) in enumerate(high_conf.head(3).iterrows()):
                move = row.get('move_san', 'N/A')
                pred = row['predicted_error']
                conf = row['prediction_confidence']
                print(f"      {i+1}. {move} → {pred} (confianza: {conf:.3f})")
        
        # Ejemplos de baja confianza
        if len(low_conf) > 0:
            print("   ⚠️  Baja confianza:")
            for i, (_, row) in enumerate(low_conf.head(2).iterrows()):
                move = row.get('move_san', 'N/A')
                pred = row['predicted_error']
                conf = row['prediction_confidence']
                print(f"      {i+1}. {move} → {pred} (confianza: {conf:.3f})")
    
    # Si tenemos etiquetas reales, evaluar
    if 'error_label' in df_results.columns:
        real_labels = df_results['error_label'].notna()
        if real_labels.sum() > 0:
            df_eval = df_results[real_labels]
            accuracy = accuracy_score(df_eval['error_label'], df_eval['predicted_error'])
            print("\n📈 Evaluación en datos con etiquetas reales:")
            print(f"   🎯 Accuracy: {accuracy:.4f}")
            print(f"   📊 Muestras evaluadas: {len(df_eval)}")

def save_predictions(df_results, output_path="predictions_results.parquet"):
    """Guardar predicciones"""
    
    df_results.to_parquet(output_path, index=False)
    logger.info(f"💾 Predicciones guardadas en: {output_path}")
    
    # También guardar un resumen CSV para fácil visualización
    summary_path = output_path.replace('.parquet', '_summary.csv')
    
    # Crear resumen con columnas clave
    summary_cols = ['move_san', 'predicted_error', 'prediction_confidence']
    
    # Agregar columnas si existen
    if 'error_label' in df_results.columns:
        summary_cols.append('error_label')
    
    # Agregar columnas de jugadas si existen
    for col in ['white_player', 'black_player', 'move_number']:
        if col in df_results.columns:
            summary_cols.append(col)
    
    available_cols = [col for col in summary_cols if col in df_results.columns]
    df_summary = df_results[available_cols].head(1000)  # Primeras 1000 para CSV
    df_summary.to_csv(summary_path, index=False)
    
    logger.info(f"📋 Resumen guardado en: {summary_path}")

def main():
    """Función principal de predicciones"""
    
    print("🔮 PREDICCIONES SIMPLES - CHESS ERROR CLASSIFIER")
    print("=" * 60)
    
    try:
        # Cargar o entrenar modelo
        model, features = load_model()
        
        # Dataset para predicciones
        dataset_path = Path("data/processed/unified_small_sources.parquet")
        
        if not dataset_path.exists():
            logger.error(f"❌ Dataset no encontrado: {dataset_path}")
            return
        
        # Hacer predicciones
        df_results = make_predictions_on_dataset(model, features, dataset_path)
        
        # Analizar resultados
        analyze_predictions(df_results)
        
        # Guardar resultados
        save_predictions(df_results)
        
        print("\n🎯 RESUMEN FINAL")
        print("=" * 30)
        print("✅ Predicciones completadas exitosamente")
        print(f"📊 Total de muestras procesadas: {len(df_results)}")
        print(f"🎯 Confianza promedio: {df_results['prediction_confidence'].mean():.3f}")
        print("💾 Resultados guardados en archivos de salida")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("1. 📊 Revisar archivo predictions_results.parquet")
        print("2. 📋 Ver resumen en predictions_results_summary.csv")
        print("3. 🔍 Analizar predicciones de baja confianza")
        print("4. 🎯 Usar modelo para predicciones en tiempo real")
        
    except Exception as e:
        logger.error(f"❌ Error durante predicciones: {e}")
        raise

if __name__ == "__main__":
    main()
