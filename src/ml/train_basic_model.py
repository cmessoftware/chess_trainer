"""
🎯 Script de Entrenamiento Básico con MLflow
Entrena un modelo de clasificación de errores usando MLflow tracking
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import mlflow
import mlflow.sklearn
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_mlflow():
    """Configurar MLflow tracking"""
    try:
        # Configurar URI (ajustar según tu configuración)
        mlflow.set_tracking_uri("http://localhost:5000")
        mlflow.set_experiment("chess_error_prediction")
        logger.info("✅ MLflow configurado correctamente")
        return True
    except Exception as e:
        logger.warning(f"⚠️ MLflow no disponible, continuando sin tracking: {e}")
        return False

def load_and_prepare_data(dataset_path):
    """Cargar y preparar datos para entrenamiento"""
    
    logger.info(f"📊 Cargando dataset: {dataset_path}")
    
    # Cargar datos
    df = pd.read_parquet(dataset_path)
    logger.info(f"📏 Dataset shape: {df.shape}")
    
    # Verificar columnas requeridas
    if 'error_label' not in df.columns:
        raise ValueError("Dataset debe tener columna 'error_label'")
    
    # Preparar features
    exclude_cols = ['error_label', 'pgn', 'game_id', 'move_san', 'fen', 'uci']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    logger.info(f"🔧 Features disponibles: {len(feature_cols)}")
    
    # Identificar features tácticas
    tactical_features = [col for col in feature_cols 
                        if any(term in col.lower() for term in 
                              ['depth_score', 'threatens_mate', 'forced_move', 'tactical'])]
    
    if tactical_features:
        logger.info(f"⚔️ Features tácticas encontradas: {len(tactical_features)}")
    
    # Preparar datos
    X = df[feature_cols].copy()
    y = df['error_label'].copy()
    
    # Manejo de valores faltantes
    logger.info(f"❓ Missing values antes: {X.isnull().sum().sum()}")
    
    # Rellenar NaN de manera inteligente
    for col in X.columns:
        if X[col].dtype in ['float64', 'int64']:
            # Para columnas numéricas, usar 0 o mediana según el caso
            if 'score' in col.lower() or 'diff' in col.lower():
                X[col] = X[col].fillna(0)  # Diferencias neutras
            else:
                X[col] = X[col].fillna(X[col].median())  # Mediana para otras
        else:
            # Para columnas categóricas
            X[col] = X[col].fillna(False)
    
    logger.info(f"✅ Missing values después: {X.isnull().sum().sum()}")
    
    # Información del target
    target_dist = y.value_counts()
    logger.info("🎯 Distribución del target:")
    for label, count in target_dist.items():
        logger.info(f"   {label}: {count} ({count/len(y)*100:.1f}%)")
    
    return X, y, feature_cols, tactical_features

def train_basic_model(X, y, feature_cols, mlflow_enabled=True):
    """Entrenar modelo básico con tracking MLflow"""
    
    # Split datos
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    logger.info(f"📊 Train samples: {len(X_train)}, Test samples: {len(X_test)}")
    
    # Configurar modelo
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    
    if mlflow_enabled:
        # MLflow tracking
        with mlflow.start_run(run_name="basic_chess_classifier"):
            
            # Log parámetros del dataset
            mlflow.log_param("n_samples", len(X))
            mlflow.log_param("n_features", len(feature_cols))
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
            y_pred_proba = model.predict_proba(X_test)
            
            # Métricas
            accuracy = accuracy_score(y_test, y_pred)
            
            # Log métricas principales
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("n_classes", len(np.unique(y)))
            
            # Reporte de clasificación detallado
            report = classification_report(y_test, y_pred, output_dict=True)
            for label, metrics in report.items():
                if isinstance(metrics, dict):
                    for metric, value in metrics.items():
                        mlflow.log_metric(f"{label}_{metric}", value)
            
            # Feature importance
            feature_importance = dict(zip(feature_cols, model.feature_importances_))
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            
            for i, (feature, importance) in enumerate(top_features):
                mlflow.log_metric(f"top_feature_{i+1}_importance", importance)
                mlflow.log_param(f"top_feature_{i+1}_name", feature)
            
            # Log modelo
            mlflow.sklearn.log_model(
                model, 
                "chess_error_classifier",
                registered_model_name="ChessErrorClassifier"
            )
            
            # Log artefactos adicionales
            
            # Matriz de confusión
            cm = confusion_matrix(y_test, y_pred)
            cm_df = pd.DataFrame(cm, 
                               index=[f"True_{label}" for label in model.classes_],
                               columns=[f"Pred_{label}" for label in model.classes_])
            
            # Guardar como CSV temporal
            cm_path = "confusion_matrix.csv"
            cm_df.to_csv(cm_path)
            mlflow.log_artifact(cm_path)
            
            logger.info(f"✅ Modelo entrenado - Accuracy: {accuracy:.4f}")
            
    else:
        # Entrenar sin MLflow
        logger.info("🔄 Entrenando modelo (sin MLflow tracking)...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"✅ Modelo entrenado - Accuracy: {accuracy:.4f}")
    
    # Reporte detallado
    print("\n📊 REPORTE DETALLADO")
    print("=" * 50)
    print(f"🎯 Accuracy: {accuracy:.4f}")
    print("\n📈 Reporte por clase:")
    print(classification_report(y_test, y_pred))
    
    # Top features
    feature_importance = dict(zip(feature_cols, model.feature_importances_))
    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
    
    print("\n🔧 Top 10 Features más importantes:")
    for i, (feature, importance) in enumerate(top_features, 1):
        print(f"   {i:2}. {feature}: {importance:.4f}")
    
    return model, accuracy, y_test, y_pred

def main():
    """Función principal"""
    
    print("🚀 ENTRENAMIENTO BÁSICO CON MLFLOW")
    print("=" * 50)
    
    # Configurar MLflow
    mlflow_enabled = setup_mlflow()
    
    # Buscar dataset
    dataset_paths = [
        Path("data/export/unified_all_sources.parquet"),
        Path("data/export/unified_small_sources.parquet"),
    ]
    
    dataset_path = None
    for path in dataset_paths:
        if path.exists():
            dataset_path = path
            break
    
    if not dataset_path:
        logger.error("❌ No se encontró dataset. Ejecuta primero el pipeline de datos.")
        return
    
    try:
        # Cargar y preparar datos
        X, y, feature_cols, tactical_features = load_and_prepare_data(dataset_path)
        
        # Entrenar modelo
        model, accuracy, y_test, y_pred = train_basic_model(
            X, y, feature_cols, mlflow_enabled
        )
        
        # Recomendaciones
        print("\n🎯 PRÓXIMOS PASOS RECOMENDADOS")
        print("=" * 50)
        print("1. 🌐 Revisar resultados en MLflow UI: http://localhost:5000")
        print("2. 📈 Ejecutar comparación por fuentes: python src/ml/compare_sources.py")
        print("3. ⚙️ Optimizar hiperparámetros: python src/ml/hyperparameter_tuning.py")
        
        if tactical_features:
            print("4. ⚔️ Experimento táctico: python src/ml/tactical_experiment.py")
        
        print("5. 🔮 Hacer predicciones: python src/ml/make_predictions.py")
        
    except Exception as e:
        logger.error(f"❌ Error durante el entrenamiento: {e}")
        raise

if __name__ == "__main__":
    main()
