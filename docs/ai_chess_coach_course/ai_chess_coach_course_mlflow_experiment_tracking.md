# Module 05 — MLflow integration

Canonical spec: **[05-ai_chess_coach_course_mlflow_experiment_tracking.md](./05-ai_chess_coach_course_mlflow_experiment_tracking.md)**

Quick start after implementation:

```powershell
cd docs/ai_chess_coach_course
jupyter notebook 05_mlflow_experiment_tracking.ipynb

# In another terminal:
.\start_mlflow_ui.ps1

# Or print the exact command (absolute sqlite path; works on Windows):
# python -c "from experiment_tracking.course_mlflow import mlflow_ui_command; print(mlflow_ui_command())"
```

Goal: show training experiments from Module 04 in the MLflow UI (params, metrics, artifacts), portable SQLite backend — no PostgreSQL.
