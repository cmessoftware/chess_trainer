# 🕐 FASE 3: ANÁLISIS TEMPORAL - PLAN DE IMPLEMENTACIÓN

**Fecha:** 7 de Febrero de 2026  
**Estado:** Iniciando (0% → 100%)  
**Contexto:** Post-Phase 2 exitoso (MLP F1=0.992)

---

## 🎯 OBJETIVOS PHASE 3

### Objetivos Principales
1. **Análisis de Secuencias Temporales**: Detectar patrones de errores en cadena
2. **Predicción de Colapso**: Identificar riesgo de racha de errores graves 
3. **Mejora sobre Phase 2**: Superar F1=0.992 usando información temporal
4. **Features Temporales**: Implementar características de presión de tiempo y tendencias

### Target de Performance
- **F1 Macro Target**: >0.995 (mejora de +0.003 sobre Phase 2)
- **Recall Blunder Sequence**: >0.85 (detectar rachas de blunders)
- **Delay de Detección**: <2 movimientos (predecir colapso temprano)
- **Stability**: CV std <0.003 (mantener consistencia)

---

## 📊 ANÁLISIS DE CONTEXTO

### Resultados Previos (Resumen)
```
Phase 1 (Baseline): F1=0.890 (Logistic L2)
Phase 2 (MLP):      F1=0.992 (99.8% accuracy)
                    Gap: 0.04% (no overfitting)
                    328K samples, 15 features
```

### ¿Por qué Análisis Temporal?
1. **Errores correlacionados**: Un error grave puede llevar a más errores
2. **Presión de tiempo**: Tiempo restante afecta calidad de decisiones
3. **Patrones de colapso**: Algunos jugadores tienen rachas malas predecibles  
4. **Context aware**: Decisión actual influenciada por jugadas previas

---

## 🛠️ PLAN DE IMPLEMENTACIÓN

### Paso 1: Features Temporales Avanzadas (2-3 horas)
```python
# Nuevas features que debemos implementar:
temporal_features = [
    'score_cp_diff',         # Cambio en evaluación (cp)
    'consecutive_errors',    # Contador de errores seguidos
    'error_severity_trend',  # Tendencia de gravedad de errores
    'time_pressure',        # Presión de tiempo estimada
    'score_volatility',     # Volatilidad de evaluación
    'recovery_pattern',     # Patrón de recuperación de errores
    'momentum_shift',       # Cambio de momentum en partida
    'blunder_risk',         # Riesgo calculado de blunder próximo
]
```

### Paso 2: Modelos Secuenciales (3-4 horas)
1. **1D-CNN**: Para detectar patrones locales en secuencias
2. **GRU**: Para memoria a largo plazo de errores
3. **LSTM**: Alternativa si GRU no converge bien
4. **CNN+GRU**: Híbrido para capturar patterns + memoria

### Paso 3: Pipeline Temporal Completo (2 horas)
- Ventanas deslizantes de 5-7 movimientos
- Preprocesamiento de secuencias
- Data augmentation temporal
- Validación temporal (split por fecha/partida)

### Paso 4: Evaluación y Comparación (1 hora)
- Métricas específicas para secuencias
- Análisis de casos donde temporal supera MLP
- Visualización de patrones detectados

---

## 📋 ESTRUCTURA DE ARCHIVOS

```
src/ml/phase3_temporal_final.py      # Implementación principal
src/ml/phase3_features.py            # Generador de features temporales  
src/ml/phase3_models.py              # Modelos CNN/GRU/LSTM
src/ml/phase3_evaluation.py          # Evaluación específica temporal
docs/PHASE3_RESULTS.md               # Resultados y análisis
logs/phase3_temporal_output.log      # Logs de ejecución
```

---

## 🔧 CONFIGURACIONES TÉCNICAS

### Arquitecturas Planificadas
```python
# 1D-CNN Configuration
cnn_config = {
    'filters': [64, 32, 16],
    'kernel_size': 3,
    'pool_size': 2,
    'dropout': 0.3
}

# GRU Configuration  
gru_config = {
    'units': [64, 32],
    'dropout': 0.4,
    'recurrent_dropout': 0.3,
    'return_sequences': False
}

# Hybrid CNN+GRU
hybrid_config = {
    'cnn_filters': 32,
    'gru_units': 48,
    'sequence_length': 7
}
```

### Hiperparámetros
- **Window Size**: 5-7 movimientos
- **Batch Size**: 64 (temporal sequences)
- **Learning Rate**: 0.001 → 0.0001 (adaptive)
- **Max Epochs**: 100 (early stopping)
- **Sample Weight**: Mantener balance de Phase 2

---

## 📈 MÉTRICAS DE EVALUACIÓN

### Métricas Estándar
- F1 Macro (comparar vs 0.992)
- Accuracy por clase
- Cross-validation (5-fold)

### Métricas Temporales Específicas
```python
temporal_metrics = {
    'sequence_accuracy': "% secuencias bien clasificadas",
    'blunder_sequence_recall': "% rachas de blunders detectadas", 
    'early_detection_rate': "% colapsos detectados temprano",
    'false_alarm_rate': "% alarmas falsas de colapso",
    'temporal_consistency': "Consistencia en predicciones secuenciales"
}
```

### Análisis de Casos
- **Mejora vs MLP**: Casos donde temporal supera individual
- **Patrones únicos**: Secuencias que solo temporal detecta
- **Colapsos predecibles**: Rachas malas identificadas temprano

---

## 🚀 NEXT STEPS CONCRETOS

### Implementación Inmediata (Hoy)
1. ✅ **Features temporales**: Extender `phase3_temporal.py` existente
2. ✅ **Data pipeline**: Crear ventanas deslizantes de 5 movimientos  
3. ✅ **Modelo baseline**: 1D-CNN simple para validar approach
4. ✅ **Comparación**: Phase 3 vs Phase 2 MLP on same test set

### Esta Sesión (2-3 horas)
1. Implementar generador de features temporales robusto
2. Crear modelos CNN y GRU funcionales
3. Pipeline completo train/test/evaluate
4. Primeros resultados vs baseline Phase 2

### Criterio de Éxito
- **F1 > 0.992**: Superar Phase 2 MLP  
- **Temporal insights**: Identificar patrones únicos no vistos en MLP
- **Casos de uso claros**: Demostrar valor de análisis secuencial
- **Código producción**: Pipeline limpio y documentado

---

## 💡 HIPÓTESIS A VALIDAR

### H1: Features Temporales Añaden Valor
**Hipótesis**: Score_diff sequence patterns mejoran F1 sobre features estáticas
**Test**: Comparar MLP con features originales vs MLP con features temporales

### H2: Memoria Temporal Es Útil  
**Hipótesis**: GRU/LSTM capturan dependencias que 1D-CNN no ve
**Test**: CNN vs GRU vs CNN+GRU en mismo dataset

### H3: Detección Temprana de Colapso
**Hipótesis**: Podemos predecir rachas de errores 2-3 movimientos antes
**Test**: Precisión de predicción de blunder sequences

---

**READY TO START PHASE 3! 🚀**

*Baseline establecido: Phase 2 MLP F1=0.992*  
*Target actualizado: F1 >0.995 con insights temporales*