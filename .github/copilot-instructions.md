# Copilot Instructions for AI Agents

Welcome to the `chess_trainer` project! This guide provides actionable, project-specific instructions to help AI coding agents (like GitHub Copilot) be productive and follow our conventions.

## Project Overview
- **Purpose:** Chess data import, feature engineering, and ML pipeline for chess training and analysis.
- **Core Technologies:** Python, Docker Compose, PostgreSQL, MLflow, Jupyter Notebooks.
- **Key Directories:**
  - `src/scripts/`: Data import, feature engineering, and utility scripts.
  - `src/ml_pipeline/`: ML pipeline classes and logic.
  - `notebooks/`: EDA, ML workflow, and pipeline execution notebooks (clean, minimal, no duplicate/old notebooks).
  - `data/`: Datasets (by source) and intermediate files.
  - `docs/`: Guides for MLflow, preprocessing, workflow, and PR instructions.

## ⚠️ CRITICAL: Python Environment
- **ALWAYS USE CONDA ENVIRONMENT:** `chess_trainer`
- **NEVER use `.venv` or other virtual environments**
- **Activation Command:** `conda activate chess_trainer`
- **ALL Python commands, pip installs, and script executions MUST use this conda environment**
- **When running terminal commands:** Ensure conda environment is activated first
- **Backend API:** Must run in `chess_trainer` conda environment
- **Scripts:** All scripts in `src/scripts/` must execute within `chess_trainer` environment

## Data & Database
- **Primary Data Source:** PostgreSQL (in Docker, service: `postgres`).
- **Datasets:** Located in `/app/src/data/games` (subfolders: `elite`, `personal`, `novice`, `stockfish`, `fide`).
- **No SQLite:** All scripts and notebooks must use PostgreSQL, not SQLite.
- **DB Schema:** Managed with Alembic migrations (`alembic/`).

## ML Pipeline
- **Entry Point:** `src/scripts/execute_issue_86_pipeline.py` (planned) will run the ML pipeline.
- **Pipeline Logic:** Implement in `src/ml_pipeline/complete_ml_pipeline.py` (planned).
- **Feature Engineering:** Use scripts in `src/scripts/` (e.g., `generate_features_with_tactics.py`).
- **Experiment Tracking:** Use MLflow (see `docs/MLFLOW_COMPLETE_GUIDE.md`).

## Orchestration & Local Dev
- **Docker Compose:** Orchestrates `chess_trainer` (app), `notebooks` (Jupyter/MLflow), and `postgres`.
- **Miniforce/PowerShell:** Use `ds_tools.ps1` for local orchestration.
- **.env:** Store DB connection strings and secrets here.

## Conventions & Best Practices
- **Scripts:** Centralize in `src/scripts/`. Avoid duplicate logic in notebooks.
- **Notebooks:** For EDA and pipeline execution only. Keep clean and minimal.
- **Documentation:** Reference and update guides in `docs/` as workflows evolve.
- **Testing:** Use scripts and notebooks for validation. Add tests as needed.
- **Pull Requests:** Follow instructions in `docs/ML_PREPROCESSING_GUIDE.md` and `docs/MLFLOW_COMPLETE_GUIDE.md`.
- **MLflow:** Always log experiments and results.

## Quickstart for AI Agents
1. **Import Data:** Use `src/scripts/import_pgns_parallel.py` to load PGN files into PostgreSQL.
2. **Feature Engineering:** Run `src/scripts/generate_features_with_tactics.py` to extract features.
3. **Run ML Pipeline:** (Planned) Use `src/scripts/execute_issue_86_pipeline.py` to train/evaluate models.
4. **Track Experiments:** Use MLflow UI (`http://localhost:5000`) to review runs.
5. **Orchestrate Locally:** Use `ds_tools.ps1` or Docker Compose tasks for service management.

## Key References
- **MLflow Guide:** `docs/MLFLOW_COMPLETE_GUIDE.md`
- **Preprocessing Guide:** `docs/ML_PREPROCESSING_GUIDE.md`
- **Project Structure:** `README.md`, `docs/DOCKER_DEVELOPMENT_STRATEGY.md`
- **DB Schema:** `alembic/`, `alembic.ini`
- **Roadmap Técnico:** `docs/ROADMAP_TECHNICAL.md` (detalles de implementación para developers)
- **Roadmap Funcional:** `docs/ROADMAP_FUNCTIONAL_CHESS_TRAINER.md` (SOURCE OF TRUTH para frontend development)
- **Testing Guide:** `docs/TESTING_AUTHENTICATION.md`

## 🚨 CRITICAL: Roadmap Adherence (Frontend Development)
- **ALWAYS follow `docs/ROADMAP_FUNCTIONAL_CHESS_TRAINER.md` for frontend tasks**
- **This roadmap is the SOURCE OF TRUTH for React + Vite development**
- **For technical implementation details, consult `docs/ROADMAP_TECHNICAL.md`**
- **Before starting ANY frontend task:**
  1. Read the current roadmap status
  2. Verify the task aligns with the next planned functionality
  3. If user requests deviations from the roadmap: **WARN THEM EXPLICITLY**
  
### **Warning Protocol**
When user requests work that deviates from the roadmap:
```
⚠️ ADVERTENCIA: La tarea solicitada se desvía del roadmap establecido.

Roadmap actual indica: [funcionalidad X en fase Y]
Tu solicitud: [descripción de la desviación]

¿Deseas continuar de todos modos? Esto puede:
- Interrumpir el flujo de desarrollo planificado
- Crear dependencias fuera de orden
- Retrasar funcionalidades prioritarias

Confirma para proceder o ajusta la solicitud al roadmap.
```

### **Current Roadmap Status** (as of Feb 14, 2026)
- ✅ **Sprint 1 COMPLETADO**: Database Browser + Authentication System
- 🔜 **Next (High Priority)**: FUNCIONALIDAD 3.1 - Chess Board Interactivo + Log System Base
- 🔜 **After that**: FUNCIONALIDAD 3.2 - Conexión con Stockfish + Logs Engine
- 🔜 **Then**: FUNCIONALIDAD 3.3 - Games Explorer en React + Logs Database

### **Roadmap Update Protocol**
- **After completing each functionality**: Update roadmap status section with:
  - Completion date
  - Commit/version reference
  - Testing documentation links
  - Next steps

## AI Agent Reminders
- **CRITICAL: Always use conda environment `chess_trainer` - NEVER use .venv or other environments.**
- **Always prefer scripts over notebooks for core logic.**
- **Never use SQLite; always use PostgreSQL.**
- **Keep notebooks clean and focused.**
- **Update documentation if workflows change.**
- **Reference this file for project-specific conventions.**
- **🚨 ALWAYS check and follow `docs/ROADMAP_FUNCTIONAL_CHESS_TRAINER.md` before starting frontend work.**
- **📋 For technical implementation details, consult `docs/ROADMAP_TECHNICAL.md`.**
- **⚠️ WARN user if requested task deviates from the roadmap.**

---
_Last updated: 2026-02-14_
