# MLflow PostgreSQL Integration

## Overview

This document describes how the `chess_trainer` project has been configured to use PostgreSQL as the backend store for MLflow, replacing the local SQLite database approach.

## Architecture

- **MLflow Backend**: PostgreSQL database (same as the main application)
- **MLflow Artifacts**: Stored in the `mlruns` directory
- **Integration Pattern**: Repository pattern using SQLAlchemy

## Key Components

1. **MLflowRepository**: Provides connection string and database operations for MLflow
   - Located at: `src/db/repository/mlflow_repository.py`

2. **MLflow Initialization Script**: Verifies and initializes MLflow database tables
   - Located at: `src/ml/init_mlflow_db.py`

3. **MLflow PostgreSQL Setup**: Sets environment variables for MLflow
   - Located at: `src/ml/mlflow_postgres_setup.py`

4. **MLflow Utils**: Updated to use PostgreSQL by default
   - Located at: `src/ml/mlflow_utils.py`

5. **Docker Configuration**: Updated to use PostgreSQL for MLflow
   - Updated in: `docker-compose.yml`

6. **PowerShell Helpers**: Functions for MLflow PostgreSQL operations
   - Located at: `mlflow-helpers.ps1`
   - Imported by: `PowerShell-Helpers.ps1` and `quick-helpers.ps1`

## Usage

### VS Code Tasks

- **🔧 ML Workflow: Initialize MLflow with PostgreSQL**: Sets up MLflow with PostgreSQL
- **🚀 ML Workflow: Start MLflow Server**: Starts the MLflow server with PostgreSQL backend
- **🌐 ML Workflow: Open MLflow UI**: Opens the MLflow UI in your browser

### PowerShell Commands

- **Initialize-MLflow**: Initialize MLflow with PostgreSQL
- **Start-MLflowWithPostgres**: Start MLflow server with PostgreSQL
- **Open-MLflowUI**: Open MLflow UI in the browser
- **Run-MLExperiment**: Run a machine learning experiment with tracking
- **Invoke-RealDatasetsAnalysis**: Run comprehensive ML analysis on real chess datasets

### Quick Commands

- **mlinit**: Initialize MLflow with PostgreSQL
- **mlexp**: Run an ML experiment with MLflow tracking

## Database Details

MLflow tables are automatically created in the PostgreSQL database the first time the MLflow server starts. The database connection is configured through the `MLflowRepository` class, which uses the same database connection as the main application.

## Migrations

Currently, no custom Alembic migrations are needed for MLflow tables, as they are automatically managed by MLflow itself. If custom extensions to MLflow metadata are needed in the future, Alembic migrations will be created.

## Troubleshooting

If you encounter issues with the MLflow PostgreSQL integration:

1. Verify PostgreSQL service is running: `docker-compose ps postgres`
2. Check MLflow logs: `docker-compose logs mlflow`
3. Verify PostgreSQL connection: `docker-compose exec mlflow python -c "from src.db.repository.mlflow_repository import mlflow_repo; print(mlflow_repo.test_connection())"`
4. Reset and reinitialize: Run the task "🧹 ML Workflow: Clean and Restart" then "🔧 ML Workflow: Initialize MLflow with PostgreSQL"

## Notes for Developers

When developing new ML features:

1. Always use the `ChessMLflowTracker` class from `src/ml/mlflow_utils.py` to ensure proper PostgreSQL integration
2. For scripts that need to connect to MLflow, import and use `mlflow_repo` from `src.db.repository.mlflow_repository`
3. Use the PowerShell helpers (Initialize-MLflow, Run-MLExperiment) for consistent workflow

## Real Datasets Analysis

The project includes a comprehensive analysis tool for comparing model performance across different chess datasets:

- **Elite Dataset**: High-level players (Elo 2500+) - Rich error labels
- **FIDE Dataset**: Official FIDE tournament games
- **Novice Dataset**: Beginner players (Elo ~1200)  
- **Personal Dataset**: Personal games from Chess.com/Lichess - Most realistic error distribution
- **Stockfish Dataset**: Engine analysis data

Use `Invoke-RealDatasetsAnalysis` or `Analyze-RealDatasets` to run the analysis.
