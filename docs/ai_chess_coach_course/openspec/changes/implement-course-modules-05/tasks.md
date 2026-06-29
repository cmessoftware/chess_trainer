# Tasks: implement-course-modules-05

## 1. Artifact Implementation
- [x] Create or update 05_mlflow_experiment_tracking.ipynb.

## 2. Module Deliverables
- [x] Configure local MLflow tracking with sqlite backend (`docs/ai_chess_coach_course/mlflow/mlflow.db`).
- [x] Log params, metrics, and artifacts for each baseline model (see spec §4).
- [x] Compare runs and identify best Human Pattern model (`val_f1_macro`, spec §6).
- [x] Write `artifacts/module05/best_human_run.json` for Module 06.

## 2b. Documentation
- [x] Course spec: `05-ai_chess_coach_course_mlflow_experiment_tracking.md`

## 3. Validation
- [x] Add `tests/docs_courses/test_course_mlflow.py` (temp sqlite smoke run).
- [ ] Verify top-to-bottom execution in the target environment.
- [ ] Document assumptions and known limitations.
