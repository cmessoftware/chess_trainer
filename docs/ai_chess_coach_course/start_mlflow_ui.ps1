# Launch MLflow UI for the course SQLite tracking store.
# Run from docs/ai_chess_coach_course (creates mlflow/ if missing).

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$command = python -c "from experiment_tracking.course_mlflow import mlflow_ui_command; print(mlflow_ui_command())"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to resolve MLflow UI command."
}

Write-Host "Starting: $command"
Invoke-Expression $command
