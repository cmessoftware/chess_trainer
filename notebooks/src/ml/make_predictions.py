"""
🔮 Script de Predicciones con MLflow
Carga el mejor modelo desde MLflow y hace predicciones
"""

import pandas as pd
import numpy as np
from pathlib import Path
import mlflow
import mlflow.sklearn
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_mlflow():
    """Configurar MLflow para cargar modelos"""
    try:
        mlflow.set_tracking_uri("http://localhost:5000")
        logger.info("✅ MLflow configurado correctamente")
        return True
    except Exception as e:
        logger.warning(f"⚠️ MLflow no disponible: {e}")
        return False

def load_best_model():
    """Cargar el mejor modelo desde MLflow"""
    
    try:
        client = mlflow.tracking.MlflowClient()
        
        # Buscar experimento
        try:
            experiment = mlflow.get_experiment_by_name("chess_error_prediction")
            if not experiment:
                logger.error("❌ No se encontró experimento 'chess_error_prediction'")
                return None
        except Exception:
            logger.error("❌ No se encontró experimento 'chess_error_prediction'")
            return None
        
        # Buscar mejor modelo por accuracy
        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["metrics.accuracy DESC"],
            max_results=1
        )
        
        if len(runs) > 0:
            best_run_id = runs.iloc[0]['run_id']
            model_uri = f"runs:/{best_run_id}/chess_error_classifier"
            
            # Cargar modelo
            model = mlflow.sklearn.load_model(model_uri)
            accuracy = runs.iloc[0]['metrics.accuracy']
            
            logger.info(f"✅ Mejor modelo cargado")
            logger.info(f"   🎯 Accuracy: {accuracy:.4f}")
            logger.info(f"   🆔 Run ID: {best_run_id}")
            
            return model, accuracy, best_run_id
        else:
            logger.error("❌ No se encontraron modelos entrenados")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error cargando modelo: {e}")
        return None

def prepare_prediction_data(data_path):
    """Preparar datos para predicción"""
    
    logger.info(f"📊 Cargando datos para predicción: {data_path}")
    
    # Cargar datos
    df = pd.read_parquet(data_path)
    logger.info(f"📏 Shape: {df.shape}")
    
    # Preparar features (mismas que en entrenamiento)
    exclude_cols = ['error_label', 'pgn', 'game_id', 'move_san', 'fen', 'uci']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Verificar si tiene target (para evaluación)
    has_target = 'error_label' in df.columns
    
    if has_target:
        X = df[feature_cols].copy()
        y = df['error_label'].copy()
        logger.info(f"🎯 Datos con target para evaluación")
    else:
        X = df[feature_cols].copy()
        y = None
        logger.info(f"🔮 Datos sin target - solo predicción")
    
    # Manejo de valores faltantes (mismo que en entrenamiento)
    for col in X.columns:
        if X[col].dtype in ['float64', 'int64']:
            if 'score' in col.lower() or 'diff' in col.lower():
                X[col] = X[col].fillna(0)
            else:
                X[col] = X[col].fillna(X[col].median())
        else:
            X[col] = X[col].fillna(False)
    
    logger.info(f"✅ Datos preparados - {len(feature_cols)} features")
    
    return X, y, df

def make_predictions(model, X, y=None):
    """Hacer predicciones con el modelo"""
    
    logger.info("🔮 Generando predicciones...")
    
    # Predicciones
    predictions = model.predict(X)
    probabilities = model.predict_proba(X)
    
    # Confianza (probabilidad máxima)
    confidence = probabilities.max(axis=1)
    
    # Clases disponibles
    classes = model.classes_
    
    logger.info(f"✅ Predicciones generadas para {len(predictions)} muestras")
    
    # Estadísticas de predicciones
    pred_counts = pd.Series(predictions).value_counts()
    logger.info("📊 Distribución de predicciones:")
    for pred_class, count in pred_counts.items():
        logger.info(f"   {pred_class}: {count} ({count/len(predictions)*100:.1f}%)")
    
    # Estadísticas de confianza
    logger.info(f"🎯 Confianza promedio: {confidence.mean():.3f}")
    logger.info(f"🎯 Confianza mínima: {confidence.min():.3f}")
    logger.info(f"🎯 Confianza máxima: {confidence.max():.3f}")
    
    # Si tenemos target, evaluar
    if y is not None:
        from sklearn.metrics import accuracy_score, classification_report
        
        accuracy = accuracy_score(y, predictions)
        logger.info(f"📈 Accuracy en estos datos: {accuracy:.4f}")
        
        print("\n📊 REPORTE DE EVALUACIÓN")
        print("=" * 50)
        print(f"🎯 Accuracy: {accuracy:.4f}")
        print("\n📈 Reporte detallado:")
        print(classification_report(y, predictions))
    
    return predictions, probabilities, confidence

def analyze_predictions(df_original, predictions, probabilities, confidence):
    """Analizar y presentar las predicciones"""
    
    # Crear DataFrame de resultados
    results_df = df_original.copy()
    results_df['predicted_error'] = predictions
    results_df['prediction_confidence'] = confidence
    
    # Agregar probabilidades por clase
    classes = ['good', 'inaccuracy', 'mistake', 'blunder']  # Ajustar según tus clases
    for i, class_name in enumerate(classes):
        if i < probabilities.shape[1]:
            results_df[f'prob_{class_name}'] = probabilities[:, i]
    
    print("\n🔍 ANÁLISIS DE PREDICCIONES")
    print("=" * 50)
    
    # Ejemplos de alta confianza
    high_conf = results_df[results_df['prediction_confidence'] > 0.9]
    if len(high_conf) > 0:
        print(f"🎯 Predicciones de alta confianza (>90%): {len(high_conf)}")
        
        # Mostrar algunos ejemplos
        sample_high = high_conf.head(3)
        for idx, row in sample_high.iterrows():
            print(f"   Ejemplo {idx}: {row['predicted_error']} (confianza: {row['prediction_confidence']:.3f})")
    
    # Predicciones inciertas
    low_conf = results_df[results_df['prediction_confidence'] < 0.6]
    if len(low_conf) > 0:
        print(f"⚠️ Predicciones inciertas (<60%): {len(low_conf)}")
    
    # Si tenemos moves originales, mostrar ejemplos
    if 'move_san' in results_df.columns:
        print("\n🔍 EJEMPLOS DE PREDICCIONES:")
        sample_moves = results_df.head(5)
        for idx, row in sample_moves.iterrows():
            move = row.get('move_san', 'N/A')
            pred = row['predicted_error']
            conf = row['prediction_confidence']
            print(f"   Jugada: {move} → Predicción: {pred} (confianza: {conf:.3f})")
    
    return results_df

def save_predictions(results_df, output_path="predictions_output.parquet"):
    """Guardar predicciones a archivo"""
    
    results_df.to_parquet(output_path, index=False)
    logger.info(f"💾 Predicciones guardadas en: {output_path}")
    
    return output_path

def main():
    """Función principal de predicciones"""
    
    print("🔮 PREDICCIONES CON MLFLOW")
    print("=" * 50)
    
    # Configurar MLflow
    if not setup_mlflow():
        logger.error("❌ No se puede conectar a MLflow")
        return
    
    # Cargar mejor modelo
    model_info = load_best_model()
    if not model_info:
        logger.error("❌ No se pudo cargar modelo. Entrena uno primero.")
        return
    
    model, accuracy, run_id = model_info
    
    # Buscar datos para predicción
    prediction_paths = [
        Path("data/export/unified_small_sources.parquet"),
        Path("data/export/unified_all_sources.parquet"),
    ]
    
    data_path = None
    for path in prediction_paths:
        if path.exists():
            data_path = path
            break
    
    if not data_path:
        logger.error("❌ No se encontraron datos para predicción")
        return
    
    try:
        # Preparar datos
        X, y, df_original = prepare_prediction_data(data_path)
        
        # Hacer predicciones
        predictions, probabilities, confidence = make_predictions(model, X, y)
        
        # Analizar resultados
        results_df = analyze_predictions(df_original, predictions, probabilities, confidence)
        
        # Guardar resultados
        output_path = save_predictions(results_df)
        
        print("\n🎯 RESUMEN FINAL")
        print("=" * 50)
        print(f"✅ Predicciones completadas")
        print(f"📊 Muestras procesadas: {len(predictions)}")
        print(f"🎯 Confianza promedio: {confidence.mean():.3f}")
        print(f"💾 Resultados guardados en: {output_path}")
        
        # Próximos pasos
        print("\n🚀 PRÓXIMOS PASOS")
        print("=" * 30)
        print("1. 📊 Revisar resultados en el archivo guardado")
        print("2. 🔍 Analizar predicciones de baja confianza")
        print("3. 🎯 Usar modelo para predicciones en tiempo real")
        print("4. 🌐 Revisar experimentos en MLflow: http://localhost:5000")
        
    except Exception as e:
        logger.error(f"❌ Error durante predicciones: {e}")
        raise

if __name__ == "__main__":
    main()
