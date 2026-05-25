# Predicciones Fiables con MLflow - Chess Trainer

## Objetivo

Este documento describe cómo hacer predicciones fiables de errores de ajedrez utilizando MLflow para el tracking y gestión de modelos.

## Arquitectura del Sistema

```
Datos → Feature Engineering → Modelos ML → MLflow → Predicciones
```

## Pipeline de Predicciones

### 1. Preparación de Datos

```python
from src.ml.chess_error_predictor import ChessErrorPredictor

# Inicializar predictor
predictor = ChessErrorPredictor()

# Cargar datos
data = predictor.load_training_data()
```

### 2. Entrenamiento del Modelo

```python
# Entrenar modelo baseline
model = predictor.train_baseline_model()

# Evaluar modelo
metrics = predictor.evaluate_model(model)
print(f"F1 Score: {metrics['f1_macro']}")
```

### 3. Registro en MLflow

```python
import mlflow
import mlflow.sklearn

with mlflow.start_run():
    # Log parámetros
    mlflow.log_param("model_type", "LogisticRegression")
    mlflow.log_param("regularization", "L2")
    
    # Log métricas
    mlflow.log_metric("f1_macro", metrics['f1_macro'])
    mlflow.log_metric("accuracy", metrics['accuracy'])
    
    # Log modelo
    mlflow.sklearn.log_model(
        model, 
        "chess_error_classifier",
        registered_model_name="ChessErrorPredictor"
    )
```

### 4. Hacer Predicciones

```python
# Cargar modelo desde MLflow
model_uri = "models:/ChessErrorPredictor/Production"
model = mlflow.sklearn.load_model(model_uri)

# Hacer predicción
features = predictor.extract_features(game)
prediction = model.predict_proba(features)

print(f"Error Label: {prediction['label']}")
print(f"Confidence: {prediction['confidence']:.2f}")
```

## Métricas de Evaluación

### Métricas Principales

1. **F1 Macro**: Métrica principal para clases desbalanceadas
2. **Matriz de Confusión**: Análisis detallado de errores
3. **Calibración**: Confiabilidad de las probabilidades

### Criterios de Calidad

- **F1 Macro > 0.70**: Baseline mínimo aceptable
- **Confusión grave < 5%**: Entre `good` y `blunder`
- **Calibración ECE < 0.1**: Probabilidades bien calibradas

## Monitoreo de Modelos

### Tracking de Experimentos

```python
# Configurar experimento
mlflow.set_experiment("chess_error_classification")

# Crear run con tags
with mlflow.start_run() as run:
    mlflow.set_tag("phase", "1")
    mlflow.set_tag("model_type", "baseline")
    mlflow.set_tag("data_version", "v1.0")
```

### Model Registry

```python
# Promoción de modelo
client = mlflow.tracking.MlflowClient()

# Transición a Production
client.transition_model_version_stage(
    name="ChessErrorPredictor",
    version=1,
    stage="Production"
)
```

## Validación de Predicciones

### Tests de Consistencia

1. **Sanity Checks**: Predicciones básicas coherentes
2. **Regression Tests**: Comparación con versiones anteriores
3. **A/B Testing**: Evaluación en producción

### Ejemplo de Validación

```python
def validate_predictions(model, test_data):
    predictions = model.predict(test_data)
    
    # Test 1: No predicciones imposibles
    assert all(p in ['good', 'inaccuracy', 'mistake', 'blunder'] for p in predictions)
    
    # Test 2: Distribución esperada
    good_ratio = sum(p == 'good' for p in predictions) / len(predictions)
    assert 0.3 <= good_ratio <= 0.7  # Entre 30-70% jugadas buenas
    
    return True
```

## Deployment

### Serving del Modelo

```bash
# Servir modelo con MLflow
mlflow models serve -m "models:/ChessErrorPredictor/Production" -p 5001
```

### API Integration

```python
import requests

# Hacer predicción via API
response = requests.post(
    "http://localhost:5001/invocations",
    json={"instances": features.tolist()}
)

prediction = response.json()
```

## Referencias

- [Chess Error Predictor](../src/ml/chess_error_predictor.py)
- [MLflow Utils](../src/ml/mlflow_utils.py)
- [Roadmap Técnico](ROADMAP_TECHNICAL.md)
