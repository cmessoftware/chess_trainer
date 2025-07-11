# 🚀 MLflow Quick Start - Chess Trainer

## 📋 ¿Qué acabamos de configurar?

Hemos configurado **MLflow** completamente integrado con tu proyecto chess_trainer. MLflow es una herramienta que te permite:

- 🔬 **Trackear experimentos**: Cada vez que entrenes un modelo, MLflow registra automáticamente parámetros, métricas y resultados
- 📊 **Comparar modelos**: Ver fácilmente qué modelo funciona mejor para predecir errores en ajedrez
- 🎯 **Reproducir resultados**: Volver a ejecutar experimentos exactos con los mismos parámetros
- 🚀 **Desplegar modelos**: Servir tu mejor modelo para hacer predicciones en producción

## 🐳 Iniciar MLflow (Primera vez)

### Opción 1: Usar VS Code Tasks (Recomendado)
```
Ctrl+Shift+P → "Tasks: Run Task" → "🚀 ML Workflow: Start MLflow Server"
```

### Opción 2: PowerShell Script
```powershell
.\build_up_clean_all.ps1
```

### Opción 3: Docker Compose Manual
```bash
docker-compose up -d mlflow
```

## 🌐 Acceder a MLflow UI

Una vez iniciado, puedes ver la interfaz web en:
- **URL**: http://localhost:5000
- **VS Code Task**: `🌐 ML Workflow: Open MLflow UI`

## 🧪 Ejecutar tu Primer Experimento

### 1. Configuración Inicial
```bash
# Desde VS Code Terminal:
docker-compose exec notebooks python /chess_trainer/src/scripts/setup_mlflow.py
```

### 2. Entrenar Modelos de Ejemplo
```bash
# Entrenar modelos baseline (RandomForest, LogisticRegression, SVM):
docker-compose exec notebooks python /chess_trainer/src/ml/train_error_model.py
```

## 📊 Qué Verás en MLflow UI

### **Experimentos Creados**:
1. **chess_error_classification** - Predecir tipos de error (blunder, mistake, inaccuracy)
2. **chess_feature_engineering** - Probar diferentes combinaciones de features
3. **chess_hyperparameter_tuning** - Optimizar parámetros de modelos
4. **chess_model_comparison** - Comparar diferentes algoritmos
5. **chess_phase_analysis** - Modelos específicos por fase del juego
6. **chess_elo_analysis** - Análisis por rango de ELO

### **Métricas Tracked**:
- `accuracy` - Precisión general del modelo
- `f1_macro` - F1-score promedio entre todas las clases
- `precision_macro` - Precisión promedio
- `recall_macro` - Recall promedio
- `cv_accuracy_mean` - Precisión de validación cruzada
- `feature_importance_*` - Importancia de cada feature

### **Artefactos Guardados**:
- 📈 **Gráficos**: Matriz de confusión, importancia de features
- 📄 **Reportes**: Classification report, resultados detallados
- 🤖 **Modelos**: Modelos entrenados listos para usar
- 📊 **Datasets**: Información sobre datos utilizados

## 🎯 Casos de Uso Inmediatos

### **Comparar Algoritmos**
```python
# En MLflow UI, ve a "chess_error_classification"
# Compara métricas entre RandomForest, LogisticRegression y SVM
# Ordena por "accuracy" para ver el mejor modelo
```

### **Optimizar Hiperparámetros**
```python
# Ve a "chess_hyperparameter_tuning"
# Observa cómo diferentes parámetros afectan el rendimiento
# Encuentra la mejor combinación de n_estimators, max_depth, etc.
```

### **Analizar Features**
```python
# En cualquier experimento con RandomForest
# Ve "Artifacts" → "feature_importance_plot.png"
# Descubre qué features son más importantes para predecir errores
```

## 🔄 Workflow Típico

### 1. **Experimentar**
```bash
# Modificar parámetros en train_error_model.py
# Ejecutar entrenamiento
docker-compose exec notebooks python /chess_trainer/src/ml/train_error_model.py
```

### 2. **Comparar en UI**
- Abrir http://localhost:5000
- Seleccionar experimento
- Comparar runs por métricas
- Revisar gráficos y reportes

### 3. **Iterar**
- Identificar qué funciona mejor
- Probar nuevas combinaciones
- Optimizar hiperparámetros
- Agregar nuevas features

### 4. **Desplegar**
```python
# Cargar mejor modelo para uso en producción
import mlflow.sklearn
model = mlflow.sklearn.load_model("runs:/<run_id>/model")
predictions = model.predict(new_data)
```

## 📈 Próximos Pasos Sugeridos

### **Inmediato (Hoy)**:
1. ✅ Ejecutar `setup_mlflow.py` - Crear experimentos base
2. ✅ Ejecutar `train_error_model.py` - Entrenar modelos baseline
3. ✅ Explorar MLflow UI - Familiarizarte con la interfaz
4. ✅ Comparar modelos - Ver cuál funciona mejor

### **Esta Semana**:
1. 🎯 Probar con tus datasets reales de chess
2. 🔧 Optimizar hiperparámetros del mejor modelo
3. 📊 Analizar importancia de features tácticos
4. 🚀 Integrar modelo en tu FastAPI

### **Próximo Sprint**:
1. 🧠 Modelos especializados por fase de juego
2. 📈 Tracking de mejora de jugadores en el tiempo
3. 🎮 Integración con sistema de recomendaciones
4. 🔄 Pipeline automatizado de reentrenamiento

## 🐛 Solución de Problemas

### **MLflow UI no carga**:
```bash
# Verificar que el servicio esté corriendo
docker-compose ps mlflow

# Ver logs del servicio
docker-compose logs -f mlflow

# Reiniciar si es necesario
docker-compose restart mlflow
```

### **Error al ejecutar scripts**:
```bash
# Verificar que el contenedor de notebooks esté activo
docker-compose ps notebooks

# Acceder al contenedor para debug
docker-compose exec notebooks bash
cd /chess_trainer
python src/scripts/setup_mlflow.py
```

### **No hay datasets**:
```bash
# Generar features si no existen
docker-compose exec chess_trainer python src/scripts/generate_features_parallel.py

# Exportar a formato parquet
docker-compose exec chess_trainer python src/scripts/export_features_dataset_parallel.py
```

## 🎉 ¡Listo para Experimentar!

Ya tienes todo configurado para empezar a usar Machine Learning de forma profesional en tu proyecto de ajedrez. MLflow te ayudará a:

- 🎯 **Enfocar** tus experimentos y no perder resultados
- 📊 **Comparar** objetivamente diferentes enfoques  
- 🚀 **Accelerar** el desarrollo de nuevos modelos
- 🔄 **Reproducir** resultados cuando necesites volver a un modelo anterior

**¡Experimenta, compara y mejora tus modelos de ajedrez!** 🏆

---

*Creado: 2025-01-26*  
*Proyecto: chess_trainer + MLflow + Docker*
