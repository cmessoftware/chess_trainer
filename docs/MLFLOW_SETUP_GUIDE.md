# MLflow Setup Guide for Chess Trainer

## 📚 ¿Qué es MLflow?

**MLflow** es una plataforma open-source para gestionar el **ciclo de vida completo de Machine Learning**. En nuestro proyecto chess_trainer, MLflow nos ayudará a:

- **🔬 Experiment Tracking**: Registrar experimentos, parámetros, métricas y resultados
- **📦 Model Registry**: Versionar y gestionar modelos entrenados  
- **🚀 Model Deployment**: Desplegar modelos para predicciones en producción
- **📊 Visualization**: Comparar experimentos y visualizar métricas

## 🎯 MLflow en Chess Trainer - Casos de Uso

### **Experiment Tracking para Chess ML**
```python
import mlflow
import mlflow.sklearn

# Registrar un experimento de predicción de errores
with mlflow.start_run(experiment_id="chess_error_prediction"):
    # Parámetros del modelo
    mlflow.log_param("model_type", "RandomForest")
    mlflow.log_param("n_estimators", 100)
    mlflow.log_param("max_depth", 10)
    mlflow.log_param("features", ["score_diff", "material_balance", "phase"])
    
    # Entrenar modelo RandomForest para predecir error_label
    model = RandomForestClassifier(n_estimators=100, max_depth=10)
    model.fit(X_train, y_train)
    
    # Registrar métricas
    accuracy = model.score(X_test, y_test)
    mlflow.log_metric("accuracy", accuracy)
    mlflow.log_metric("precision", precision_score(y_test, y_pred, average='weighted'))
    mlflow.log_metric("recall", recall_score(y_test, y_pred, average='weighted'))
    
    # Guardar el modelo
    mlflow.sklearn.log_model(model, "chess_error_predictor")
```

### **Casos de Uso Específicos**
1. **Comparar modelos**: RandomForest vs LogisticRegression vs XGBoost
2. **Optimizar hiperparámetros**: n_estimators, max_depth, learning_rate
3. **Evaluar features**: ¿Qué features son más predictivos para error_label?
4. **Versionar datasets**: Diferentes fuentes (elite, novice, personal, fide)
5. **Tracking por fases**: Modelos para opening, middlegame, endgame

## 🐳 Configuración Docker para Chess Trainer

### **1. Actualizar docker-compose.yml**

```yaml
version: '3.8'

services:
  # ...existing services...
  
  mlflow:
    image: python:3.9-slim
    container_name: chess_mlflow
    ports:
      - "5000:5000"
    volumes:
      - ./mlruns:/mlflow/mlruns
      - ./models:/mlflow/models
      - .:/workspace
    working_dir: /workspace
    environment:
      - MLFLOW_BACKEND_STORE_URI=sqlite:///mlflow/mlruns/mlflow.db
      - MLFLOW_DEFAULT_ARTIFACT_ROOT=/mlflow/mlruns
    command: >
      bash -c "pip install mlflow[extras] && 
               mlflow server 
               --backend-store-uri sqlite:///mlflow/mlruns/mlflow.db 
               --default-artifact-root /mlflow/mlruns 
               --host 0.0.0.0 
               --port 5000"
    networks:
      - chess_network

  # Contenedor principal con MLflow cliente
  app:
    # ...existing config...
    environment:
      - MLFLOW_TRACKING_URI=http://mlflow:5000
    depends_on:
      - mlflow
      - postgres
    # ...rest of config...

networks:
  chess_network:
    driver: bridge

volumes:
  postgres_data:
  mlflow_data:
```

### **2. Estructura de Directorios MLflow**

```
chess_trainer/
├── mlruns/                     # Experimentos y métricas
│   ├── 0/                      # Experimento Default
│   ├── 1/                      # chess_error_prediction
│   ├── 2/                      # chess_opening_recommendation
│   └── mlflow.db              # Base de datos SQLite
├── models/                     # Modelos registrados
│   ├── chess_error_predictor/  
│   ├── chess_accuracy_predictor/
│   └── chess_phase_classifier/
├── src/ml/                     # Scripts ML con MLflow
│   ├── train_error_model.py
│   ├── train_accuracy_model.py
│   └── mlflow_utils.py
└── notebooks/                  # Notebooks con tracking
    ├── mlflow_experiments.ipynb
    └── model_comparison.ipynb
```

## 🚀 Scripts de MLflow para Chess Trainer

### **src/ml/mlflow_utils.py**
```python
import mlflow
import mlflow.sklearn
import mlflow.xgboost
import pandas as pd
import os
from pathlib import Path

class ChessMLflowTracker:
    def __init__(self, tracking_uri="http://localhost:5000"):
        mlflow.set_tracking_uri(tracking_uri)
        self.client = mlflow.tracking.MlflowClient()
    
    def create_chess_experiments(self):
        """Crear experimentos específicos para chess_trainer"""
        experiments = [
            ("chess_error_prediction", "Predecir tipo de error (blunder, mistake, inaccuracy)"),
            ("chess_accuracy_prediction", "Predecir accuracy de partidas"),
            ("chess_phase_classification", "Clasificar fase del juego"),
            ("chess_opening_recommendation", "Recomendar aperturas basado en estilo"),
            ("chess_stockfish_features", "Optimizar features de Stockfish")
        ]
        
        for name, description in experiments:
            try:
                experiment = self.client.create_experiment(
                    name=name, 
                    tags={"project": "chess_trainer", "description": description}
                )
                print(f"✅ Experimento creado: {name} (ID: {experiment})")
            except mlflow.exceptions.MlflowException as e:
                print(f"⚠️ Experimento {name} ya existe o error: {e}")
    
    def log_chess_dataset_info(self, df: pd.DataFrame, source: str):
        """Registrar información del dataset"""
        mlflow.log_param("dataset_source", source)
        mlflow.log_param("dataset_rows", len(df))
        mlflow.log_param("dataset_features", list(df.columns))
        mlflow.log_param("missing_values", df.isnull().sum().sum())
        
        # Log distribución de error_label si existe
        if 'error_label' in df.columns:
            error_dist = df['error_label'].value_counts().to_dict()
            for error_type, count in error_dist.items():
                mlflow.log_metric(f"count_{error_type}", count)
    
    def log_chess_model_metrics(self, y_true, y_pred, model_name: str):
        """Registrar métricas específicas para modelos de chess"""
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        # Métricas básicas
        mlflow.log_metric("accuracy", accuracy_score(y_true, y_pred))
        mlflow.log_metric("precision_macro", precision_score(y_true, y_pred, average='macro'))
        mlflow.log_metric("recall_macro", recall_score(y_true, y_pred, average='macro'))
        mlflow.log_metric("f1_macro", f1_score(y_true, y_pred, average='macro'))
        
        # Métricas por clase (para error_label)
        if len(set(y_true)) > 2:  # Multi-class
            for label in set(y_true):
                y_true_binary = (y_true == label).astype(int)
                y_pred_binary = (y_pred == label).astype(int)
                mlflow.log_metric(f"precision_{label}", precision_score(y_true_binary, y_pred_binary))
                mlflow.log_metric(f"recall_{label}", recall_score(y_true_binary, y_pred_binary))
```

### **src/ml/train_error_model.py**
```python
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import sys
sys.path.append('/chess_trainer/src')
from ml.mlflow_utils import ChessMLflowTracker

def train_chess_error_model():
    """Entrenar modelo para predecir error_label con MLflow tracking"""
    
    # Inicializar MLflow
    tracker = ChessMLflowTracker()
    mlflow.set_experiment("chess_error_prediction")
    
    # Cargar datos
    print("📊 Cargando dataset...")
    df = pd.read_parquet('/chess_trainer/datasets/export/personal/features.parquet')
    
    # Preparar datos
    feature_cols = [
        'score_diff', 'material_balance', 'branching_factor', 
        'self_mobility', 'opponent_mobility', 'num_pieces'
    ]
    
    # Filtrar datos válidos
    df_clean = df.dropna(subset=feature_cols + ['error_label'])
    X = df_clean[feature_cols]
    y = df_clean['error_label']
    
    # Split datos
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Modelos a comparar
    models = {
        'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
        'LogisticRegression': LogisticRegression(random_state=42, max_iter=1000)
    }
    
    # Entrenar cada modelo
    for model_name, model in models.items():
        with mlflow.start_run(run_name=f"chess_error_{model_name}"):
            print(f"🤖 Entrenando {model_name}...")
            
            # Log dataset info
            tracker.log_chess_dataset_info(df_clean, "personal")
            
            # Log parámetros del modelo
            mlflow.log_param("model_type", model_name)
            mlflow.log_param("features", feature_cols)
            mlflow.log_param("n_samples_train", len(X_train))
            mlflow.log_param("n_samples_test", len(X_test))
            
            if model_name == 'RandomForest':
                mlflow.log_param("n_estimators", model.n_estimators)
                mlflow.log_param("random_state", model.random_state)
            
            # Entrenar modelo
            model.fit(X_train, y_train)
            
            # Predicciones
            y_pred = model.predict(X_test)
            
            # Log métricas
            tracker.log_chess_model_metrics(y_test, y_pred, model_name)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            mlflow.log_metric("cv_mean", cv_scores.mean())
            mlflow.log_metric("cv_std", cv_scores.std())
            
            # Guardar modelo
            mlflow.sklearn.log_model(
                model, 
                f"chess_error_{model_name.lower()}",
                registered_model_name=f"ChessErrorPredictor_{model_name}"
            )
            
            # Log feature importance (solo RandomForest)
            if hasattr(model, 'feature_importances_'):
                feature_importance = pd.DataFrame({
                    'feature': feature_cols,
                    'importance': model.feature_importances_
                }).sort_values('importance', ascending=False)
                
                # Log top features
                for idx, row in feature_importance.iterrows():
                    mlflow.log_metric(f"importance_{row['feature']}", row['importance'])
                
                print("📈 Feature Importance:")
                print(feature_importance)
            
            print(f"✅ {model_name} completado!")
            print(f"🎯 Accuracy: {model.score(X_test, y_test):.3f}")
            print(f"📊 Classification Report:")
            print(classification_report(y_test, y_pred))

if __name__ == "__main__":
    train_chess_error_model()
```

## 📊 Comandos Esenciales MLflow

### **1. Iniciar MLflow Server**
```bash
# En Docker
docker-compose up -d mlflow

# Local
mlflow server --backend-store-uri sqlite:///mlruns/mlflow.db --default-artifact-root ./mlruns --host 0.0.0.0 --port 5000
```

### **2. Acceder a MLflow UI**
```bash
# Abrir en navegador
http://localhost:5000
```

### **3. Ejecutar Experimentos**
```bash
# Desde contenedor
docker-compose exec app python src/ml/train_error_model.py

# Local
cd /chess_trainer
python src/ml/train_error_model.py
```

### **4. Comparar Experimentos en UI**
1. **Experiments Tab**: Ver lista de experimentos
2. **Runs Comparison**: Seleccionar runs y comparar métricas
3. **Charts**: Visualizar métricas en gráficos
4. **Models**: Ver modelos registrados

## 🎲 Ejemplos Prácticos para Chess Trainer

### **Experimento 1: Optimización de RandomForest**
```python
import mlflow

# Experimento de Grid Search con MLflow
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15, None],
    'min_samples_split': [2, 5, 10]
}

mlflow.set_experiment("chess_rf_optimization")

for n_est in param_grid['n_estimators']:
    for max_d in param_grid['max_depth']:
        for min_split in param_grid['min_samples_split']:
            with mlflow.start_run():
                # Log parámetros
                mlflow.log_param("n_estimators", n_est)
                mlflow.log_param("max_depth", max_d)
                mlflow.log_param("min_samples_split", min_split)
                
                # Entrenar modelo
                model = RandomForestClassifier(
                    n_estimators=n_est,
                    max_depth=max_d,
                    min_samples_split=min_split,
                    random_state=42
                )
                model.fit(X_train, y_train)
                
                # Evaluar y log métricas
                accuracy = model.score(X_test, y_test)
                mlflow.log_metric("accuracy", accuracy)
                
                print(f"n_est={n_est}, max_d={max_d}, min_split={min_split} -> Acc={accuracy:.3f}")
```

### **Experimento 2: Comparar Features Sets**
```python
feature_sets = {
    'basic': ['score_diff', 'material_balance'],
    'tactical': ['score_diff', 'material_balance', 'branching_factor', 'self_mobility'],
    'complete': ['score_diff', 'material_balance', 'branching_factor', 'self_mobility', 
                 'opponent_mobility', 'num_pieces', 'phase', 'has_castling_rights']
}

mlflow.set_experiment("chess_feature_comparison")

for set_name, features in feature_sets.items():
    with mlflow.start_run(run_name=f"features_{set_name}"):
        mlflow.log_param("feature_set", set_name)
        mlflow.log_param("n_features", len(features))
        mlflow.log_param("features", features)
        
        # Entrenar con este set de features
        X_subset = X_train[features]
        X_test_subset = X_test[features]
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_subset, y_train)
        
        accuracy = model.score(X_test_subset, y_test)
        mlflow.log_metric("accuracy", accuracy)
        
        print(f"Feature set '{set_name}' ({len(features)} features) -> Accuracy: {accuracy:.3f}")
```

## 🔧 Tasks específicos para chess_trainer

### **Agregar a requirements.txt**
```text
mlflow>=2.0.0
mlflow[extras]>=2.0.0
```

### **Crear script de inicialización**
```bash
# src/scripts/setup_mlflow.py
from src.ml.mlflow_utils import ChessMLflowTracker

def setup_chess_mlflow():
    print("🚀 Configurando MLflow para Chess Trainer...")
    tracker = ChessMLflowTracker()
    tracker.create_chess_experiments()
    print("✅ MLflow configurado correctamente!")

if __name__ == "__main__":
    setup_chess_mlflow()
```

### **Integrar con existing tasks.json**
```json
{
    "label": "🤖 ML: Setup MLflow",
    "type": "shell",
    "command": "python src/scripts/setup_mlflow.py",
    "group": "build"
},
{
    "label": "🤖 ML: Train Error Model",
    "type": "shell", 
    "command": "python src/ml/train_error_model.py",
    "group": "test"
},
{
    "label": "🌐 ML: Open MLflow UI",
    "type": "shell",
    "command": "cmd",
    "args": ["/c", "start", "http://localhost:5000"],
    "group": "none"
}
```

## 📈 Workflow Recomendado

### **Paso 1: Setup Inicial**
```bash
# 1. Levantar MLflow
docker-compose up -d mlflow

# 2. Configurar experimentos
python src/scripts/setup_mlflow.py

# 3. Verificar en UI
http://localhost:5000
```

### **Paso 2: Primer Experimento**
```bash
# Entrenar modelo baseline
python src/ml/train_error_model.py
```

### **Paso 3: Comparar en UI**
1. Ir a http://localhost:5000
2. Seleccionar experimento "chess_error_prediction"
3. Comparar runs RandomForest vs LogisticRegression
4. Analizar métricas y feature importance

### **Paso 4: Iterar y Mejorar**
- Probar diferentes hiperparámetros
- Experimentar con feature engineering
- Comparar diferentes datasets (elite vs novice)

---

**✨ Con esta configuración tendrás experiment tracking completo para todos los modelos de chess_trainer!**

**Próximos pasos**: Una vez que tengas MLflow funcionando, podremos continuar con mejorar el EDA sistemático (#66) y entrenar los primeros modelos baseline (#67).

---

**Última actualización**: 08-07-2025
