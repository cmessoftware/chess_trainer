# MLflow PostgreSQL Integration Guide

## Overview

This guide covers the integration of MLflow with PostgreSQL backend for the Chess Trainer project.

## Configuration

### PostgreSQL Backend Setup

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# MLflow tracking URI
export MLFLOW_TRACKING_URI="postgresql://chess:chess_pass@localhost:5432/chess_trainer_db"
```

### Environment Variables

```bash
# .env file
MLFLOW_TRACKING_URI=postgresql://chess:chess_pass@localhost:5432/chess_trainer_db
MLFLOW_DEFAULT_ARTIFACT_ROOT=./mlruns
```

## Usage

### Starting MLflow Server

```python
import mlflow
import mlflow.sklearn

# Set tracking URI
mlflow.set_tracking_uri("postgresql://chess:chess_pass@localhost:5432/chess_trainer_db")

# Start experiment
with mlflow.start_run():
    # Your ML code here
    pass
```

### Model Registry

```python
# Register model
mlflow.sklearn.log_model(
    model, 
    "chess_error_classifier",
    registered_model_name="ChessErrorPredictor"
)
```

## Best Practices

1. **Experiment Organization**: Use meaningful experiment names
2. **Parameter Logging**: Log all hyperparameters
3. **Metric Tracking**: Track F1 macro, confusion matrix
4. **Artifact Storage**: Save models and plots

## Troubleshooting

### Common Issues

- **Connection refused**: Verify PostgreSQL is running
- **Authentication failed**: Check credentials in connection string
- **Database not found**: Ensure chess_trainer_db exists

### Solutions

```bash
# Test PostgreSQL connection
psql -h localhost -U chess -d chess_trainer_db -c "SELECT 1;"

# Reset MLflow tables if needed
mlflow db upgrade postgresql://chess:chess_pass@localhost:5432/chess_trainer_db
```

## References

- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [PostgreSQL Docker Setup](../docker-compose.yml)
- [Chess Trainer ML Pipeline](../src/ml/)
