# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.103] - 2026-03-26

### Added
- **Arquitectura Orquestada - Fase 0 Completada** - Documentación técnica completa para rediseño del módulo ai_chess_coach
- **Especificación Técnica** (`docs/arquitectura-orquestada/00-fase0-especificacion-tecnica.md`) - 1,200 líneas detallando:
  - 5 componentes arquitectónicos (Planner, Executor, Critic, Memory, Explainer)
  - 5 reglas de validación programáticas del Critic
  - Implementación completa de AnalyzeGameUseCase con Clean Architecture
  - Estrategia de testing, métricas y patrones de diseño
- **Interfaces y Schemas JSON** (`docs/arquitectura-orquestada/00-fase0-interfaces-json.md`) - 1,100 líneas con:
  - 7 schemas completos con validación (AnalysisOptions, AnalysisPlan, ExecutionResult, CriticResult, EnrichedResult, AnalysisReport, PlayerPatterns)
  - Modelos Pydantic con validadores personalizados
  - Ejemplos de uso y documentación OpenAPI
- **Plan de Migración** (`docs/arquitectura-orquestada/00-fase0-plan-migracion.md`) - 1,200 líneas cubriendo:
  - Estrategia de migración en 5 fases sin breaking changes
  - Implementación de dual write/read con feature flags
  - Migraciones Alembic para esquema v2.0
  - Plan de rollback y estrategia de pruebas
- **Diagramas de Arquitectura** (`docs/arquitectura-orquestada/00-fase0-diagramas-arquitectura.md`) - 930 líneas con 10 diagramas Mermaid:
  - Componentes (arquitectura de alto nivel con 4 capas)
  - Secuencia (flujo completo AnalyzeGameUseCase)
  - Flujo de datos (pipeline de transformación)
  - Base de datos (ERD con esquema v2.0)
  - Despliegue (topología Docker con puertos)
  - Estados del Critic (máquina de estados con validaciones)
  - Ciclo de vida (proceso end-to-end desde PGN hasta frontend)
  - Migración (timeline de 5 fases visualizado)
  - Dependencias (relaciones entre servicios)
  - Feature flags (control de rollback y versiones)
- **README Navegable** (`docs/arquitectura-orquestada/README.md`) - 350 líneas con índice de navegación y guía de referencia

### Changed
- **Issue Management** - Creados 6 issues para fases 0-5 (#85-90) del proyecto de Arquitectura Orquestada
- **Branch Strategy** - Creadas 6 ramas de feature para implementación por fases

### Fixed
- **Git Cleanup** - Eliminadas 10 ramas obsoletas de desarrollo anterior
- **Issue Organization** - Cerrados 10 issues legacy para mantener enfoque en nueva arquitectura

### Technical Details
- **Total Documentation**: ~4,400 líneas de especificación técnica
- **Branch**: `feature/arquitectura-orquestada-fase0-documentacion`
- **Commits**: 5 commits (b2c60c8, 58538fc, f678c97, 8f3d7f0, 1e8ec3d)
- **Issue Closed**: #85 - Fase 0: Documentación y Preparación
- **Architecture Pattern**: Clean Architecture + Planner/Executor/Critic/Memory/Explainer
- **Migration Strategy**: 5 phases with feature flags (ENABLE_ORCHESTRATED_ANALYSIS, ENABLE_DUAL_WRITE, PREFER_VERSION)
- **Design Patterns**: Use Case, Strategy, Chain of Responsibility, Builder, Repository, Facade

### Next Steps
- **Fase 1**: Implementación de Planner + Executor + Memory (Issue #86)
- **Database**: Crear migraciones Alembic para tablas move_analyses y player_patterns
- **Services**: Implementar PlannerService, ExecutorService, MemoryService con feature flags
- **Testing**: Unit tests e integration tests para flujo Planner → Executor → Memory

---

## [v0.1.108] - 2026-03-26

### Added
- **Arquitectura Orquestada - Fase 1 Completada** - Implementación core de Planner, Executor y Memory con ~1,650 líneas de código
- **Database Migration** (`alembic/versions/d65ac6f4b42a_add_move_analyses_and_player_patterns_.py`) - Migración completa con:
  - Tabla `move_analyses` (25 columnas): game_id, player_id, ply, move_san, FENs, evaluaciones engine, features JSONB, tactical_tags[], ML predictions, RAG context JSONB, explanation, critic validation, metadata
  - Tabla `player_patterns` (11 columnas): player_id UNIQUE, estadísticas agregadas, error_distribution JSONB, frequent_tactics JSONB, weak_phases[], phase_error_rates JSONB, improvement_trend, error_clusters JSONB
  - 7 índices optimizados (game_ply composite, player_created DESC, version, ml_prediction, critic_consistent, player_patterns_last_updated)
  - 6 constraints (CHECK para confidence/score 0-1, UNIQUE game_id+ply+version)
  - Foreign keys con CASCADE delete desde games/users
  - Rollback completo en downgrade()
- **Pydantic Schemas** (`src/ai_coach/orchestrated/schemas.py`) - 7 modelos con validación (~420 líneas):
  - `AnalysisOptions`: depth (10-40, múltiplo de 5), enable_ml/rag/cv, elo_threshold (800-3000), focus_mode enum (critical/full/tactical/positional)
  - `AnalysisPlan`: game_id UUID, target_moves, analysis_modes, priorities dict, metadata
  - `ExecutionResult`: Análisis completo con engine evals, features dict, phase enum, MLPrediction opcional, RAGContext opcional, auto score_diff @validator
  - `CriticResult`: is_consistent bool, confidence (0-1), ValidationIssue list, passed/failed rules, @validator previene consistencia con errores
  - `EnrichedResult`: Wrapper de execution + explanation + critique, @property helpers (is_high_quality >0.85, requires_review <0.70)
  - `AnalysisReport`: Reporte a nivel de partida con enriched_results[], @property consistency_rate y avg_confidence
  - `PlayerPatterns`: Estadísticas agregadas (error_distribution, frequent_tactics, weak_phases, trends)
  - Todos con Config.schema_extra examples y validadores de negocio
- **PlannerService** (`src/ai_coach/orchestrated/planner_service.py`) - 300 líneas, decisión de QUÉ analizar:
  - `build_plan()`: Entry point con AnalysisOptions → AnalysisPlan
  - Identificación de momentos críticos con scoring basado en 5 criterios:
    * Eval swing (>100cp=10pts, 50-100cp=5pts, 20-50cp=2pts)
    * Material change (<-200=8pts, <-100=4pts)
    * Tactical tags (2pts cada uno)
    * Error labels (blunder=10pts, mistake=7pts, inaccuracy=4pts)
    * Phase adjustment según focus_mode
  - 4 focus modes (critical=threshold 5 max 20 moves, full=0/200, tactical=3/30, positional=4/25)
  - Asignación de prioridades (high/medium/low) por move
  - Logging extensivo (info/debug) con tiempos y estadísticas
- **ExecutorService** (`src/ai_coach/orchestrated/executor_service.py`) - 450 líneas async, producción de EVIDENCIA:
  - `async execute()`: Loop principal iterando target_moves del plan
  - Pipeline de 4 pasos por movimiento:
    1. Engine analysis (bloqueante) - eval_before/after, score_diff, best_move/line, tactical_tags
    2. Feature extraction (depende de engine) - king_safety, material_balance, center_control, piece_activity
    3. ML + RAG en paralelo con `asyncio.gather(*tasks, return_exceptions=True)` - MLPrediction + RAGContext
    4. Ensamblaje de ExecutionResult con toda la evidencia
  - Placeholders (TODO) para integración con servicios reales (AnalysisService, FeatureService, ChessErrorPredictor, RAG)
  - Error handling robusto (try/except con continue-on-error)
  - CV support opcional en constructor
  - Logging detallado por paso con tiempos de ejecución
- **MemoryService** (`src/ai_coach/orchestrated/memory_service.py`) - 480 líneas async, persistencia de RESULTADOS:
  - Dual-write strategy con feature flags (ENABLE_DUAL_WRITE default=true, PREFER_VERSION default=v2.0)
  - `async store_move_analysis()`: Guarda EnrichedResult con dual-write v2.0 + v1.0 opcional
  - `async _store_v2_move_analysis()`: INSERT masivo en move_analyses (30 parámetros) con SQLAlchemy text() y JSONB
  - `async update_player_patterns()`: Agregación + UPSERT con ON CONFLICT(player_id) DO UPDATE
  - `_compute_player_statistics()`: Calcula error_distribution, frequent_tactics (top 10), weak_phases (error_rate >0.15), phase_error_rates, improvement_trend, recent_avg_error_rate
  - `async get_player_patterns()`: SELECT con lookback_days filter (default 30)
  - Placeholder para _store_v1_move_legacy() (backward compatibility)
  - Manejo de sesiones async con commits explícitos

### Changed
- **Module Structure** - Nuevo paquete `src/ai_coach/orchestrated/` con __init__.py exportando schemas públicos
- **Architecture** - Implementación completa del patrón Clean Architecture especificado en Fase 0
- **Async/Await** - Executor y Memory completamente asíncronos para escalabilidad
- **Parallelization** - ML + RAG ejecutan en paralelo reduciendo latencia por movimiento

### Technical Details
- **Total Code**: ~1,650 líneas de producción (migration 170, schemas 420, planner 300, executor 450, memory 480)
- **Branch**: `feature/arquitectura-orquestada-fase1-planner-executor`
- **Commits**: 2 feat commits (c6c4ca9 migration+schemas+planner, 4c28cb4 executor+memory)
- **Version**: v0.1.108-4c28cb4
- **Issue**: #86 - Fase 1: Planner + Executor + Memory (core completado)
- **Design Patterns**: Strategy, Async/Await, Feature Toggle, Repository (implicit), Chain of Responsibility (pipeline)
- **Testing Strategy**: Placeholders in place for pytest unit/integration tests
- **Performance**: asyncio.gather() parallelization reduces analyze time, async I/O for database operations

### Next Steps
- **Testing**: Crear pytest suite (unit tests para cada service, integration test e2e Planner→Executor→Memory)
- **Integration**: Reemplazar placeholders con servicios reales (AnalysisService, FeatureSummarizer, ChessErrorPredictor, RAG)
- **Fase 2**: Implementar CriticService con 5 reglas de validación programáticas (Issue #87)
- **Fase 3**: ExplainerService (LLM) + RAG improvements (Issue #88)

---

## [v0.1.43] - 2025-06-30

### Added
- **Documentation Structure Enhancement** - Comprehensive documentation improvements addressing issue #62
- **Localized Documentation Updates** - Historical v0.1.43 context: Spanish versions for major documentation files at that time included:
  - `src/architecture_es.md` - System architecture diagram and explanations in Spanish
  - `DATASETS_VOLUMES_CONFIG_es.md` - Docker volumes configuration for dataset sharing in Spanish
- **Documentation Index** - Organized navigation structure replacing requirements sections in both VERSION_BASE files
- **Docker Installation References** - Clear references to automatic dependency installation via:
  - `Dockerfile` - Main application container setup
  - `dockerfile.notebooks` - Jupyter environment setup
  - `requirements.txt` - Complete Python dependencies
  - `docker-compose.yml` - Container orchestration

### Changed
- **VERSION_BASE Files Restructured** - Documentation index now serves as primary navigation replacing basic requirements section
- **Cross-Reference Enhancement** - Better organization and linking between English and Spanish documentation versions
- **Issue Management Optimization** - Removed #MIGRATED-TODO keys from English version to prevent duplicate GitHub issues

### Fixed
- **Docker Build Issues** - Resolved pytest package installation error in Dockerfile (issue #62)
- **Documentation Organization** - Logical categorization into Core Documentation, Configuration, Architecture, Testing, and Reports sections

### Technical Details
- **Commit**: `6f8d69b6fa66173cf4e4e13d385fc061fef7ca02`
- **Author**: Sergio Salanitri
- **Date**: Mon Jun 30 15:06:47 2025 -0300
- **Branch**: `62-compartir-datasets-ente-containers`

---

## Previous Versions

### [v0.1.42] - 2025-06-30
- **Fixed Docker build**: Remove pytest packages from apt-get install
- **Resolved build error**: 'E: Unable to locate package pytest'
- **Technical Details**: Commit `e6619b7` - Fixes #62, moved pytest packages to pip installation

### [v0.1.41] - 2025-06-30
- **Git LFS Configuration**: Added Docker Git LFS support and selective volume sharing
- **Docker Updates**: Enhanced dockerfile and dockerfile.notebooks with proper Git LFS installation
- **Documentation**: Created comprehensive dataset volume sharing documentation
- **Windows Support**: Added Windows setup guide and LFS usage documentation
- **Volume Sharing**: Updated docker-compose.yml for selective export/models sharing between containers

### [v0.1.40] - 2025-06-30
- **Source Parameter Support**: Added source parameter in feature generation process (issue #59)
- **Testing Enhancements**: Associated tests for source parameter functionality
- **Feature Filtering**: Added filter by source in generate_feature process (issue #56)
- **Bug Fixes**: Fixed max-games control failure

### [v0.1.39] - 2025-06-29
- **PostgreSQL Migration**: Migrated entire system from SQLite to PostgreSQL
- **Testing Suite**: Added comprehensive tests for analyze_tactics_parallel
- **Requirements Update**: Updated requirements.txt with all references (app, notebooks, and tests)
- **Pipeline Improvements**: Enhanced analyze_tactics process with fixes and optimizations

### [v0.1.38] - 2025-06-26
- **Git LFS Setup**: Configured Git LFS for large files and processed games
- **Performance**: Optimized storage for large dataset files

## Major Releases

### [v0.2] - 2025-06-14
- **Major Version Update**: New stable version with enhanced features
- **Commit**: `09eacce` - Significant system improvements and optimizations

### [v0.1] - 2025-05-31  
- **Initial Stable Release**: Backend stabilization and core functionality
- **Training Dataset**: Successfully generating training_dataset.csv
- **Commit**: `30f47e3` - First stable version with working training dataset generation

## Recent Feature Development (June 2025)

### Dataset and Source Management
- **Multi-source Support**: Enhanced support for multiple datasets (issue #8)
- **Source Filtering**: Improved feature generation with source-based filtering
- **Data Processing**: Optimized pipeline for different data sources

### Infrastructure and DevOps  
- **Docker Optimization**: Complete containerization with Git LFS support
- **PostgreSQL Migration**: Full database migration from SQLite to PostgreSQL
- **Volume Sharing**: Intelligent dataset sharing between containers
- **Testing Framework**: Comprehensive test suite implementation

### Documentation and Localization
- **Bilingual Documentation**: Complete Spanish translations for all major docs
- **Architecture Documentation**: Detailed system architecture diagrams
- **Testing Guides**: Comprehensive testing documentation and runner guides
- **Installation Automation**: Docker-first approach with automatic dependency management

<!-- Template for future entries:

## [Unreleased]

### Added
### Changed  
### Deprecated
### Removed
### Fixed
### Security

-->
