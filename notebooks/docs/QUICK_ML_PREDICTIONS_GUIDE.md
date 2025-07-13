# 🔮 PREDICCIONES ML CON MLFLOW - GUÍA RÁPIDA

## 🚀 Inicio Rápido (2 minutos)

### Opción 1: Ejecución Automática (Recomendada)
```powershell
# Ejecutar todo automáticamente
.\mlflow-predictions.ps1
```

### Opción 2: Ejecución Manual Paso a Paso
```powershell
# 1. Iniciar servicios
docker-compose up -d

# 2. Análisis de datos
python src/ml/explore_datasets.py

# 3. Entrenar modelo
python src/ml/train_basic_model.py

# 4. Hacer predicciones
python src/ml/make_predictions.py
```

### Opción 3: Pipeline Completo
```powershell
python src/ml/run_complete_pipeline.py
```

---

## 📊 ¿Qué hace cada script?

### 🔍 `explore_datasets.py`
- Analiza todos los datasets disponibles
- Muestra estadísticas de calidad de datos
- Identifica features tácticas y ELO standardizadas
- Recomienda estrategia de experimentación

**Salida esperada:**
```
📊 Dataset: unified_all
   📊 Shape: (15000, 45)
   🎯 Target distribution:
      good: 8500 (56.7%)
      mistake: 3200 (21.3%)
      inaccuracy: 2100 (14.0%)
      blunder: 1200 (8.0%)
   ⚔️ Features tácticas: 8
   🎯 Columnas ELO: ['white_elo', 'black_elo', 'standardized_white_elo', 'standardized_black_elo']
```

### 🎯 `train_basic_model.py`
- Entrena modelo RandomForest con MLflow tracking
- Evalúa rendimiento con métricas detalladas
- Registra modelo en MLflow Model Registry
- Muestra feature importance

**Salida esperada:**
```
✅ Modelo entrenado - Accuracy: 0.8542
📊 REPORTE DETALLADO
🎯 Accuracy: 0.8542

🔧 Top 10 Features más importantes:
   1. score_diff: 0.2341
   2. material_balance: 0.1789
   3. depth_score_diff: 0.1456
   4. threatens_mate: 0.0987
   5. standardized_white_elo: 0.0834
```

### 🔮 `make_predictions.py`
- Carga el mejor modelo desde MLflow
- Hace predicciones en nuevos datos
- Analiza confianza de predicciones
- Guarda resultados en archivo Parquet

**Salida esperada:**
```
✅ Mejor modelo cargado - Accuracy: 0.8542
🔮 Generando predicciones...
📊 Distribución de predicciones:
   good: 5670 (56.7%)
   mistake: 2130 (21.3%)
   inaccuracy: 1400 (14.0%)
   blunder: 800 (8.0%)
🎯 Confianza promedio: 0.847
💾 Predicciones guardadas en: predictions_output.parquet
```

### 🚀 `run_complete_pipeline.py`
- Ejecuta todo el pipeline automáticamente
- Maneja errores y timeouts
- Proporciona reporte final
- Ofrece experimentos adicionales

---

## 📈 Interpretación de Resultados

### 🎯 Métricas de Evaluación

| Métrica       | Descripción                  | Valor Objetivo |
| ------------- | ---------------------------- | -------------- |
| **Accuracy**  | Precisión general del modelo | > 0.80         |
| **Precision** | Precisión por clase de error | > 0.75         |
| **Recall**    | Recall por clase de error    | > 0.70         |
| **F1-Score**  | Promedio armónico P/R        | > 0.75         |

### 🔮 Confianza de Predicciones

| Rango     | Interpretación  | Acción Recomendada           |
| --------- | --------------- | ---------------------------- |
| > 0.90    | Alta confianza  | Usar predicción directamente |
| 0.70-0.90 | Confianza media | Revisar contexto             |
| 0.50-0.70 | Baja confianza  | Análisis manual requerido    |
| < 0.50    | Muy incierta    | No usar predicción           |

### ⚔️ Features Más Importantes

1. **`score_diff`** - Diferencia de evaluación Stockfish
2. **`material_balance`** - Balance material en la posición
3. **`depth_score_diff`** - Diferencia por profundidad (Feature táctica)
4. **`threatens_mate`** - Amenaza de mate (Feature táctica)
5. **`standardized_elo`** - ELO estandarizado (Issue #21)

---

## 🌐 MLflow UI - Navegación

### Acceso
- **URL**: http://localhost:5000
- **Experimentos**: "chess_error_prediction"

### Secciones Importantes

#### 📊 Experiments
- Lista de todos los runs de entrenamiento
- Comparación de métricas entre modelos
- Filtrado y ordenamiento por accuracy

#### 🏆 Models
- Modelo registrado: "ChessErrorClassifier"
- Versiones disponibles
- Staging/Production deployment

#### 📈 Run Details
- Parámetros del modelo
- Métricas detalladas
- Artefactos (matriz de confusión)
- Feature importance

---

## 🔧 Troubleshooting

### ❌ Error: "No se encontraron datasets"
```powershell
# Verificar datasets disponibles
ls data/export/

# Si no existen, ejecutar pipeline de datos
python src/pipeline/generate_datasets.py
```

### ❌ Error: "MLflow no disponible"
```powershell
# Iniciar servicios Docker
docker-compose up -d mlflow

# Verificar servicios
docker ps | grep mlflow
```

### ❌ Error: "Modelo no encontrado"
```powershell
# Entrenar modelo primero
python src/ml/train_basic_model.py

# Verificar en MLflow UI
start http://localhost:5000
```

### ❌ Error: "Missing values"
```powershell
# Verificar calidad de datos
python src/ml/explore_datasets.py

# Regenerar datasets si es necesario
python src/ml/preprocess_data.py
```

---

## 🎯 Experimentos Avanzados

### 1. 📊 Comparación por Fuentes
```python
# Comparar rendimiento entre elite, novice, personal
datasets = ["elite", "novice", "personal", "fide"]
for dataset in datasets:
    train_model_for_source(dataset)
```

### 2. ⚙️ Optimización de Hiperparámetros
```python
# Grid search con MLflow tracking
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15, None]
}
optimize_hyperparameters(param_grid)
```

### 3. ⚔️ Experimento Features Tácticas
```python
# Comparar: solo tácticas vs estándar vs combinadas
compare_feature_sets([
    "tactical_only",
    "standard_only", 
    "combined"
])
```

### 4. 🎲 Ensemble Models
```python
# Combinar múltiples modelos
models = [RandomForest, GradientBoosting, XGBoost]
train_ensemble(models)
```

---

## 📚 Próximos Pasos

### 🔮 Predicciones en Tiempo Real
```python
from src.ml.realtime_predictor import RealTimeChessPredictor

predictor = RealTimeChessPredictor()
result = predictor.predict_from_fen("fen_string")
```

### 🌐 API REST
```python
# Implementar endpoint de predicciones
@app.post("/predict")
def predict_move_error(position: ChessPosition):
    return predictor.predict(position)
```

### 📊 Dashboard Interactivo
```python
# Streamlit dashboard para visualizar predicciones
streamlit run src/pages/ml_dashboard.py
```

### 🧪 A/B Testing
```python
# Comparar diferentes versiones del modelo
test_model_versions(["v1.0", "v2.0"])
```

---

## 🎉 Resultado Esperado

Al finalizar esta guía, tendrás:

✅ **Modelo ML entrenado** con accuracy > 80%  
✅ **Sistema de predicciones** funcionando  
✅ **MLflow tracking** configurado  
✅ **Análisis de confianza** implementado  
✅ **ELO standardization** integrado (Issue #21)  
✅ **Features tácticas** disponibles  
✅ **Pipeline automatizado** listo para producción  

¡Listo para hacer predicciones inteligentes de errores de ajedrez! 🚀♟️
