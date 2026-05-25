# 🎯 PROPUESTA DE NUEVOS ISSUES - ML Pipeline Chess Trainer

**Fecha:** 4 de Febrero de 2026  
**Análisis Base:** [ML_PROJECT_STATE_ANALYSIS.md](./ML_PROJECT_STATE_ANALYSIS.md)

---

## 🔴 PRIORIDAD CRÍTICA (Implementar Inmediatamente)

### Issue #NEW-1: Completar Etiquetado Masivo de Features
**Título:** Complete mass labeling of remaining 16,157 features with Stockfish tactical analysis

**Descripción:**
Completar el etiquetado táctico automático de las 16,157 features restantes (81% del dataset) utilizando el sistema ya implementado en `generate_features_with_tactics.py`.

**Estado Actual:**
- ✅ Sistema de etiquetado operativo con Stockfish 17 + NNUE
- ✅ 3,790 features etiquetadas (19% completado)
- ⏳ 16,157 features pendientes de etiquetado

**Tareas:**
- [ ] Ejecutar proceso de etiquetado continuo (ETA: 2-3 días)
- [ ] Monitorear progreso cada 1,000 features etiquetadas
- [ ] Verificar distribución balanceada de labels
- [ ] Validar calidad del etiquetado (muestreo aleatorio)

**Criterio de Completitud:**
- [x] 100% de features etiquetadas (19,947 records)
- [x] Distribución balanceada verificada
- [x] Proceso sin errores críticos

**Prioridad:** 🔴 CRÍTICA  
**Estimación:** 2-3 días (proceso continuo)  
**Dependencias:** Ninguna (ya implementado)  
**Fase del Roadmap:** Fase 1  

---

### Issue #NEW-2: Establecer Baseline ML en Phase 1 con MLflow
**Título:** Establish Phase 1 ML baseline with systematic MLflow tracking

**Descripción:**
Ejecutar `phase1_baseline.py` para establecer baseline oficial con Logistic Regression L2, L1 y RandomForest, registrando todas las métricas en MLflow.

**Estado Actual:**
- ✅ Script `phase1_baseline.py` implementado
- ❌ Sin runs registrados en MLflow
- ❌ Métricas no consolidadas

**Tareas:**
- [ ] Ejecutar training con dataset completo (19,947 features)
- [ ] Registrar métricas en MLflow:
  - F1 macro (métrica principal)
  - Accuracy
  - Precision/Recall por clase
  - Confusion matrix (artifact)
  - Feature importance (artifact)
- [ ] Validar criterios de avance:
  - F1 macro > 0.70
  - Confusión grave (good ↔ blunder) < 5%
- [ ] Documentar resultados

**Criterio de Completitud:**
- [x] 3 modelos entrenados y registrados en MLflow
- [x] F1 macro > 0.70 alcanzado
- [x] Confusión grave < 5%
- [x] Modelo baseline seleccionado y documentado

**Prioridad:** 🔴 CRÍTICA  
**Estimación:** 3-5 días  
**Dependencias:** Issue #NEW-1 (80% completado es suficiente para empezar)  
**Fase del Roadmap:** Fase 1  

---

### Issue #NEW-3: Crear Documento ML_THEORETICAL_FRAMEWORK.md
**Título:** Create comprehensive ML theoretical framework documentation

**Descripción:**
Crear documento completo con conceptos teóricos de algoritmos ML y ejemplos concretos aplicados a chess_trainer.

**Estado Actual:**
- ❌ Documento NO existe (referenciado pero ausente)
- ✅ Concepto definido en análisis de estado

**Tareas:**
- [ ] Crear estructura del documento
- [ ] Documentar algoritmos con teoría:
  - Regresión Lineal/Múltiple
  - Regresión Logística
  - K-Nearest Neighbors
  - K-Means Clustering
  - Naive Bayes
  - Random Forest
  - Gradient Boosting
  - SVM
  - Neural Networks (MLP)
  - LSTM/GRU
- [ ] Agregar ejemplos concretos para chess_trainer
- [ ] Incluir casos de sobre/subajuste
- [ ] Agregar diagramas y visualizaciones

**Contenido Requerido por Algoritmo:**
```markdown
### [Algoritmo]
**Teoría:** [Explicación conceptual]
**Fórmula:** [Si aplica]
**Aplicación en Chess Trainer:** [Uso específico]
**Ejemplo Concreto:** [Código + caso de uso]
**Ventajas:** [...]
**Desventajas:** [...]
**Casos de Uso:** [Cuándo usarlo]
```

**Criterio de Completitud:**
- [x] 10 algoritmos documentados
- [x] Ejemplos concretos para cada uno
- [x] Sección de sobre/subajuste con casos
- [x] Revisión técnica aprobada

**Prioridad:** 🔴 CRÍTICA  
**Estimación:** 4-6 días  
**Dependencias:** Ninguna (documentación)  
**Ubicación:** `docs/ML_THEORETICAL_FRAMEWORK.md`

---

### Issue #NEW-7: Pipeline ML Unificado y Orquestado
**Título:** Unified and orchestrated ML pipeline with centralized execution

**Descripción:**
Integrar scripts dispersos en un pipeline ML central que orqueste todo el flujo desde data loading hasta model deployment.

**Estado Actual:**
- 🟡 Scripts individuales funcionando
- ❌ Sin orquestación central
- ❌ Ejecución manual y dispersa

**Tareas:**
- [ ] Crear `src/ml/pipeline_orchestrator.py`
- [ ] Definir stages del pipeline:
  1. Data Loading & Validation
  2. Feature Engineering
  3. Data Preprocessing
  4. Model Training
  5. Model Evaluation
  6. Model Registration
  7. Model Deployment
- [ ] Integrar con MLflow Pipelines
- [ ] Agregar logging y monitoring
- [ ] Tests de integración end-to-end
- [ ] Documentación de uso

**Arquitectura Propuesta:**
```python
class MLPipelineOrchestrator:
    def __init__(self, config):
        self.stages = [
            DataLoadingStage(),
            FeatureEngineeringStage(),
            PreprocessingStage(),
            TrainingStage(),
            EvaluationStage(),
            RegistrationStage(),
            DeploymentStage()
        ]
    
    def run(self, experiment_name):
        # Execute all stages sequentially
        pass
```

**Criterio de Completitud:**
- [x] Pipeline ejecutable end-to-end
- [x] Integración con MLflow completa
- [x] Tests pasando
- [x] Documentación actualizada

**Prioridad:** 🔴 CRÍTICA  
**Estimación:** 1 semana  
**Dependencias:** Issue #NEW-2  
**Fase del Roadmap:** Fase 1-3  

---

## 🟡 PRIORIDAD ALTA (Implementar en Sprint 1-2)

### Issue #NEW-4: API de Recomendaciones por Partida Individual
**Título:** Implement game-specific recommendations API endpoint

**Descripción:**
Crear endpoint FastAPI que analice una partida y genere recomendaciones específicas de mejora.

**Estado Actual:**
- ✅ Modelo de predicción implementado
- ❌ Sin endpoint de análisis
- ❌ Sin servicio de recomendaciones

**Tareas:**
- [ ] Crear `src/api/routes/game_analysis.py`
- [ ] Implementar `src/services/game_analysis_service.py`
- [ ] Endpoint: `POST /api/v1/games/{game_id}/analyze`
- [ ] Endpoint: `GET /api/v1/games/{game_id}/recommendations`
- [ ] Integrar con modelos MLflow
- [ ] Sistema de explicabilidad básico
- [ ] Tests de API
- [ ] Documentación OpenAPI

**Request/Response:**
```json
// Request: POST /api/v1/games/{game_id}/analyze
{
  "include_recommendations": true,
  "detail_level": "full"
}

// Response:
{
  "game_id": "uuid",
  "analysis": {
    "total_moves": 42,
    "blunders": 2,
    "mistakes": 5,
    "inaccuracies": 8,
    "accuracy": 85.7
  },
  "critical_positions": [...],
  "recommendations": [
    {
      "move_number": 15,
      "error_type": "blunder",
      "description": "Hanging knight on e4",
      "better_move": "Nf3",
      "explanation": "Protect the knight or move it to safety"
    }
  ]
}
```

**Criterio de Completitud:**
- [x] Endpoints funcionando
- [x] Integración con ML model
- [x] Tests pasando
- [x] Documentación completa

**Prioridad:** 🟡 ALTA  
**Estimación:** 1 semana  
**Dependencias:** Issue #NEW-2  
**Fase del Roadmap:** Fase 5  

---

## 🟢 PRIORIDAD MEDIA (Implementar en Sprint 2-3)

### Issue #NEW-5: Sistema de Clustering por Nivel ELO
**Título:** ELO-based player clustering for pattern identification

**Descripción:**
Implementar K-Means clustering para identificar patrones comunes de errores por nivel de ELO.

**Estado Actual:**
- ✅ Dataset con ELO estandarizado
- ❌ Sin análisis de clustering
- ❌ Sin identificación de patrones por nivel

**Tareas:**
- [ ] Crear `src/ml/level_clustering.py`
- [ ] Implementar K-Means clustering por ELO
- [ ] Análisis de patrones tácticos por cluster
- [ ] Visualizaciones de clusters
- [ ] Identificación de características comunes
- [ ] Sistema de recomendaciones por nivel
- [ ] Notebook de análisis exploratorio

**Algoritmo:**
```python
# Definir rangos de ELO
ranges = [
    (800, 1200),   # Beginner
    (1200, 1600),  # Intermediate
    (1600, 2000),  # Advanced
    (2000, 2400),  # Expert
    (2400, 3000)   # Master
]

# K-Means por cada rango
for elo_range in ranges:
    data = filter_by_elo(df, elo_range)
    clusters = kmeans.fit_predict(data)
    analyze_patterns(clusters)
```

**Criterio de Completitud:**
- [x] Clustering implementado
- [x] Análisis de patrones documentado
- [x] Visualizaciones generadas
- [x] Sistema de recomendaciones por nivel

**Prioridad:** 🟢 MEDIA  
**Estimación:** 1 semana  
**Dependencias:** Issue #NEW-2  
**Fase del Roadmap:** Fase 4  

---

### Issue #NEW-6: Generador de Reportes PDF Personalizados
**Título:** Personalized PDF report generator with statistics and recommendations

**Descripción:**
Sistema completo de generación de reportes PDF con estadísticas, gráficos y recomendaciones personalizadas.

**Estado Actual:**
- ❌ Sin generación de reportes
- ❌ Sin templates

**Tareas:**
- [ ] Crear `src/services/report_generator.py`
- [ ] Implementar templates HTML con Jinja2
- [ ] Generar gráficos con Matplotlib/Seaborn
- [ ] Exportar a PDF con ReportLab/WeasyPrint
- [ ] Endpoint: `POST /api/v1/reports/generate`
- [ ] Endpoint: `GET /api/v1/reports/{report_id}/download`
- [ ] Tests de generación
- [ ] Ejemplos de reportes

**Contenido del Reporte:**
1. **Perfil del Jugador**
   - Nombre, ELO, rango de fechas
   - Partidas analizadas
2. **Estadísticas Generales**
   - Win rate, accuracy promedio
   - Errores por partida
3. **Análisis por Fase del Juego**
   - Apertura, medio juego, final
   - Fortalezas y debilidades
4. **Análisis por Color**
   - Blancas vs negras
5. **Análisis de Aperturas**
   - Aperturas frecuentes
   - Win rate por apertura
6. **Recomendaciones**
   - Top 5 áreas de mejora
   - Ejercicios sugeridos

**Criterio de Completitud:**
- [x] Generador funcionando
- [x] Templates creados
- [x] Endpoints implementados
- [x] Ejemplos generados

**Prioridad:** 🟢 MEDIA  
**Estimación:** 1.5 semanas  
**Dependencias:** Issue #NEW-4  
**Fase del Roadmap:** Fase 5  

---

### Issue #NEW-8: Features Temporales y Presión de Tiempo
**Título:** Temporal features and time pressure analysis implementation

**Descripción:**
Implementar features relacionadas con tiempo y secuencias de errores para análisis temporal (Fase 3).

**Estado Actual:**
- ❌ Sin features temporales
- ❌ Sin análisis de presión de tiempo

**Tareas:**
- [ ] Agregar features a `generate_features_with_tactics.py`:
  - `time_pressure`: Indicador de presión temporal
  - `time_left`: Tiempo restante en reloj
  - `move_time`: Tiempo usado en jugada
  - `prev_error_count`: Errores en últimas N jugadas
  - `error_streak`: Racha de errores consecutivos
- [ ] Migración de BD para nuevas columnas
- [ ] Reprocesar dataset con nuevos features
- [ ] Tests de feature engineering
- [ ] Documentación actualizada

**Criterio de Completitud:**
- [x] 5+ features temporales agregados
- [x] Dataset reprocesado
- [x] Tests pasando
- [x] Documentación actualizada

**Prioridad:** 🟢 MEDIA  
**Estimación:** 4-5 días  
**Dependencias:** Issue #NEW-2  
**Fase del Roadmap:** Fase 3  

---

### Issue #NEW-9: Sistema de Validación Cross-Dataset
**Título:** Cross-dataset validation system for model generalization

**Descripción:**
Implementar sistema de validación cruzada entre diferentes datasets (personal, elite, novice, FIDE) para verificar generalización del modelo.

**Estado Actual:**
- ✅ Múltiples datasets disponibles
- ❌ Sin validación cruzada sistemática

**Tareas:**
- [ ] Crear `src/ml/cross_dataset_validator.py`
- [ ] Implementar validación:
  - Train on personal, test on elite
  - Train on elite, test on personal
  - Train on novice, test on FIDE
  - etc.
- [ ] Métricas de generalización
- [ ] Análisis de performance degradation
- [ ] Notebook con visualizaciones
- [ ] Reporte de generalización

**Criterio de Completitud:**
- [x] Validación cruzada implementada
- [x] Métricas consolidadas
- [x] Reporte generado
- [x] Insights documentados

**Prioridad:** 🟢 MEDIA  
**Estimación:** 4-5 días  
**Dependencias:** Issue #NEW-2  
**Fase del Roadmap:** Fase 1  

---

## 🔵 PRIORIDAD BAJA (Mejoras Futuras)

### Issue #NEW-10: Dashboard de Métricas ML en Tiempo Real
**Título:** Real-time ML metrics dashboard with MLflow integration

**Descripción:**
Dashboard interactivo en React para visualizar experimentos de MLflow, métricas en tiempo real y comparación de modelos.

**Estado Actual:**
- ✅ MLflow UI disponible
- ❌ Sin dashboard personalizado

**Tareas:**
- [ ] Crear componente React para dashboard
- [ ] Integrar con API de MLflow
- [ ] Visualizaciones:
  - Experimentos activos
  - Métricas por modelo
  - Comparación de runs
  - Feature importance
  - Confusion matrices
- [ ] Actualización en tiempo real
- [ ] Filtros y búsqueda

**Criterio de Completitud:**
- [x] Dashboard funcionando
- [x] Integración con MLflow
- [x] Visualizaciones implementadas
- [x] Tests E2E pasando

**Prioridad:** 🔵 BAJA  
**Estimación:** 1 semana  
**Dependencias:** Issue #NEW-7  
**Fase del Roadmap:** Fase 5  

---

## 📋 RESUMEN DE ISSUES PROPUESTOS

| Issue # | Título                      | Prioridad | Estimación  | Fase     | Sprint     |
| ------- | --------------------------- | --------- | ----------- | -------- | ---------- |
| #NEW-1  | Completar etiquetado masivo | 🔴 CRÍTICA | 2-3 días    | Fase 1   | Sprint 1   |
| #NEW-2  | Establecer baseline Phase 1 | 🔴 CRÍTICA | 3-5 días    | Fase 1   | Sprint 1   |
| #NEW-3  | Documento teórico ML        | 🔴 CRÍTICA | 4-6 días    | Docs     | Sprint 1   |
| #NEW-7  | Pipeline ML unificado       | 🔴 CRÍTICA | 1 semana    | Fase 1-3 | Sprint 1   |
| #NEW-4  | API de recomendaciones      | 🟡 ALTA    | 1 semana    | Fase 5   | Sprint 1-2 |
| #NEW-5  | Clustering por nivel ELO    | 🟢 MEDIA   | 1 semana    | Fase 4   | Sprint 2   |
| #NEW-6  | Reportes PDF                | 🟢 MEDIA   | 1.5 semanas | Fase 5   | Sprint 2   |
| #NEW-8  | Features temporales         | 🟢 MEDIA   | 4-5 días    | Fase 3   | Sprint 2-3 |
| #NEW-9  | Validación cross-dataset    | 🟢 MEDIA   | 4-5 días    | Fase 1   | Sprint 2-3 |
| #NEW-10 | Dashboard ML                | 🔵 BAJA    | 1 semana    | Fase 5   | Sprint 3+  |

**Total Estimado:** 7-9 semanas de desarrollo

---

## 🎯 ESTRATEGIA DE IMPLEMENTACIÓN

### Sprint 1 (Semanas 1-3): Foundation
**Objetivo:** Establecer baseline ML sólido
- Issues: #NEW-1, #NEW-2, #NEW-3, #NEW-7

### Sprint 2 (Semanas 4-5): Advanced Analysis
**Objetivo:** Análisis avanzado y recomendaciones
- Issues: #NEW-4, #NEW-5, #NEW-6

### Sprint 3 (Semanas 6-8): Temporal & Optimization
**Objetivo:** Análisis temporal y optimización
- Issues: #NEW-8, #NEW-9

### Sprint 4+ (Semanas 9+): Polish & Extras
**Objetivo:** Mejoras y features adicionales
- Issues: #NEW-10, otros

---

## 📝 PLANTILLA PARA CREAR ISSUES EN GITHUB

```markdown
## 🎯 Objetivo
[Descripción breve del objetivo]

## 📊 Estado Actual
- ✅ [Completado]
- 🟡 [En progreso]
- ❌ [Pendiente]

## ✅ Tareas
- [ ] Tarea 1
- [ ] Tarea 2
- [ ] Tarea 3

## 🎯 Criterio de Completitud
- [ ] Criterio 1
- [ ] Criterio 2

## 📚 Dependencias
- Issue #XX
- Issue #YY

## 🔗 Referencias
- [Documento relacionado](./path/to/doc.md)

## 📅 Estimación
X días/semanas

## 🏷️ Labels
- priority-critical / priority-high / priority-medium / priority-low
- phase-1 / phase-2 / phase-3 / phase-4 / phase-5
- type-ml / type-api / type-docs / type-infrastructure
```

---

**Documento generado por:** GitHub Copilot  
**Fecha:** 4 de Febrero de 2026  
**Para revisión interactiva con el usuario**
