# ML Current State Analysis

This document compares the current repository state with the broader machine-learning vision suggested by the project structure.

## Snapshot

| Capability | Current state | Evidence |
| --- | --- | --- |
| PGN ingestion and parsing | Implemented | `../src/modules/import_games.py`, `../src/modules/pgn_utils.py`, `../src/modules/pgn_batch_loader.py` |
| Tactical and engine feature generation | Implemented | `../src/scripts/generate_features.py`, `../src/scripts/generate_features_parallel.py`, `../src/modules/stockfish_analysis.py` |
| Error-label modeling | Implemented | `../src/ml/train_error_model.py`, `../src/modules/predict_error_label.py` |
| MLflow support | Implemented | `../src/ml/mlflow_postgres_setup.py`, `../src/ml/mlflow_utils.py` |
| Rating normalization | Implemented | `../src/ml/elo_standardization.py` |
| Real-time prediction serving | Partial | `../src/ml/realtime_predictor.py` exists, but a production API boundary is not yet documented |
| AI coaching workflow | Partial / planned | `../src/ai_coach/` package exists, but end-to-end coaching orchestration is still incomplete |
| Explainability, RAG, and richer recommendations | Planned | Mentioned by project direction, but not yet represented as complete production modules |

## Main strengths

- The repository already contains meaningful preprocessing, feature generation, and training code.
- Rating standardization and MLflow utilities show movement toward more mature ML operations.
- The script inventory suggests active experimentation across data ingestion, feature extraction, and dataset export.

## Main gaps

- Serving and productization are behind the offline pipeline work.
- Documentation had drifted away from the actual file layout and needed consolidation.
- Some test execution paths still depend on environment-specific assumptions such as `PYTHONPATH` and service availability.

## Recommended next milestones

1. define a stable feature schema for both training and inference;
2. formalize model packaging and serving contracts;
3. connect prediction outputs to coaching or recommendation interfaces;
4. add clearer environment setup for automated tests and CI parity.
