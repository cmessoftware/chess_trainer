# 🚀 GUÍA COMPLETA MLflow para Chess Trainer

## 📋 ÍNDICE

1. [🏁 Setup Inicial](#-setup-inicial)
2. [🔄 Iniciando MLflow](#-iniciando-mlflow)
3. [📊 Carga de Datasets](#-carga-de-datasets)
4. [🎯 Entrenamiento con MLflow](#-entrenamiento-con-mlflow)
5. [🔮 Predicciones y Registro](#-predicciones-y-registro)
6. [📈 Monitoreo y Evaluación](#-monitoreo-y-evaluación)
7. [🛠️ Troubleshooting](#️-troubleshooting)
8. [🎮 Scripts Automatizados](#-scripts-automatizados)

---

## 🏁 SETUP INICIAL

### Prerequisitos
```bash
# Verificar Docker
docker --version
docker-compose --version

# Verificar Python environment
python --version
pip list | grep mlflow
```

### 1. Configuración de Servicios

```bash
# Directorio base
cd c:\Users\sergiosal\source\repos\chess_trainer

# Iniciar servicios base (PostgreSQL)
docker-compose up -d postgres

# Esperar que PostgreSQL arranque
timeout 10

# Iniciar MLflow
docker-compose up -d mlflow

# Verificar servicios
docker-compose ps
```

### 2. Verificar Conectividad

```bash
# Verificar MLflow UI
curl http://localhost:5000/health 2>/dev/null || echo "MLflow no disponible"

# Si no funciona, reiniciar
docker-compose restart mlflow
```

### 3. Estructura de Directorios

```
chess_trainer/
├── src/ml/
│   ├── mlflow_complete_guide.py      # 🆕 Guía unificada
│   ├── mlflow_utils.py               # Utilidades MLflow
│   └── experiments/                  # Experimentos organizados
├── models/                           # Modelos entrenados
├── data/
│   ├── export/                       # Datasets procesados
│   └── mlflow_artifacts/             # Artefactos MLflow
└── mlruns/                          # Tracking local (backup)
```

---

## 🔄 INICIANDO MLflow

### Configuración Básica

```python
import mlflow
import mlflow.sklearn
import os
from pathlib import Path

# Configurar MLflow
MLFLOW_TRACKING_URI = "http://localhost:5000"
EXPERIMENT_NAME = "chess_error_prediction"

# Setup
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

# Crear experimento si no existe
try:
    mlflow.create_experiment(EXPERIMENT_NAME)
    print(f"✅ Experimento '{EXPERIMENT_NAME}' creado")
except mlflow.exceptions.MlflowException:
    print(f"✅ Usando experimento existente: '{EXPERIMENT_NAME}'")

mlflow.set_experiment(EXPERIMENT_NAME)
```

### Verificación de Conexión

```python
def verify_mlflow_connection():
    """Verificar conexión con MLflow"""
    try:
        # Test básico
        experiments = mlflow.search_experiments()
        print(f"✅ MLflow conectado - {len(experiments)} experimentos")
        
        # Test de escritura
        with mlflow.start_run(run_name="connection_test"):
            mlflow.log_param("test_param", "test_value")
            mlflow.log_metric("test_metric", 1.0)
            run_id = mlflow.active_run().info.run_id
            print(f"✅ Test run creado: {run_id}")
        
        return True
    except Exception as e:
        print(f"❌ Error MLflow: {e}")
        return False

# Ejecutar verificación
verify_mlflow_connection()
```

---

## 📊 CARGA DE DATASETS

### 1. Ubicación de Datasets

```python
import pandas as pd
from pathlib import Path

def find_dataset():
    """Encontrar dataset principal"""
    
    possible_paths = [
        "data/export/unified_small_sources.parquet",
        "data/processed/unified_small_sources.parquet",
        "data/unified_small_sources.parquet"
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    raise FileNotFoundError(f"Dataset no encontrado en: {possible_paths}")

# Encontrar y cargar dataset
dataset_path = find_dataset()
print(f"📂 Dataset encontrado: {dataset_path}")
```

### 2. Carga y Exploración Inicial

```python
def load_and_explore_dataset(dataset_path):
    """Cargar dataset y exploración básica con MLflow logging"""
    
    with mlflow.start_run(run_name="dataset_exploration"):
        
        # Cargar dataset
        df = pd.read_parquet(dataset_path)
        
        # Log información básica
        mlflow.log_param("dataset_path", dataset_path)
        mlflow.log_metric("total_rows", len(df))
        mlflow.log_metric("total_columns", len(df.columns))
        
        # Información sobre error_label (target)
        if 'error_label' in df.columns:
            df_valid = df[df['error_label'].notna()]
            mlflow.log_metric("valid_labels", len(df_valid))
            mlflow.log_metric("valid_percentage", len(df_valid)/len(df)*100)
            
            # Distribución de clases
            class_dist = df_valid['error_label'].value_counts()
            for class_name, count in class_dist.items():
                mlflow.log_metric(f"class_count_{class_name}", count)
                mlflow.log_metric(f"class_pct_{class_name}", count/len(df_valid)*100)
            
            print(f"📊 Dataset shape: {df.shape}")
            print(f"📊 Valid labels: {len(df_valid)} ({len(df_valid)/len(df)*100:.1f}%)")
            print(f"📊 Class distribution:")
            for class_name, count in class_dist.items():
                print(f"   • {class_name}: {count} ({count/len(df_valid)*100:.1f}%)")
        
        # Log columnas disponibles
        mlflow.log_param("available_columns", list(df.columns))
        
        return df

# Cargar dataset
df = load_and_explore_dataset(dataset_path)
```

### 3. Preparación de Features

```python
def prepare_features_for_training(df):
    """Preparar features para entrenamiento"""
    
    with mlflow.start_run(run_name="feature_preparation"):
        
        # Features definidos
        features = [
            'material_balance', 'material_total', 'num_pieces', 
            'branching_factor', 'self_mobility', 'opponent_mobility',
            'score_diff', 'move_number', 'white_elo', 'black_elo'
        ]
        
        # Filtrar datos válidos
        df_valid = df[df['error_label'].notna()].copy()
        
        # Verificar features disponibles
        available_features = [f for f in features if f in df_valid.columns]
        missing_features = [f for f in features if f not in df_valid.columns]
        
        mlflow.log_param("requested_features", features)
        mlflow.log_param("available_features", available_features)
        mlflow.log_param("missing_features", missing_features)
        mlflow.log_metric("feature_coverage", len(available_features)/len(features)*100)
        
        if missing_features:
            print(f"⚠️  Features faltantes: {missing_features}")
        
        # Preparar X e y
        X = df_valid[available_features].fillna(0)
        y = df_valid['error_label']
        
        # Log estadísticas finales
        mlflow.log_metric("final_samples", len(X))
        mlflow.log_metric("final_features", len(available_features))
        
        # Estadísticas de features
        for feature in available_features:
            mlflow.log_metric(f"feature_mean_{feature}", X[feature].mean())
            mlflow.log_metric(f"feature_std_{feature}", X[feature].std())
            mlflow.log_metric(f"feature_null_pct_{feature}", X[feature].isnull().sum()/len(X)*100)
        
        print(f"✅ Features preparados: {X.shape}")
        print(f"✅ Features disponibles: {len(available_features)}/{len(features)}")
        
        return X, y, available_features

# Preparar features
X, y, features = prepare_features_for_training(df)
```

---

## 🎯 ENTRENAMIENTO CON MLflow

### 1. Entrenamiento Básico

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import numpy as np

def train_model_with_mlflow(X, y, features):
    """Entrenamiento completo con MLflow tracking"""
    
    with mlflow.start_run(run_name="chess_error_classification_training"):
        
        # Log información del experimento
        mlflow.log_param("algorithm", "RandomForest")
        mlflow.log_param("features_used", features)
        mlflow.log_param("total_samples", len(X))
        
        # Split de datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        mlflow.log_param("train_size", len(X_train))
        mlflow.log_param("test_size", len(X_test))
        mlflow.log_param("test_ratio", 0.2)
        mlflow.log_param("random_state", 42)
        
        # Parámetros del modelo
        model_params = {
            'n_estimators': 100,
            'random_state': 42,
            'n_jobs': -1,
            'max_depth': None,
            'min_samples_split': 2,
            'min_samples_leaf': 1
        }
        
        # Log parámetros del modelo
        for param, value in model_params.items():
            mlflow.log_param(f"model_{param}", value)
        
        # Entrenar modelo
        print("🎯 Entrenando RandomForest...")
        import time
        start_time = time.time()
        
        model = RandomForestClassifier(**model_params)
        model.fit(X_train, y_train)
        
        training_time = time.time() - start_time
        mlflow.log_metric("training_time_seconds", training_time)
        
        # Predicciones
        y_train_pred = model.predict(X_train)
        y_test_pred = model.predict(X_test)
        
        # Métricas de accuracy
        train_accuracy = accuracy_score(y_train, y_train_pred)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        
        mlflow.log_metric("train_accuracy", train_accuracy)
        mlflow.log_metric("test_accuracy", test_accuracy)
        mlflow.log_metric("accuracy_gap", train_accuracy - test_accuracy)
        
        # Reporte detallado por clase
        report = classification_report(y_test, y_test_pred, output_dict=True)
        
        for class_name in ['good', 'inaccuracy', 'mistake', 'blunder']:
            if class_name in report:
                mlflow.log_metric(f"precision_{class_name}", report[class_name]['precision'])
                mlflow.log_metric(f"recall_{class_name}", report[class_name]['recall'])
                mlflow.log_metric(f"f1_{class_name}", report[class_name]['f1-score'])
        
        # Métricas agregadas
        mlflow.log_metric("macro_avg_precision", report['macro avg']['precision'])
        mlflow.log_metric("macro_avg_recall", report['macro avg']['recall'])
        mlflow.log_metric("macro_avg_f1", report['macro avg']['f1-score'])
        mlflow.log_metric("weighted_avg_f1", report['weighted avg']['f1-score'])
        
        # Feature importance
        feature_importance = dict(zip(features, model.feature_importances_))
        
        for feature, importance in feature_importance.items():
            mlflow.log_metric(f"importance_{feature}", importance)
        
        # Feature más importante
        most_important_feature = max(feature_importance, key=feature_importance.get)
        mlflow.log_param("most_important_feature", most_important_feature)
        mlflow.log_metric("most_important_score", feature_importance[most_important_feature])
        
        # Guardar modelo en MLflow
        mlflow.sklearn.log_model(
            model, 
            "model",
            registered_model_name="chess_error_classifier",
            input_example=X_test.head(5),
            signature=mlflow.models.infer_signature(X_test, y_test_pred)
        )
        
        # Guardar artefactos adicionales
        
        # 1. Lista de features
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('\n'.join(features))
            features_file = f.name
        
        mlflow.log_artifact(features_file, "model_artifacts")
        os.unlink(features_file)
        
        # 2. Reporte de clasificación
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(classification_report(y_test, y_test_pred))
            report_file = f.name
        
        mlflow.log_artifact(report_file, "evaluation")
        os.unlink(report_file)
        
        # 3. Matriz de confusión
        cm = confusion_matrix(y_test, y_test_pred)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            np.savetxt(f.name, cm, delimiter=',', fmt='%d')
            cm_file = f.name
        
        mlflow.log_artifact(cm_file, "evaluation")
        os.unlink(cm_file)
        
        # Log información final
        run_id = mlflow.active_run().info.run_id
        
        print(f"✅ Entrenamiento completado")
        print(f"🎯 Test Accuracy: {test_accuracy:.4f}")
        print(f"⭐ Feature más importante: {most_important_feature} ({feature_importance[most_important_feature]:.4f})")
        print(f"📋 MLflow Run ID: {run_id}")
        
        return model, run_id, test_accuracy

# Entrenar modelo
model, run_id, accuracy = train_model_with_mlflow(X, y, features)
```

### 2. Entrenamiento con Hyperparameter Tuning

```python
from sklearn.model_selection import GridSearchCV

def train_with_hyperparameter_tuning(X, y, features):
    """Entrenamiento con optimización de hiperparámetros"""
    
    with mlflow.start_run(run_name="hyperparameter_tuning"):
        
        # Split de datos
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Grid de parámetros
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [10, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        mlflow.log_param("param_grid", str(param_grid))
        mlflow.log_param("cv_folds", 3)
        
        # Grid Search
        print("🔍 Ejecutando Grid Search...")
        rf = RandomForestClassifier(random_state=42, n_jobs=-1)
        
        grid_search = GridSearchCV(
            rf, 
            param_grid, 
            cv=3, 
            scoring='f1_weighted',
            n_jobs=-1,
            verbose=1
        )
        
        import time
        start_time = time.time()
        grid_search.fit(X_train, y_train)
        tuning_time = time.time() - start_time
        
        mlflow.log_metric("tuning_time_seconds", tuning_time)
        
        # Mejores parámetros
        best_params = grid_search.best_params_
        for param, value in best_params.items():
            mlflow.log_param(f"best_{param}", value)
        
        mlflow.log_metric("best_cv_score", grid_search.best_score_)
        
        # Modelo final
        best_model = grid_search.best_estimator_
        
        # Evaluación en test
        y_test_pred = best_model.predict(X_test)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        
        mlflow.log_metric("final_test_accuracy", test_accuracy)
        
        # Guardar modelo optimizado
        mlflow.sklearn.log_model(
            best_model,
            "tuned_model",
            registered_model_name="chess_error_classifier_tuned"
        )
        
        run_id = mlflow.active_run().info.run_id
        
        print(f"✅ Tuning completado - Run ID: {run_id}")
        print(f"🎯 Best CV Score: {grid_search.best_score_:.4f}")
        print(f"🎯 Test Accuracy: {test_accuracy:.4f}")
        print(f"⚙️ Best params: {best_params}")
        
        return best_model, run_id

# Ejecutar tuning (opcional)
# tuned_model, tuning_run_id = train_with_hyperparameter_tuning(X, y, features)
```

---

## 🔮 PREDICCIONES Y REGISTRO

### 1. Predicciones con Modelo MLflow

```python
def make_predictions_with_mlflow_model(run_id=None, model_name=None):
    """Hacer predicciones usando modelo de MLflow"""
    
    with mlflow.start_run(run_name="model_predictions"):
        
        # Cargar modelo
        if run_id:
            model_uri = f"runs:/{run_id}/model"
            mlflow.log_param("model_source", f"run_id:{run_id}")
        elif model_name:
            model_uri = f"models:/{model_name}/latest"
            mlflow.log_param("model_source", f"registered_model:{model_name}")
        else:
            model_uri = "models:/chess_error_classifier/latest"
            mlflow.log_param("model_source", "latest_registered")
        
        print(f"📦 Cargando modelo desde: {model_uri}")
        
        try:
            loaded_model = mlflow.sklearn.load_model(model_uri)
            mlflow.log_param("model_loaded_successfully", True)
        except Exception as e:
            print(f"❌ Error cargando modelo: {e}")
            mlflow.log_param("model_load_error", str(e))
            return None
        
        # Cargar datos para predicción
        X, y, features = prepare_features_for_training(df)
        
        mlflow.log_param("prediction_samples", len(X))
        
        # Hacer predicciones
        print("🔮 Generando predicciones...")
        start_time = time.time()
        
        predictions = loaded_model.predict(X)
        probabilities = loaded_model.predict_proba(X)
        
        prediction_time = time.time() - start_time
        mlflow.log_metric("prediction_time_seconds", prediction_time)
        mlflow.log_metric("predictions_per_second", len(X) / prediction_time)
        
        # Estadísticas de predicciones
        pred_series = pd.Series(predictions)
        pred_dist = pred_series.value_counts()
        
        for class_name, count in pred_dist.items():
            mlflow.log_metric(f"predicted_count_{class_name}", count)
            mlflow.log_metric(f"predicted_pct_{class_name}", count/len(predictions)*100)
        
        # Estadísticas de confianza
        max_probs = probabilities.max(axis=1)
        
        confidence_stats = {
            "mean_confidence": max_probs.mean(),
            "median_confidence": np.median(max_probs),
            "min_confidence": max_probs.min(),
            "max_confidence": max_probs.max(),
            "high_confidence_count": (max_probs > 0.9).sum(),
            "low_confidence_count": (max_probs < 0.6).sum(),
        }
        
        for metric, value in confidence_stats.items():
            mlflow.log_metric(metric, value)
        
        # Crear DataFrame de resultados
        df_results = df[df['error_label'].notna()].copy()
        df_results['predicted_error'] = predictions
        df_results['prediction_confidence'] = max_probs
        
        # Agregar probabilidades por clase
        classes = loaded_model.classes_
        for i, class_name in enumerate(classes):
            df_results[f'prob_{class_name}'] = probabilities[:, i]
        
        # Guardar resultados
        output_path = "predictions_results_mlflow.parquet"
        df_results.to_parquet(output_path, index=False)
        mlflow.log_artifact(output_path, "predictions")
        
        # Resumen CSV
        summary_path = "predictions_summary_mlflow.csv"
        summary_cols = ['move_san', 'predicted_error', 'prediction_confidence']
        if 'error_label' in df_results.columns:
            summary_cols.append('error_label')
        
        available_cols = [col for col in summary_cols if col in df_results.columns]
        df_summary = df_results[available_cols].head(1000)
        df_summary.to_csv(summary_path, index=False)
        mlflow.log_artifact(summary_path, "predictions")
        
        # Log información final
        prediction_run_id = mlflow.active_run().info.run_id
        
        print(f"✅ Predicciones completadas - Run ID: {prediction_run_id}")
        print(f"📊 {len(predictions)} predicciones generadas")
        print(f"🎯 Confianza promedio: {confidence_stats['mean_confidence']:.3f}")
        print(f"💾 Resultados guardados en: {output_path}")
        
        return df_results, prediction_run_id

# Hacer predicciones
if 'run_id' in locals():
    results, pred_run_id = make_predictions_with_mlflow_model(run_id=run_id)
```

### 2. Evaluación en Datos Reales

```python
def evaluate_model_performance(df_results):
    """Evaluar rendimiento del modelo en datos reales"""
    
    with mlflow.start_run(run_name="model_evaluation"):
        
        # Filtrar datos con etiquetas reales
        df_eval = df_results[df_results['error_label'].notna()]
        
        if len(df_eval) == 0:
            print("⚠️  No hay datos con etiquetas reales para evaluar")
            return
        
        mlflow.log_metric("evaluation_samples", len(df_eval))
        
        # Métricas de evaluación
        y_true = df_eval['error_label']
        y_pred = df_eval['predicted_error']
        
        accuracy = accuracy_score(y_true, y_pred)
        mlflow.log_metric("real_data_accuracy", accuracy)
        
        # Reporte por clase
        report = classification_report(y_true, y_pred, output_dict=True)
        
        for class_name in ['good', 'inaccuracy', 'mistake', 'blunder']:
            if class_name in report:
                mlflow.log_metric(f"real_precision_{class_name}", report[class_name]['precision'])
                mlflow.log_metric(f"real_recall_{class_name}", report[class_name]['recall'])
                mlflow.log_metric(f"real_f1_{class_name}", report[class_name]['f1-score'])
        
        # Análisis de confianza vs accuracy
        confidence = df_eval['prediction_confidence']
        
        # Accuracy por rangos de confianza
        high_conf = df_eval[confidence > 0.9]
        if len(high_conf) > 0:
            high_conf_acc = accuracy_score(high_conf['error_label'], high_conf['predicted_error'])
            mlflow.log_metric("high_confidence_accuracy", high_conf_acc)
            mlflow.log_metric("high_confidence_samples", len(high_conf))
        
        medium_conf = df_eval[(confidence > 0.7) & (confidence <= 0.9)]
        if len(medium_conf) > 0:
            medium_conf_acc = accuracy_score(medium_conf['error_label'], medium_conf['predicted_error'])
            mlflow.log_metric("medium_confidence_accuracy", medium_conf_acc)
            mlflow.log_metric("medium_confidence_samples", len(medium_conf))
        
        low_conf = df_eval[confidence <= 0.7]
        if len(low_conf) > 0:
            low_conf_acc = accuracy_score(low_conf['error_label'], low_conf['predicted_error'])
            mlflow.log_metric("low_confidence_accuracy", low_conf_acc)
            mlflow.log_metric("low_confidence_samples", len(low_conf))
        
        print(f"✅ Evaluación completada")
        print(f"🎯 Accuracy en datos reales: {accuracy:.4f}")
        print(f"📊 Muestras evaluadas: {len(df_eval)}")

# Evaluar si tenemos resultados
if 'results' in locals():
    evaluate_model_performance(results)
```

---

## 📈 MONITOREO Y EVALUACIÓN

### 1. Comparación de Experimentos

```python
def compare_experiments():
    """Comparar experimentos en MLflow"""
    
    # Buscar experimentos
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    
    if experiment is None:
        print("❌ Experimento no encontrado")
        return
    
    # Obtener runs
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["start_time DESC"],
        max_results=10
    )
    
    if len(runs) == 0:
        print("❌ No hay runs en el experimento")
        return
    
    print(f"📊 COMPARACIÓN DE EXPERIMENTOS")
    print("=" * 60)
    
    # Mostrar métricas clave
    key_metrics = ['test_accuracy', 'macro_avg_f1', 'training_time_seconds']
    
    for metric in key_metrics:
        if metric in runs.columns:
            print(f"\n🎯 {metric.upper()}:")
            top_runs = runs.nlargest(3, metric) if 'accuracy' in metric or 'f1' in metric else runs.nsmallest(3, metric)
            
            for idx, run in top_runs.iterrows():
                run_name = run.get('tags.mlflow.runName', 'N/A')
                value = run[metric] if not pd.isna(run[metric]) else 'N/A'
                print(f"   • {run_name}: {value}")
    
    # Mejores runs por métrica
    print(f"\n🏆 MEJORES RUNS:")
    
    if 'test_accuracy' in runs.columns:
        best_accuracy = runs.loc[runs['test_accuracy'].idxmax()]
        print(f"   🎯 Mejor Accuracy: {best_accuracy.get('tags.mlflow.runName', 'N/A')} ({best_accuracy['test_accuracy']:.4f})")
    
    if 'macro_avg_f1' in runs.columns:
        best_f1 = runs.loc[runs['macro_avg_f1'].idxmax()]
        print(f"   📊 Mejor F1: {best_f1.get('tags.mlflow.runName', 'N/A')} ({best_f1['macro_avg_f1']:.4f})")
    
    return runs

# Comparar experimentos
comparison_df = compare_experiments()
```

### 2. Análisis de Feature Importance

```python
def analyze_feature_importance():
    """Analizar importancia de features across runs"""
    
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    runs = mlflow.search_runs(experiment_ids=[experiment.experiment_id])
    
    # Filtrar runs con feature importance
    importance_cols = [col for col in runs.columns if col.startswith('metrics.importance_')]
    
    if len(importance_cols) == 0:
        print("❌ No hay datos de feature importance")
        return
    
    print(f"📊 ANÁLISIS DE FEATURE IMPORTANCE")
    print("=" * 50)
    
    # Calcular importancia promedio
    importance_data = runs[importance_cols].mean().sort_values(ascending=False)
    
    print(f"🎯 TOP 5 FEATURES MÁS IMPORTANTES:")
    for i, (col, importance) in enumerate(importance_data.head().items(), 1):
        feature_name = col.replace('metrics.importance_', '')
        print(f"   {i}. {feature_name}: {importance:.4f}")
    
    return importance_data

# Analizar feature importance
feature_analysis = analyze_feature_importance()
```

---

## 🛠️ TROUBLESHOOTING

### Problemas Comunes y Soluciones

```python
def troubleshoot_mlflow():
    """Diagnosticar problemas comunes con MLflow"""
    
    print("🔍 DIAGNÓSTICO MLflow")
    print("=" * 40)
    
    # 1. Verificar conexión
    try:
        mlflow.search_experiments()
        print("✅ Conexión MLflow OK")
    except Exception as e:
        print(f"❌ Error conexión: {e}")
        print("💡 Solución: docker-compose restart mlflow")
        return
    
    # 2. Verificar experimento
    try:
        experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
        if experiment:
            print(f"✅ Experimento '{EXPERIMENT_NAME}' encontrado")
        else:
            print(f"⚠️  Experimento '{EXPERIMENT_NAME}' no existe")
            print("💡 Se creará automáticamente en el próximo run")
    except Exception as e:
        print(f"❌ Error experimento: {e}")
    
    # 3. Verificar permisos
    try:
        with mlflow.start_run(run_name="permission_test"):
            mlflow.log_param("test", "value")
        print("✅ Permisos de escritura OK")
    except Exception as e:
        print(f"❌ Error permisos: {e}")
        print("💡 Verificar configuración Docker")
    
    # 4. Verificar almacenamiento
    try:
        import requests
        response = requests.get(f"{MLFLOW_TRACKING_URI}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor MLflow healthy")
        else:
            print(f"⚠️  MLflow responde con código: {response.status_code}")
    except Exception as e:
        print(f"❌ Error servidor: {e}")
        print("💡 Verificar: docker-compose logs mlflow")

# Ejecutar diagnóstico
troubleshoot_mlflow()
```

### Comandos de Recuperación

```bash
# Si MLflow no responde
docker-compose restart mlflow
docker-compose logs mlflow

# Si hay problemas de base de datos
docker-compose restart postgres
docker-compose exec postgres psql -U postgres -c "\l"

# Reinicio completo
docker-compose down
docker-compose up -d postgres
sleep 10
docker-compose up -d mlflow

# Verificar estado
docker-compose ps
curl http://localhost:5000/health
```

---

## 🎮 SCRIPTS AUTOMATIZADOS

### Script Principal Unificado

```python
def run_complete_mlflow_pipeline():
    """Pipeline completo automatizado"""
    
    print("🚀 PIPELINE COMPLETO MLflow - CHESS ERROR PREDICTION")
    print("=" * 80)
    
    success_steps = 0
    total_steps = 5
    
    try:
        # PASO 1: Verificar MLflow
        print("\n" + "="*60)
        print("📋 PASO 1/5: Verificando MLflow")
        print("="*60)
        
        if not verify_mlflow_connection():
            print("❌ MLflow no disponible. Verifica servicios Docker.")
            return False
        
        success_steps += 1
        
        # PASO 2: Cargar y explorar datos
        print("\n" + "="*60)
        print("📊 PASO 2/5: Cargando y explorando dataset")
        print("="*60)
        
        dataset_path = find_dataset()
        df = load_and_explore_dataset(dataset_path)
        
        success_steps += 1
        
        # PASO 3: Preparar features
        print("\n" + "="*60)
        print("🔧 PASO 3/5: Preparando features")
        print("="*60)
        
        X, y, features = prepare_features_for_training(df)
        
        success_steps += 1
        
        # PASO 4: Entrenar modelo
        print("\n" + "="*60)
        print("🎯 PASO 4/5: Entrenando modelo")
        print("="*60)
        
        model, run_id, accuracy = train_model_with_mlflow(X, y, features)
        
        success_steps += 1
        
        # PASO 5: Hacer predicciones
        print("\n" + "="*60)
        print("🔮 PASO 5/5: Generando predicciones")
        print("="*60)
        
        results, pred_run_id = make_predictions_with_mlflow_model(run_id=run_id)
        evaluate_model_performance(results)
        
        success_steps += 1
        
        # RESUMEN FINAL
        print("\n" + "="*80)
        print("🎉 PIPELINE COMPLETADO EXITOSAMENTE")
        print("="*80)
        
        print(f"✅ Pasos completados: {success_steps}/{total_steps}")
        print(f"🎯 Accuracy obtenida: {accuracy:.4f}")
        print(f"📊 Muestras procesadas: {len(results)}")
        
        print(f"\n🌐 ENLACES MLflow:")
        print(f"   • UI Principal: http://localhost:5000")
        print(f"   • Experimento: http://localhost:5000/#/experiments")
        print(f"   • Training Run: http://localhost:5000/#/experiments/1/runs/{run_id}")
        print(f"   • Prediction Run: http://localhost:5000/#/experiments/1/runs/{pred_run_id}")
        
        print(f"\n💾 ARCHIVOS GENERADOS:")
        print("   • predictions_results_mlflow.parquet")
        print("   • predictions_summary_mlflow.csv")
        print("   • Modelo registrado en MLflow")
        
        print(f"\n🚀 PRÓXIMOS PASOS:")
        print("   1. 🔍 Explorar resultados en MLflow UI")
        print("   2. 📊 Comparar experimentos")
        print("   3. 🎯 Optimizar hiperparámetros")
        print("   4. 🔮 Integrar en aplicación")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN PASO {success_steps + 1}/{total_steps}")
        print(f"Error: {e}")
        print(f"\n🔍 Para diagnosticar:")
        print("troubleshoot_mlflow()")
        return False

# EJECUTAR PIPELINE COMPLETO
if __name__ == "__main__":
    success = run_complete_mlflow_pipeline()
    
    if success:
        print(f"\n🎯 ¡TUTORIAL MLflow COMPLETADO!")
        print("Revisa la UI de MLflow en: http://localhost:5000")
    else:
        print(f"\n⚠️  Pipeline incompleto. Revisa los errores anteriores.")
```

### Comandos de Uso Rápido

```python
# COMANDOS RÁPIDOS PARA COPIAR/PEGAR

# 1. Setup inicial
"""
# Terminal
docker-compose up -d postgres mlflow
timeout 10
"""

# 2. Verificación rápida
"""
verify_mlflow_connection()
"""

# 3. Pipeline completo
"""
run_complete_mlflow_pipeline()
"""

# 4. Solo entrenamiento
"""
dataset_path = find_dataset()
df = load_and_explore_dataset(dataset_path)
X, y, features = prepare_features_for_training(df)
model, run_id, accuracy = train_model_with_mlflow(X, y, features)
"""

# 5. Solo predicciones
"""
results, pred_run_id = make_predictions_with_mlflow_model(run_id="TU_RUN_ID")
"""

# 6. Comparar experimentos
"""
comparison_df = compare_experiments()
feature_analysis = analyze_feature_importance()
"""

# 7. Diagnóstico
"""
troubleshoot_mlflow()
"""
```

---

## 🎯 RESULTADO ESPERADO

Al final de esta guía tendrás:

✅ **MLflow funcionando** con tracking completo
✅ **Modelo entrenado** con métricas registradas  
✅ **Predicciones generadas** con evaluación
✅ **Experimentos comparables** en UI web
✅ **Artefactos guardados** (modelo, reportes, datos)
✅ **Pipeline reproducible** para futuras iteraciones

**🌐 Accede a MLflow UI**: http://localhost:5000

**📊 Revisa tus experimentos, métricas, y modelos registrados!**

---

*Guía creada: Julio 2025 | Chess Trainer ML Pipeline*
