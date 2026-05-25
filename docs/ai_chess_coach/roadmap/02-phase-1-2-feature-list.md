# Feature List and Proposed Tasks

## 1. core-engine + minimal api

### Feature List
- PGN ingestion and validation pipeline
- Deterministic chess analysis with Stockfish integration
- Position and move evaluation services
- Basic error and blunder detection
- Minimal API endpoint for PGN analysis requests
- Structured JSON response for analysis results
- Docker-based local execution aligned with project services
- Basic observability for request success/failure and timing
- Automated tests for core analysis flow and API contract

### Proposed Tasks
- Define core-engine module boundaries and interfaces for PGN parsing, move replay, and analysis
- Implement PGN validation rules and normalized error handling
- Add Stockfish service wrapper with deterministic configuration defaults
- Create move-by-move evaluation pipeline from PGN to analyzed positions
- Implement baseline mistake/inaccuracy/blunder classification rules using engine evaluation deltas
- Design minimal API contract for submitting PGN and receiving analysis output
- Add API endpoint and request/response schemas
- Add logging and metrics for engine runtime, failures, and API latency
- Create unit tests for parser, analyzer, and classification rules
- Create integration tests for end-to-end PGN analysis through the API
- Document local run instructions using Docker Compose and the project environment

## 2. ml-error-classification

### Feature List
- Training dataset generation from analyzed games
- ML-ready feature engineering pipeline for move quality classification
- Error classification model for player mistakes
- Model evaluation and comparison workflow
- MLflow experiment tracking for training runs
- Batch inference service for classifying moves and errors
- Model versioning and reproducible training configuration
- Monitoring hooks for prediction quality and data drift signals
- Automated tests for feature generation and inference behavior

### Proposed Tasks
- Define the label taxonomy and target classes for error classification
- Identify and document training data sources from stored analysis outputs
- Implement dataset extraction script for labeled move and error samples
- Build or extend feature engineering scripts for ML input generation
- Implement training, validation, and evaluation pipeline components
- Add baseline models and compare metrics across candidate approaches
- Track experiments, parameters, metrics, and artifacts in MLflow
- Implement model serialization, loading, and version selection strategy
- Expose batch or service-level inference interface for downstream API/orchestration use
- Add validation checks for schema drift and missing feature columns
- Create tests for dataset generation, training pipeline, and inference outputs
- Document model training, retraining, and evaluation workflow
