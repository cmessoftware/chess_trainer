# AI Engineer Course (ChessInsightAI)

Este curso implementa la base de la especificación `docs/courses/ai_enginner_roadmap` reutilizando la infraestructura real del proyecto.

## Principios
- Flujo principal: **PostgreSQL + scripts existentes de `src/scripts/` + MLflow**.
- No se reimplementa parser PGN ni extracción de features.
- Los notebooks v1 de `docs/courses/` se mantienen como entrada inicial.
- `migrate_to_sqlite.py` se conserva solo como utilidad auxiliar/portable para notebooks, no como flujo principal de producción.

## Estructura
- `00_foundations` a `12_phase2_agentic_system`: módulos del curso.
- `data_access/features_repository.py`: acceso portable (PostgreSQL-first) a tabla `features`.
- `dataset/build_training_dataset.py`: construcción de dataset con target `error_label`.

## Requisitos de entorno
Usar el conda env `chess_trainer` recomendado por el proyecto.
