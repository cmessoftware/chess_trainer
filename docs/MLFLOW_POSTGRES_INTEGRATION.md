# MLflow PostgreSQL Integration

This document describes the theoretical role of MLflow with PostgreSQL in ChessInsightAI and maps that role to the modules that already exist in the repository.

## Purpose

MLflow provides a structured place to track model-training runs, parameters, metrics, and artifacts. PostgreSQL is the durable metadata backend that makes this tracking workflow more reliable than a local SQLite-only setup.

## Current implementation map

| Component | Repository reference | Status | Notes |
| --- | --- | --- | --- |
| MLflow database initialization | [`../src/ml/init_mlflow_db.py`](../src/ml/init_mlflow_db.py) | Existing | Prepares database objects for MLflow metadata |
| PostgreSQL-oriented setup | [`../src/ml/mlflow_postgres_setup.py`](../src/ml/mlflow_postgres_setup.py) | Existing | Encapsulates backend configuration logic |
| Utility helpers | [`../src/ml/mlflow_utils.py`](../src/ml/mlflow_utils.py) | Existing | Shared helper layer for MLflow usage |
| SQLite cleanup and migration support | [`../src/ml/cleanup_mlflow_sqlite.py`](../src/ml/cleanup_mlflow_sqlite.py) | Existing | Supports moving away from local-only tracking |
| Validation coverage | [`../src/ml/test_mlflow_postgres_integration.py`](../src/ml/test_mlflow_postgres_integration.py) | Existing | Focused integration test module |
| Production experiment registry hardening | Not yet implemented | Future plan | Would add stronger lifecycle and deployment controls |

## Theory of operation

A PostgreSQL-backed MLflow deployment is useful when the project evolves from notebook experimentation to repeatable training pipelines. In that model:

1. training scripts log runs and metrics to MLflow;
2. model artifacts remain in artifact storage;
3. PostgreSQL stores experiment metadata and enables consistent access across environments.

For ChessInsightAI, this matters because multiple dataset variants can be trained and compared: elite games, novice games, personal games, and normalized cross-platform rating data.

## How it relates to current modules

- `../src/ml/train_error_model.py` can emit training metrics that are natural MLflow run data.
- `../src/ml/chess_error_predictor.py` benefits from registered model lineage.
- `../src/scripts/train_model_with_tactic_phase_model.py` is a candidate training entry point for tracked experiments.
- `../src/ml/run_datasets_analysis.py` can generate comparison metrics that fit experiment dashboards.

## Recommended future direction

- Connect all training scripts to a single MLflow tracking URI.
- Separate metadata storage from artifact storage explicitly.
- Add a model registry policy for promotion from experiment to serving candidate.
- Define naming conventions for datasets, rating-normalization versions, and tactical feature variants.
