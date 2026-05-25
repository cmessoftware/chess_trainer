# Tests & Verification Scripts

Esta carpeta contiene scripts de testing, verificación y exploración del sistema.

## Organización

### 📊 Scripts SHAP
Scripts para testing y exploración del sistema SHAP:
- `check_shap_tables.py` - Verificar tablas SHAP en la base de datos
- `verify_shap_counts*.py` - Verificar conteos de SHAP values
- `explore_shap_view.py` - Explorar vista `shap_values_with_games`
- `test_shap_*.py` - Tests del endpoint SHAP
- `quick_test_shap_endpoint.py` - Test rápido del endpoint
- `verify_shap_system.py` - Verificación completa del sistema SHAP
- `verify_analysis_shap.py` - Verificación de análisis con SHAP
- `SHAP_API_EXAMPLES.py` - Ejemplos de uso de la API SHAP
- `show_shap_dashboard.py` - Dashboard de SHAP values
- `show_shap_with_games.py` - Visualización SHAP con partidas
- `populate_shap_database.py` - Popular base de datos con SHAP
- `example_llm_shap_analysis.py` - **[NUEVO]** Ejemplo de análisis con LLM usando move context

### 🗄️ Scripts Base de Datos
Scripts de exploración y verificación de la base de datos:
- `check_games_schema.py` - Verificar esquema de tabla `games`
- `check_features_schema.py` - Verificar esquema de tabla `features`
- `check_features_status.py` - Estado de features generadas
- `find_cmess_manuelfrp_games.py` - Buscar partidas específicas
- `find_games_with_features.py` - Buscar partidas con features
- `get_test_games.py` - Obtener partidas para testing
- `check_shap_db.py` - Verificar base de datos SHAP

### 🔍 Scripts Análisis
Scripts para testing de análisis y predicciones:
- `test_analysis_debug.py` - Debug de sistema de análisis
- `test_analysis_service_direct.py` - Test directo del servicio
- `check_analysis_19.py` - Verificar análisis específico
- `check_latest_analysis.py` - Verificar último análisis
- `test_ml_error_prediction.py` - Test predicción de errores ML

### 🧹 Scripts Limpieza
Scripts de limpieza y mantenimiento:
- `cleanup_empty_analyses.py` - Limpiar análisis vacíos
- `clean_all_analyses.py` - Limpiar todos los análisis

### ⚙️ Scripts Features
Scripts de generación y verificación de features:
- `verify_features.py` - Verificar features generadas
- `generate_features_specific.py` - Generar features específicas
- `gen_features_simple.py` - Generador simple de features

### 🔧 Scripts Utilitarios
Scripts de corrección y utilidades:
- `fix_analysis_auth.py` - Corregir autenticación en análisis
- `fix_main.py` - Fix temporal para main

### 📋 Otros Tests
Scripts de testing existentes:
- `test_api_endpoints.py`
- `test_elo_*.py`
- `test_fide_import.py`
- `test_lichess_upload.py`
- `test_mlflow_postgres_integration.py`
- `test_ml_preprocessing.py`
- `test_survivorship_*.py`
- `test_tactical_*.py`
- `test_training_recommender*.py`
- `test_upload_page.py`
- `verify_batch.py`
- `verify_processing.py`

## Uso

Estos scripts son para desarrollo y verificación. **NO deben ejecutarse en producción**.

### Ejecutar desde root del proyecto:
```bash
conda activate chess_trainer
python tests/verification/check_shap_tables.py
```

### Ejecutar con pytest:
```bash
pytest tests/verification/test_shap_simple.py -v
```

## Notas

- Scripts creados durante sesiones de desarrollo/debug
- Algunos scripts pueden tener credenciales hardcoded (solo para local)
- Mantener actualizados con cambios en esquema de BD

---
_Última actualización: 2026-02-28_
