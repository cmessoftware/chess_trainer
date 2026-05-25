# Reliable Chess Predictions with MLflow

This document explains the theory behind reliable prediction workflows in ChessInsightAI and identifies which repository modules already support that direction.

## Goal

A reliable prediction pipeline should produce repeatable inputs, stable training outputs, traceable experiments, and clear boundaries between offline training and future online inference.

## Existing building blocks

| Layer | Repository reference | Status | Role |
| --- | --- | --- | --- |
| Feature preprocessing | [`../src/modules/ml_preprocessing.py`](../src/modules/ml_preprocessing.py) | Existing | Normalizes inputs for downstream models |
| Feature engineering | [`../src/modules/feature_engineering.py`](../src/modules/feature_engineering.py) | Existing | Builds chess-specific predictors |
| Error label prediction support | [`../src/modules/predict_error_label.py`](../src/modules/predict_error_label.py) | Existing | Classification-oriented module |
| Model training | [`../src/ml/train_error_model.py`](../src/ml/train_error_model.py) | Existing | Core ML training entry point |
| Predictor wrapper | [`../src/ml/chess_error_predictor.py`](../src/ml/chess_error_predictor.py) | Existing | Encapsulates model usage |
| Real-time predictor | [`../src/ml/realtime_predictor.py`](../src/ml/realtime_predictor.py) | Existing | Early inference-oriented helper |
| Experiment tracking | [`./MLFLOW_POSTGRES_INTEGRATION.md`](./MLFLOW_POSTGRES_INTEGRATION.md) | Implemented and documented | Supports reproducibility |
| API-grade serving layer | Not yet implemented | Future plan | Would expose stable prediction endpoints |

## Reliability principles

Reliable predictions in this repository depend on four principles:

1. **consistent input semantics** - PGN-derived features must be generated the same way in training and inference;
2. **label quality** - engine-derived error labels and tactical tags must remain well defined;
3. **experiment traceability** - each model must be traceable to data, code, and parameters;
4. **serving discipline** - future APIs must validate inputs and version models explicitly.

## Data flow concept

A theoretical end-to-end flow is:

1. ingest PGN games;
2. enrich them with Stockfish and tactical features;
3. standardize rating context;
4. train and log models with MLflow;
5. expose a prediction service for coaching or recommendation features.

The first four stages already have code support in the repository. The fifth stage is still part of the future roadmap.

## Future plan

- Add an API-facing inference contract for game or move-level predictions.
- Version feature schemas explicitly.
- Add confidence calibration and drift monitoring.
- Connect predictions to coaching modules under `../src/ai_coach/` once those flows are implemented.
