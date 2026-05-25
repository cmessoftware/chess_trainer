# chessinsightai

ChessInsightAI is a chess analysis and training project focused on importing games, enriching them with engine and tactical signals, building machine-learning datasets, and preparing recommendation workflows for future coaching features.

## Documentation index

### Main entry points
- **[Main README](./README.md)** - Project overview, setup, roadmap, and documentation hub
- **[Version Base (English)](./VERSION_BASE.md)** - Quick start and condensed project summary
- **[Version Base (Spanish)](./VERSION_BASE_es.md)** - Spanish quick start and overview
- **[Tests Guide](./tests/README.md)** - Test runner usage and test-suite structure
- **[Architecture Notes](./src/architecture.md)** - Source-level architecture overview

### Technical documents
- **[MLflow PostgreSQL Integration](./docs/MLFLOW_POSTGRES_INTEGRATION.md)** - Theory and implementation map for experiment tracking with PostgreSQL
- **[Reliable Chess Predictions](./docs/PREDICCIONES_FIABLES_MLFLOW.md)** - Prediction pipeline concepts, current modules, and future serving work
- **[ELO Standardization Guide](./docs/ELO_STANDARDIZATION_GUIDE.md)** - Rating normalization design and implementation references
- **[Issue #21 Completion Report](./docs/ISSUE_21_COMPLETION_REPORT.md)** - Project-level summary of the rating standardization milestone
- **[Docker Development Strategy](./docs/DOCKER_DEVELOPMENT_STRATEGY.md)** - Container workflow, services, and environment responsibilities
- **[Datasets Volumes Config](./docs/DATASETS_VOLUMES_CONFIG.md)** - Theoretical storage layout for datasets, artifacts, and shared volumes
- **[Git LFS Setup Guide](./docs/GIT_LFS_SETUP_GUIDE.md)** - Guidance for handling large assets and model artifacts
- **[ML Theoretical Framework](./docs/ML_THEORETICAL_FRAMEWORK.md)** - Core ML concepts applied to chess data in this repository
- **[ML Current State Analysis](./docs/ML_CURRENT_STATE_ANALYSIS.md)** - What exists today versus what is still planned

## Current capabilities

- Import games from external sources and local PGN collections
- Analyze positions with Stockfish-oriented feature extraction
- Label tactical or error-oriented training signals
- Build machine-learning datasets and supporting exports
- Track model experiments and supporting ML utilities
- Provide a base for future coaching, recommendation, and explainability features

## Repository map

| Area | Purpose | Current status |
| --- | --- | --- |
| `src/modules/` | PGN parsing, feature engineering, tagging, reporting, and utility modules | Implemented |
| `src/scripts/` | Operational scripts for downloads, feature generation, training data, and CLI workflows | Implemented |
| `src/ml/` | MLflow setup, ELO standardization, dataset analysis, training utilities, and prediction helpers | Implemented |
| `src/services/` | Service wrappers for uploads, studies, and integration logic | Implemented |
| `src/ai_coach/` | Early coaching-oriented package structure | Partial / evolving |
| `docs/` | Technical and theoretical documentation | Being consolidated |
| `tests/` | Automated tests and test runner utilities | Implemented, environment-dependent |

## Quick start

### Docker setup (recommended)

#### Windows users
```powershell
.\build_up_clean_all.ps1
```

This script builds and starts the main application environment and related development services.

#### Manual Docker setup
```bash
docker-compose build
docker-compose up -d
```

### Local development
```bash
# Main application entry point
streamlit run app.py

# Pipeline entry point
cd src/pipeline
./run_pipeline.sh interactive
```

## Testing

### CI baseline
The repository workflow in `.github/workflows/test.yml` installs `requirements.txt` and runs:

```bash
pytest tests/
```

### Local note
Some tests assume project-specific import paths and runtime services. In this workspace, a baseline run currently fails during collection because `modules` is not available on the default `PYTHONPATH`.

## Machine-learning context

Chess games are represented primarily through PGN move sequences and derived engine features. From those inputs, the project can build datasets that capture:

- openings and move sequences
- tactical opportunities and tactical mistakes
- engine score differences and error labels
- rating context and player strength normalization
- game outcomes and quality signals

From a theoretical point of view, the repository supports several ML problem families:

- **classification** for error labels or tactical pattern categories
- **regression** for score-based or quality-based estimations
- **clustering** for player-style or dataset-segmentation studies
- **recommendation** for future training and coaching flows

Relevant implementation references include `src/modules/ml_preprocessing.py`, `src/modules/feature_engineering.py`, `src/modules/predict_error_label.py`, `src/ml/train_error_model.py`, and `src/ml/chess_error_predictor.py`.

## Status and roadmap

| Topic | Status | Notes |
| --- | --- | --- |
| PGN ingestion and dataset preparation | Implemented | Covered by modules and scripts under `src/modules/` and `src/scripts/` |
| Tactical and feature extraction | Implemented | Stockfish- and tactics-related scripts already exist |
| ELO standardization | Implemented | See `src/ml/elo_standardization.py` and related utilities |
| MLflow tracking support | Implemented | PostgreSQL setup and utilities are present in `src/ml/` |
| Real-time prediction serving | Partial | Predictor modules exist, but production API integration remains future work |
| Explainability and coaching orchestration | Planned | Mentioned by docs and package layout, not fully implemented yet |

## Credits

Developed by cmessoftware as part of practical work connected to a data-science learning path.
