# 📁 Organización del Proyecto - Chess Trainer

Este documento describe la estructura organizada del proyecto después de la reorganización del 4 de febrero de 2026.

## 🎯 Objetivo de la Reorganización

Limpiar la raíz del proyecto moviendo scripts, resultados de análisis ML, logs y archivos de test a sus ubicaciones correctas para mejorar la mantenibilidad y navegación del proyecto.

---

## 📂 Estructura de Directorios

### Raíz del Proyecto
```
chess_trainer/
├── README.md                      # Documentación principal
├── requirements*.txt              # Dependencias Python
├── docker-compose.yml             # Orquestación de servicios
├── alembic.ini                    # Configuración de migraciones DB
├── pytest.ini                     # Configuración de tests
├── VERSION                        # Versionado del proyecto
├── .env                          # Variables de entorno (no versionado)
├── *-helpers.ps1                 # Scripts PowerShell de utilidad frecuente
├── *.sh                          # Scripts Bash de automatización
└── src/                          # Código fuente principal
```

**Nota:** La raíz solo contiene archivos de configuración esenciales y scripts de orquestación de uso muy frecuente.

---

## 📦 Directorio `src/`

### `src/scripts/` - Scripts de Automatización y Utilidades

**Propósito:** Scripts ejecutables para tareas específicas del proyecto (import, feature engineering, verificación).

**Archivos Clave:**
```
src/scripts/
├── execute_phase1_baseline.py          # ⭐ Ejecutar entrenamiento Phase 1
├── import_pgns_parallel.py              # Importar PGNs en paralelo
├── generate_features_with_tactics.py    # Feature engineering con Stockfish
├── verify_features.py                   # Verificar features en DB
├── check_schema.py                      # Verificar esquema de DB
├── debug_pagination.py                  # Debug de paginación
└── [80+ scripts de data pipeline]
```

**Uso Típico:**
```bash
# Entrenar modelo baseline
python src/scripts/execute_phase1_baseline.py

# Generar features
python src/scripts/generate_features_with_tactics.py

# Importar PGNs
python src/scripts/import_pgns_parallel.py --source elite --workers 4
```

---

### `src/ml/` - Machine Learning Pipeline

**Propósito:** Código ML, modelos entrenados, y análisis de datos.

**Estructura:**
```
src/ml/
├── phase1_baseline.py              # Baseline models (Logistic, RF)
├── phase2_*.py                     # Phase 2 models (MLP, segmented)
├── phase3_temporal.py              # Temporal models (LSTM/GRU)
├── mlflow_utils.py                 # Utilidades MLflow
├── elo_standardization.py          # Normalización de ELO
├── results/                        # ⭐ Resultados de entrenamientos
│   ├── classification_report_logistic_l2.csv
│   ├── classification_report_logistic_l2.txt
│   ├── confusion_matrix_logistic_l2.png
│   └── predictions_results.parquet
└── mlflow.db                       # Base de datos MLflow (local)
```

**Archivos Importantes:**
- **phase1_baseline.py**: Implementación de modelos baseline (F1=0.890)
- **results/**: Reportes CSV, matrices de confusión, predicciones
- **mlflow.db**: Tracking de experimentos (complementa mlruns/)

---

### `src/config/` - Scripts de Inicialización

**Propósito:** Scripts de configuración e inicialización de servicios.

**Archivos:**
```
src/config/
├── init_api.py                     # Inicializar FastAPI
├── init_frontend.py                # Inicializar React frontend
└── launch_chess_trainer.py         # Lanzar aplicación completa
```

---

### `src/api/`, `src/frontend/`, `src/streamlit/`

Estructuras de código para backend (FastAPI), frontend (React), y dashboards (Streamlit). No modificadas en esta reorganización.

---

## 🧪 Directorio `tests/`

### `tests/integration/` - Tests de Integración

**Propósito:** Tests que verifican integración entre componentes (DB, API, frontend).

**Archivos Movidos:**
```
tests/integration/
├── test_chess_board_integration.py
├── test_database_connector.py
├── test_games_browser.py
├── test_postgresql_connection.py
└── test_sprint1_integration.py
```

**Uso:**
```bash
pytest tests/integration/ -v
```

---

## 📊 Directorio `logs/`

**Propósito:** Logs de ejecución organizados por componente.

**Estructura:**
```
logs/
├── feature_engineering/
│   ├── generate_features_with_tactics.log    # 1.4 MB
│   └── complete_error_labels.log             # 1.6 GB (proceso masivo)
└── analyze.log
```

**Nota:** Los logs de feature engineering son grandes (>1GB) y se mantienen para debugging histórico.

---

## 📄 Directorio `docs/`

**Propósito:** Documentación técnica y guías del proyecto.

**Archivos Añadidos:**
```
docs/
├── high_priority_issues_summary.json    # Resumen de issues críticos
├── test_board_refresh.md                # Documentación de tests
├── PHASE1_BASELINE_EXECUTION.md         # Tracking de Phase 1
├── ML_THEORETICAL_FRAMEWORK.md          # Marco teórico ML (3,500 líneas)
├── ML_PROJECT_STATE_ANALYSIS.md         # Análisis de estado del proyecto
└── [50+ documentos técnicos]
```

---

## 🧪 Directorio `test_data/`

**Propósito:** Datos de prueba y fixtures.

**Estructura:**
```
test_data/
└── postman/
    └── postman_test_cases.csv           # Casos de prueba API
```

---

## 🗂️ Directorios de Datos y Artefactos

### `mlruns/` - MLflow Tracking Store
Experimentos de MLflow (file-based tracking). Generado automáticamente.

### `mlartifacts/` - MLflow Artifacts
Modelos serializados, gráficos, archivos de experimentos.

### `data/` - Datasets del Proyecto
```
data/
└── games/
    ├── elite/              # Partidas de jugadores elite (FIDE 2000+)
    ├── personal/           # Partidas del usuario
    ├── novice/             # Partidas de principiantes
    ├── stockfish/          # Partidas contra Stockfish
    └── fide/               # Partidas FIDE oficiales
```

### `models/` - Modelos Entrenados
Modelos ML finales para producción.

### `reports/` - Reportes Generados
Reportes PDF, análisis estadísticos, gráficos.

---

## 🚫 Archivos Eliminados/No Versionados

**`.gitignore` incluye:**
- `mlruns/` - Tracking local de MLflow
- `mlartifacts/` - Artefactos de experimentos
- `logs/*.log` - Logs de ejecución
- `src/ml/results/*.png` - Matrices de confusión
- `src/ml/results/*.parquet` - Datasets de predicciones
- `__pycache__/` - Archivos compilados Python
- `.venv/` - Entorno virtual Python

---

## 📋 Checklist de Organización Completada

- ✅ **Scripts:** Movidos a `src/scripts/` (execute_phase1_baseline.py, verify_features.py, etc.)
- ✅ **Resultados ML:** Movidos a `src/ml/results/` (classification reports, confusion matrices)
- ✅ **Logs:** Movidos a `logs/feature_engineering/` (generate_features_with_tactics.log, etc.)
- ✅ **Tests de Integración:** Movidos a `tests/integration/` (test_*.py)
- ✅ **Inicialización:** Movidos a `src/config/` (init_api.py, init_frontend.py, launch_chess_trainer.py)
- ✅ **Documentación:** Movida a `docs/` (high_priority_issues_summary.json, test_board_refresh.md)
- ✅ **Test Data:** Movido a `test_data/postman/` (postman_test_cases.csv)
- ✅ **README:** Actualizado con rutas correctas
- ✅ **Raíz Limpia:** Solo archivos de configuración esenciales y scripts de orquestación

---

## 🎯 Beneficios de la Organización

1. **Mantenibilidad:** Estructura clara facilita encontrar y modificar código
2. **Escalabilidad:** Fácil añadir nuevos scripts/modelos en ubicaciones lógicas
3. **Colaboración:** Estructura estándar reduce curva de aprendizaje
4. **CI/CD:** Paths organizados facilitan automatización de tests y despliegues
5. **Profesionalismo:** Estructura limpia transmite calidad del proyecto

---

## 🔄 Migraciones Futuras

**Consideraciones para próximas reorganizaciones:**
- Mover scripts PowerShell/Bash menos usados a `scripts/helpers/`
- Consolidar notebooks en `notebooks/` con estructura por fase ML
- Archivar scripts obsoletos marcados como `.old` o `.borrar`
- Crear `src/utils/` para módulos compartidos entre scripts

---

## 📞 Referencias

- **README Principal:** [README.md](../README.md)
- **Guía ML:** [ML_COMPLETE_GUIDE.md](ML_COMPLETE_GUIDE.md)
- **Docker Strategy:** [DOCKER_DEVELOPMENT_STRATEGY.md](DOCKER_DEVELOPMENT_STRATEGY.md)
- **Copilot Instructions:** [.github/copilot-instructions.md](../.github/copilot-instructions.md)

---

_Última actualización: 2026-02-04_  
_Reorganización ejecutada por: GitHub Copilot Agent_
