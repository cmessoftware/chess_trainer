"""
🎯 Entrenamiento Optimizado con MLflow
Version que funciona con los datos reales disponibles
"""

import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import mlflow
import mlflow.sklearn
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_mlflow():
    """Configurar MLflow tracking"""
    try:
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("chess_error_prediction")
        logger.info("✅ MLflow configurado correctamente")
        return True
    except Exception as e:
        logger.warning(f"⚠️ MLflow no disponible: {e}")
        return False

def load_and_prepare_data():
    """Cargar y preparar datos optimizados"""
    
    # Cargar dataset
    dataset_path = Path("data/export/unified_small_sources.parquet")
    logger.info(f"📊 Cargando: {dataset_path}")
    
    df = pd.read_parquet(dataset_path)
    logger.info(f"📏 Shape original: {df.shape}")
    
    # Filtrar solo filas con error_label válido
    df_valid = df[df['error_label'].notna()]
    logger.info(f"📏 Shape con labels válidos: {df_valid.shape}")
    
    # Tomar muestra manejable para demo
    sample_size = min(15000, len(df_valid))
    df_sample = df_valid.sample(n=sample_size, random_state=42)
    logger.info(f"📏 Muestra final: {len(df_sample)}")
    
    # Features disponibles
    numeric_features = [
        'material_balance', 'material_total', 'num_pieces', 
        'branching_factor', 'self_mobility', 'opponent_mobility',
        'score_diff', 'move_number', 'white_elo', 'black_elo'
    ]
    
    # Verificar features disponibles
    available_features = [f for f in numeric_features if f in df_sample.columns]
    logger.info(f"🔧 Features disponibles: {len(available_features)}")
    
    # Preparar datos
    X = df_sample[available_features].fillna(0)
    y = df_sample['error_label']
    
    # Información del target
    target_dist = y.value_counts()
    logger.info("🎯 Distribución del target:")
    for label, count in target_dist.items():
        logger.info(f"   {label}: {count} ({count/len(y)*100:.1f}%)")
    
    return X, y, available_features

def train_with_mlflow(X, y, feature_names, mlflow_enabled=True):
    """Entrenar modelo con MLflow tracking"""
    
    # Split datos
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"📊 Train: {len(X_train)}, Test: {len(X_test)}")
    
    # Configurar modelo
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    if mlflow_enabled:
        # MLflow tracking
        with mlflow.start_run(run_name="optimized_chess_classifier"):
            
            # Log parámetros del dataset
            mlflow.log_param("dataset_source", "unified_small_sources")
            mlflow.log_param("n_samples", len(X))
            mlflow.log_param("n_features", len(feature_names))
            mlflow.log_param("target_classes", y.nunique())
            mlflow.log_param("train_samples", len(X_train))
            mlflow.log_param("test_samples", len(X_test))
            
            # Log parámetros del modelo
            mlflow.log_params(model.get_params())
            
            # Entrenar
            logger.info("🔄 Entrenando modelo...")
            model.fit(X_train, y_train)
            
            # Predicciones
            y_pred = model.predict(X_test)
            
            # Métricas principales
            accuracy = accuracy_score(y_test, y_pred)
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("n_classes", len(y.unique()))
            
            # Reporte de clasificación detallado
            report = classification_report(y_test, y_pred, output_dict=True)
            for label, metrics in report.items():
                if isinstance(metrics, dict):
                    for metric, value in metrics.items():
                        mlflow.log_metric(f"{label}_{metric}", value)
            
            # Feature importance
            feature_importance = dict(zip(feature_names, model.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
            
            # Log top 5 features
            for i, (feature, importance) in enumerate(top_features[:5]):
                mlflow.log_metric(f"top_feature_{i+1}_importance", importance)
                mlflow.log_param(f"top_feature_{i+1}_name", feature)
            
            # Log modelo
            mlflow.sklearn.log_model(
                model, 
                "chess_error_classifier",
                registered_model_name="ChessErrorClassifier"
            )
            
            # Log información adicional
            mlflow.log_text(
                classification_report(y_test, y_pred), 
                "classification_report.txt"
            )
            
            logger.info(f"✅ Modelo registrado en MLflow - Accuracy: {accuracy:.4f}")
    
    else:
        # Entrenar sin MLflow
        logger.info("🔄 Entrenando modelo (sin MLflow)...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"✅ Modelo entrenado - Accuracy: {accuracy:.4f}")
    
    # Reporte detallado en consola
    print("\n📊 REPORTE DETALLADO")
    print("=" * 50)
    print(f"🎯 Accuracy: {accuracy:.4f}")
    print("\n📈 Reporte por clase:")
    print(classification_report(y_test, y_pred))
    
    # Top features
    feature_importance = dict(zip(feature_names, model.feature_importances_))
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    print("\n🔧 Top 5 Features más importantes:")
    for i, (feature, importance) in enumerate(top_features[:5], 1):
        print(f"   {i}. {feature}: {importance:.4f}")
    
    return model, accuracy

def main():
    """Función principal optimizada"""
    
    print("🚀 ENTRENAMIENTO OPTIMIZADO CON MLFLOW")
    print("=" * 50)
    
    # Configurar MLflow
    mlflow_enabled = setup_mlflow()
    
    try:
        # Cargar y preparar datos
        X, y, feature_names = load_and_prepare_data()
        
        # Entrenar modelo
        model, accuracy = train_with_mlflow(X, y, feature_names, mlflow_enabled)
        
        # Recomendaciones finales
        print("\n🎯 PRÓXIMOS PASOS")
        print("=" * 30)
        
        if mlflow_enabled:
            print("1. 🌐 Revisar MLflow UI: http://localhost:5000")
            print("2. 📊 Comparar con otros experimentos")
            print("3. 🔮 Hacer predicciones: python src/ml/make_predictions.py")
        else:
            print("1. 🔧 Iniciar MLflow para tracking completo")
            print("2. 🔮 Usar modelo para predicciones locales")
        
        print("4. ⚙️ Optimizar hiperparámetros si es necesario")
        print("5. 🎲 Probar con diferentes datasets")
        
        if accuracy > 0.8:
            print(f"\n🎉 ¡EXCELENTE RENDIMIENTO!")
            print(f"   Accuracy {accuracy:.4f} > 80% - Modelo listo para producción")
        elif accuracy > 0.6:
            print(f"\n✅ Buen rendimiento")
            print(f"   Accuracy {accuracy:.4f} - Considera optimización")
        else:
            print(f"\n⚠️ Rendimiento mejorable")
            print(f"   Accuracy {accuracy:.4f} - Revisar features o datos")
        
    except Exception as e:
        logger.error(f"❌ Error durante el entrenamiento: {e}")
        raise

if __name__ == "__main__":
    main()
