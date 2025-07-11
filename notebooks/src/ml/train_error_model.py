#!/usr/bin/env python3
"""
Script de entrenamiento de modelos de error prediction con MLflow tracking.
Ejemplo práctico para chess_trainer.
"""

import sys
sys.path.append('/chess_trainer/src')

import pandas as pd
import logging
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import mlflow
import mlflow.sklearn

from ml.mlflow_utils import ChessMLflowTracker

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def load_chess_dataset(data_path: str = "/chess_trainer/datasets/export/personal/features.parquet"):
    """
    Cargar y preparar dataset de chess_trainer.
    
    Args:
        data_path: Ruta al dataset parquet
        
    Returns:
        DataFrame limpio y preparado
    """
    try:
        print(f"📊 Cargando dataset desde: {data_path}")
        
        if not Path(data_path).exists():
            print(f"⚠️ Archivo no encontrado: {data_path}")
            print("💡 Rutas alternativas a verificar:")
            print("   - /chess_trainer/datasets/export/personal/features.parquet")
            print("   - /chess_trainer/datasets/export/elite/features.parquet")
            print("   - /chess_trainer/datasets/export/novice/features.parquet")
            return None
        
        df = pd.read_parquet(data_path)
        print(f"✅ Dataset cargado: {len(df)} filas, {len(df.columns)} columnas")
        
        # Mostrar información básica
        print(f"📈 Columnas disponibles: {list(df.columns)}")
        
        if 'error_label' in df.columns:
            error_dist = df['error_label'].value_counts()
            print(f"🎯 Distribución error_label:")
            for error, count in error_dist.items():
                print(f"   - {error}: {count} ({count/len(df)*100:.1f}%)")
        
        return df
        
    except Exception as e:
        print(f"❌ Error cargando dataset: {e}")
        return None

def prepare_features_and_target(df: pd.DataFrame):
    """
    Preparar features y target para entrenamiento.
    
    Args:
        df: DataFrame con datos raw
        
    Returns:
        X, y preparados para ML
    """
    print("🔧 Preparando features y target...")
    
    # Features principales disponibles en chess_trainer
    base_features = [
        'score_diff', 'material_balance', 'branching_factor', 
        'self_mobility', 'opponent_mobility', 'num_pieces'
    ]
    
    # Features adicionales si están disponibles
    additional_features = [
        'material_total', 'has_castling_rights', 'is_repetition',
        'is_low_mobility', 'is_center_controlled', 'is_pawn_endgame',
        'move_number'
    ]
    
    # Seleccionar features que existen en el dataset
    available_features = []
    for feature in base_features + additional_features:
        if feature in df.columns:
            available_features.append(feature)
        else:
            print(f"⚠️ Feature no disponible: {feature}")
    
    print(f"✅ Features seleccionados: {available_features}")
    
    # Verificar que tenemos target
    if 'error_label' not in df.columns:
        print("❌ Column 'error_label' no encontrada")
        print(f"Available columns: {list(df.columns)}")
        return None, None, None
    
    # Filtrar datos válidos (sin NaN en features importantes)
    print("🧹 Limpiando datos...")
    df_clean = df[available_features + ['error_label']].copy()
    
    # Eliminar filas con NaN en features críticos
    critical_features = ['score_diff', 'error_label']
    initial_rows = len(df_clean)
    df_clean = df_clean.dropna(subset=critical_features)
    print(f"📉 Filas eliminadas por NaN críticos: {initial_rows - len(df_clean)}")
    
    # Rellenar NaN en features secundarios con mediana/moda
    for feature in available_features:
        if df_clean[feature].isnull().sum() > 0:
            if df_clean[feature].dtype in ['int64', 'float64']:
                df_clean[feature] = df_clean[feature].fillna(df_clean[feature].median())
            else:
                df_clean[feature] = df_clean[feature].fillna(df_clean[feature].mode()[0] if not df_clean[feature].mode().empty else 'unknown')
    
    # Preparar X e y
    X = df_clean[available_features]
    y = df_clean['error_label']
    
    print(f"✅ Dataset final: {len(X)} muestras, {len(available_features)} features")
    print(f"🎯 Clases target: {sorted(y.unique())}")
    
    return X, y, available_features

def train_chess_error_model():
    """
    Entrenar modelos para predecir error_label con MLflow tracking.
    """
    print("🚀 CHESS TRAINER - Error Prediction Training")
    print("=" * 50)
    
    # Inicializar MLflow
    try:
        tracker = ChessMLflowTracker()
        mlflow.set_experiment("chess_error_prediction")
        print("✅ MLflow configurado")
    except Exception as e:
        print(f"❌ Error configurando MLflow: {e}")
        return False
    
    # Cargar datos
    df = load_chess_dataset()
    if df is None:
        return False
    
    # Preparar features
    X, y, feature_names = prepare_features_and_target(df)
    if X is None:
        return False
    
    # Verificar que tenemos suficientes datos
    if len(X) < 100:
        print(f"⚠️ Pocas muestras para entrenar: {len(X)}")
        print("💡 Necesitas al menos 100 muestras para un entrenamiento confiable")
        return False
    
    # Split datos
    print("📊 Dividiendo dataset...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"📈 Train: {len(X_train)} muestras")
    print(f"📉 Test: {len(X_test)} muestras")
    
    # Modelos a entrenar
    models = {
        'RandomForest': {
            'model': RandomForestClassifier(n_estimators=100, random_state=42),
            'scale_features': False
        },
        'LogisticRegression': {
            'model': LogisticRegression(random_state=42, max_iter=1000),
            'scale_features': True
        }
    }
    
    results = {}
    
    # Entrenar cada modelo
    for model_name, model_config in models.items():
        print(f"\n🤖 Entrenando {model_name}...")
        
        with mlflow.start_run(run_name=f"chess_error_{model_name}"):
            try:
                model = model_config['model']
                
                # Preparar datos (escalar si es necesario)
                X_train_processed = X_train.copy()
                X_test_processed = X_test.copy()
                
                scaler = None
                if model_config['scale_features']:
                    print("🔄 Escalando features...")
                    scaler = StandardScaler()
                    X_train_processed = pd.DataFrame(
                        scaler.fit_transform(X_train_processed),
                        columns=X_train_processed.columns,
                        index=X_train_processed.index
                    )
                    X_test_processed = pd.DataFrame(
                        scaler.transform(X_test_processed),
                        columns=X_test_processed.columns,
                        index=X_test_processed.index
                    )
                
                # Log información del dataset
                tracker.log_chess_dataset_info(df, "personal", "features_parquet")
                
                # Log parámetros del modelo
                tracker.log_chess_hyperparameters(model, model_name, {
                    'features_scaled': model_config['scale_features'],
                    'n_features': len(feature_names),
                    'n_samples_train': len(X_train),
                    'n_samples_test': len(X_test)
                })
                
                # Entrenar modelo
                print("⚡ Entrenando...")
                model.fit(X_train_processed, y_train)
                
                # Predicciones
                y_pred = model.predict(X_test_processed)
                
                # Log métricas
                tracker.log_chess_model_metrics(y_test, y_pred, model_name, feature_names)
                
                # Cross-validation
                print("🔄 Cross-validation...")
                cv_scores = cross_val_score(model, X_train_processed, y_train, cv=5, scoring='accuracy')
                mlflow.log_metric("cv_mean", cv_scores.mean())
                mlflow.log_metric("cv_std", cv_scores.std())
                
                # Feature importance (si disponible)
                feature_importance = tracker.log_feature_importance(model, feature_names, model_name)
                
                # Guardar modelo y scaler
                if scaler:
                    mlflow.sklearn.log_model(
                        scaler, 
                        f"scaler_{model_name.lower()}",
                        registered_model_name=f"ChessScaler_{model_name}"
                    )
                
                mlflow.sklearn.log_model(
                    model, 
                    f"chess_error_{model_name.lower()}",
                    registered_model_name=f"ChessErrorPredictor_{model_name}"
                )
                
                # Guardar resultados
                accuracy = model.score(X_test_processed, y_test)
                results[model_name] = {
                    'accuracy': accuracy,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'feature_importance': feature_importance
                }
                
                print(f"✅ {model_name} completado!")
                print(f"🎯 Accuracy: {accuracy:.3f}")
                print(f"🔄 CV Mean: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
                
                # Mostrar classification report
                print("📊 Classification Report:")
                print(classification_report(y_test, y_pred))
                
            except Exception as e:
                print(f"❌ Error entrenando {model_name}: {e}")
                logger.error(f"Training error for {model_name}: {e}")
    
    # Resumen final
    print("\n📊 RESUMEN FINAL")
    print("=" * 30)
    
    if results:
        best_model = max(results.items(), key=lambda x: x[1]['accuracy'])
        print(f"🏆 Mejor modelo: {best_model[0]}")
        print(f"🎯 Mejor accuracy: {best_model[1]['accuracy']:.3f}")
        
        print("\n📈 Comparación de modelos:")
        for model_name, metrics in results.items():
            print(f"   {model_name}: {metrics['accuracy']:.3f} (CV: {metrics['cv_mean']:.3f})")
        
        print(f"\n🌐 Ver resultados en MLflow UI: http://localhost:5000")
        print("💡 Compara experimentos en la pestaña 'Experiments'")
        
        return True
    else:
        print("❌ No se entrenó ningún modelo exitosamente")
        return False

def train_with_hyperparameter_tuning():
    """
    Ejemplo de optimización de hiperparámetros con MLflow.
    """
    print("\n🔧 HYPERPARAMETER TUNING")
    print("=" * 30)
    
    # Cargar datos
    df = load_chess_dataset()
    if df is None:
        return False
    
    X, y, feature_names = prepare_features_and_target(df)
    if X is None:
        return False
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Grid search para RandomForest
    param_grid = {
        'n_estimators': [50, 100],
        'max_depth': [5, 10, None],
        'min_samples_split': [2, 5]
    }
    
    tracker = ChessMLflowTracker()
    mlflow.set_experiment("chess_error_prediction")
    
    print("🔍 Grid Search para RandomForest...")
    
    best_score = 0
    best_params = None
    
    for n_est in param_grid['n_estimators']:
        for max_d in param_grid['max_depth']:
            for min_split in param_grid['min_samples_split']:
                
                with mlflow.start_run(run_name=f"RF_grid_{n_est}_{max_d}_{min_split}"):
                    # Crear modelo con parámetros específicos
                    model = RandomForestClassifier(
                        n_estimators=n_est,
                        max_depth=max_d,
                        min_samples_split=min_split,
                        random_state=42
                    )
                    
                    # Log parámetros
                    mlflow.log_param("n_estimators", n_est)
                    mlflow.log_param("max_depth", max_d)
                    mlflow.log_param("min_samples_split", min_split)
                    mlflow.log_param("model_type", "RandomForest_GridSearch")
                    
                    # Entrenar y evaluar
                    model.fit(X_train, y_train)
                    accuracy = model.score(X_test, y_test)
                    
                    mlflow.log_metric("accuracy", accuracy)
                    
                    print(f"   n_est={n_est}, max_d={max_d}, min_split={min_split} -> Acc={accuracy:.3f}")
                    
                    if accuracy > best_score:
                        best_score = accuracy
                        best_params = {
                            'n_estimators': n_est,
                            'max_depth': max_d,
                            'min_samples_split': min_split
                        }
    
    print(f"\n🏆 Mejores parámetros: {best_params}")
    print(f"🎯 Mejor score: {best_score:.3f}")
    
    return True

if __name__ == "__main__":
    print("🎮 CHESS TRAINER - ML Training Pipeline")
    print("======================================")
    
    # Verificar MLflow
    try:
        import mlflow
        print(f"✅ MLflow disponible: versión {mlflow.__version__}")
    except ImportError:
        print("❌ MLflow no instalado")
        print("💡 Instalar con: pip install mlflow[extras]")
        sys.exit(1)
    
    # Entrenamiento principal
    success = train_chess_error_model()
    
    if success:
        # Opcional: Hyperparameter tuning
        print("\n" + "="*50)
        user_input = input("🔧 ¿Ejecutar hyperparameter tuning? (y/N): ")
        
        if user_input.lower() in ['y', 'yes', 'sí', 'si']:
            train_with_hyperparameter_tuning()
        
        print("\n🎉 Entrenamiento completado!")
        print("🌐 Revisar resultados: http://localhost:5000")
    else:
        print("\n❌ Entrenamiento falló")
        sys.exit(1)
