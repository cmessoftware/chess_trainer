# AI Engineering Course (ChessInsightAI)

Este directorio contiene el material del curso de AI Engineering alineado con
`docs/courses/ai_enginner_roadmap`.

## Flujo principal (recomendado): PostgreSQL + pipeline real

El curso reutiliza la infraestructura del proyecto:

- extracción de features existente en `src/scripts/`
- base de datos PostgreSQL (`features`, `games`)
- seguimiento de experimentos con MLflow
- entorno conda recomendado: `chess_trainer`

### Notebooks v1 disponibles

| # | Archivo | Módulo |
|---|---------|--------|
| 1 | `01_architecture_overview.ipynb` | Foundations |
| 2 | `02_run_feature_pipeline.ipynb` | Data Pipeline |
| 3 | `03_dataset_builder.ipynb` | Dataset Generation |

### Curso base 00–12

Se agregó la estructura `docs/courses/ai_engineer_course/` con módulos:

- `00_foundations`
- `01_data_pipeline`
- `02_dataset_generation`
- `03_feature_analysis`
- `04_machine_learning`
- `05_model_evaluation`
- `06_llm_explanations`
- `07_rag_system`
- `08_ai_agents_phase1`
- `09_ai_system_architecture`
- `10_production_ai`
- `11_capstone`
- `12_phase2_agentic_system`

Incluye componentes iniciales clave:

- `data_access/features_repository.py`
- `dataset/build_training_dataset.py`
- scripts/notebooks base para módulos 3–12

## Construcción de dataset de entrenamiento

`dataset/build_training_dataset.py` construye dataset supervisado desde `features`
con target `error_label` y clases:

- `good`
- `inaccuracy`
- `mistake`
- `blunder`

Ejemplo:

```bash
conda activate chess_trainer
python docs/courses/ai_engineer_course/dataset/build_training_dataset.py \
  --db-url "$CHESS_TRAINER_DB_URL" \
  --output docs/courses/ai_engineer_course/dataset/training_dataset.parquet
```

## Nota sobre `migrate_to_sqlite.py`

`docs/courses/migrate_to_sqlite.py` se mantiene como **utilidad auxiliar** para
escenarios educativos/portables de notebooks.

No reemplaza el flujo principal del proyecto, que sigue siendo PostgreSQL.
