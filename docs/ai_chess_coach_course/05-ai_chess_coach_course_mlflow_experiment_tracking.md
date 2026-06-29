# Phase 05 — ChessTrainer MLflow Experiment Tracking (Course Spec)

> **Placement:** Module 05 (`05_mlflow_experiment_tracking.ipynb`)  
> **Builds on:** Module 04 (`04_ml_training.ipynb`) — same dataset, splits, models, metrics  
> **Module 06:** SHAP uses the best **Human Pattern** run selected here (or from Module 04 if 05 only adds tracking)  
> **Status:** v1 — course-portable (SQLite MLflow backend, no PostgreSQL)

---

## 1. Context (why Module 05 exists)

Module 04 trains and compares baselines in-notebook (tables, plots). That is enough for learning once, but not for:

- Comparing **many runs** over time (different hyperparameters, SMOTE vs class weights, Human vs Proxy)
- Reproducing **which model** Module 06 SHAP should explain
- Showing stakeholders a **UI** of experiments during training

Module 05 adds **MLflow experiment tracking** on top of the same training loop — it does **not** replace Module 04.

| Module 04 result (reference) | Feature set | Macro F1 (approx.) |
| ---------------------------- | ----------- | -----------------: |
| Proxy baseline               | engine + human + context | ~0.99 |
| Human Pattern baseline       | human + context only     | ~0.41 |

**Primary tracking goal:** log every **Human Pattern** training run (and optionally Proxy as a leakage sanity check) with params, metrics, and artifacts so you can pick the best run by **macro-F1 on validation** with **game-level splits**.

---

## 2. Objective

1. Configure **local MLflow** for the course (SQLite backend, no project PostgreSQL).
2. Wrap Module 04 training in `mlflow.start_run()` so each model / imbalance strategy is a **run**.
3. Log **params**, **metrics**, and **artifacts** consistently.
4. Open **MLflow UI** and compare runs; document selection criteria for “best Human model”.
5. Export a small **run manifest** (JSON) for Module 06 (`artifacts/module05/best_human_run.json`).

---

## 3. Course vs production (important)

| Aspect | Course (Module 05) | Main app (`src/ml/`, Docker) |
| ------ | ------------------ | ------------------------------ |
| Tracking store | `sqlite:///…/mlflow.db` or `./mlruns` under course folder | PostgreSQL (`mlflow_repository`) |
| Dependency | `pip install mlflow` | Full stack + DB |
| Portable | Yes — same idea as `course_data.sqlite` | No — dev/prod infra |

**Rule:** Notebooks and helpers for Module 05 live under `docs/ai_chess_coach_course/`. Do **not** import `src/db/repository/mlflow_repository.py` in the course path.

Default tracking URI (course):

```python
COURSE_ROOT = Path(__file__).resolve().parents[1]  # ai_chess_coach_course
MLFLOW_DB = COURSE_ROOT / "mlflow" / "mlflow.db"
MLFLOW_DB.parent.mkdir(parents=True, exist_ok=True)
mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_DB.resolve()}")
```

Add to `.gitignore` (course-local, not committed):

```gitignore
docs/ai_chess_coach_course/mlflow/
docs/ai_chess_coach_course/mlruns/
```

---

## 4. What to show in MLflow (contract)

### 4.1 Experiment layout

| MLflow experiment name | Purpose |
| ---------------------- | ------- |
| `chess_course_human_pattern` | Production-like models for coaching / SHAP |
| `chess_course_proxy_sanity` | Optional — confirms engine features leak labels (~0.99 F1) |

Use **one run per trained model configuration**, not one run per entire notebook.

### 4.2 Tags (filtering in UI)

| Tag | Example values |
| --- | -------------- |
| `feature_set` | `human`, `proxy` |
| `model_family` | `LogisticRegression`, `RandomForest`, `LightGBM`, `XGBoost`, `CatBoost`, `KNN` |
| `imbalance_strategy` | `class_weight`, `smote`, `none` |
| `split_policy` | `game_level` |
| `course_module` | `05` |

### 4.3 Parameters (`mlflow.log_params`)

Log at minimum:

| Param | Source |
| ----- | ------ |
| `feature_set` | `human` / `proxy` |
| `n_train_rows`, `n_val_rows`, `n_test_rows` | split sizes |
| `n_features` | after `resolve_model_feature_columns` |
| `random_state` | `42` (same as Module 04) |
| `train_ratio`, `val_ratio`, `test_ratio` | e.g. `0.70`, `0.15`, `0.15` |
| `target_column` | `error_label` |
| All model hyperparameters | e.g. `n_estimators`, `max_depth`, `learning_rate` |
| `imbalance_strategy` | `class_weight` / `smote` / `none` |
| `dataset_path` | path to `course_training_dataset.parquet` |
| `dataset_version` | git short SHA or file mtime hash (optional) |

Cap string param length (MLflow limit 500 chars); hash long feature lists.

### 4.4 Metrics (`mlflow.log_metrics`)

Align with Module 04 — log on **validation** split (primary) and **test** (secondary):

| Metric | Role |
| ------ | ---- |
| `f1_macro` | **Primary** for selecting Human Pattern best run |
| `balanced_accuracy` | Secondary |
| `pr_auc_macro` | Imbalanced multiclass |
| `precision_macro`, `recall_macro` | Report |
| `roc_auc_macro` | If computed |
| `f1_good`, `f1_inaccuracy`, `f1_mistake`, `f1_blunder` | Per-class (optional) |
| `train_f1_macro`, `val_f1_macro`, `test_f1_macro` | Overfit check |

Log validation metrics without prefix; prefix test metrics with `test_`.

### 4.5 Artifacts (`mlflow.log_artifact` / `log_dict`)

| Artifact | Description |
| -------- | ----------- |
| `model/` | `mlflow.sklearn.log_model` or `mlflow.lightgbm.log_model` etc. |
| `metrics/classification_report.json` | sklearn report |
| `plots/confusion_matrix.png` | validation confusion matrix |
| `plots/pr_curve.png` | optional |
| `feature_columns.json` | list from `resolve_model_feature_columns` |
| `label_order.json` | `["good","inaccuracy","mistake","blunder"]` |
| `run_summary.md` | human-readable one-pager |

### 4.6 What NOT to log

- Full training dataframe or parquet copies (too large; path is enough)
- Engine-proxy features when `feature_set=human` (should not be in matrix anyway)
- Secrets, DB passwords, absolute paths with usernames (prefer relative to `COURSE_ROOT`)

---

## 5. Training flow (same as Module 04 + MLflow)

```text
course_training_dataset.parquet
        ↓
encode_training_features() / split_features_and_target()
        ↓
split_by_game_id()  →  train | val | test  (by game_id)
        ↓
for each (feature_set × model × imbalance_strategy):
        mlflow.start_run()
        log params / tags
        fit on train
        evaluate on val  → log metrics
        evaluate on test → log test_* metrics
        log artifacts (model, plots, feature list)
        mlflow.end_run()
        ↓
compare runs in UI → pick best Human run (max val f1_macro)
        ↓
write artifacts/module05/best_human_run.json
```

Reuse from `dataset/feature_engineering.py`:

- `resolve_model_feature_columns(..., feature_set="human"|"engine")`
- `split_features_and_target(..., sanitize_feature_names=True)`
- `ENGINE_PROXY_FEATURES`, `HUMAN_PATTERN_FEATURES`

Reuse from Module 04 notebook (extract to helper when implementing):

- Model registry dict (LogisticRegression, KNN, RF, LightGBM, XGBoost, CatBoost)
- `compute_multiclass_metrics()` helper
- SMOTE / `class_weight` pipelines

---

## 6. Best-model selection criteria

For **Human Pattern** runs (used by Module 06 SHAP):

1. Filter: `feature_set=human`, split = game-level validation
2. Rank by **`val_f1_macro`** (descending)
3. Tie-break: higher `val_balanced_accuracy`, then simpler model (LR < RF < LightGBM)
4. Reject runs with `train_f1_macro - val_f1_macro > 0.15` (overfit flag) unless no alternative
5. Save winning `run_id` to `artifacts/module05/best_human_run.json`:

```json
{
  "run_id": "<mlflow-run-uuid>",
  "experiment_name": "chess_course_human_pattern",
  "model_family": "LightGBM",
  "imbalance_strategy": "class_weight",
  "val_f1_macro": 0.41,
  "selected_at": "2026-06-20T12:00:00Z"
}
```

Proxy runs: keep in separate experiment for teaching; **never** select Proxy for SHAP/coaching.

---

## 7. MLflow UI (what you show during training)

### Start tracking server

From repo root or course folder:

```powershell
cd docs/ai_chess_coach_course
mlflow ui --backend-store-uri sqlite:///mlflow/mlflow.db --port 5000
```

Open: [http://localhost:5000](http://localhost:5000)

### What to demonstrate live

1. **Experiments** sidebar — `chess_course_human_pattern` vs proxy sanity
2. **Compare runs** — sort by `f1_macro`, parallel coordinates for hyperparameters
3. **Run detail** — params, metrics, artifact model + confusion matrix
4. **Model registry** (optional v1) — register best run as `human_error_classifier_staging`

Screenshot-friendly metric for slides: **Human ~0.41 macro-F1 vs Proxy ~0.99** on the same split policy.

---

## 8. Deliverables (Module 05)

| Artifact | Location |
| -------- | -------- |
| Course spec (this file) | `05-ai_chess_coach_course_mlflow_experiment_tracking.md` |
| Notebook | `05_mlflow_experiment_tracking.ipynb` |
| Helper (recommended) | `experiment_tracking/course_mlflow.py` |
| MLflow store (local, gitignored) | `mlflow/mlflow.db` |
| Best-run pointer | `artifacts/module05/best_human_run.json` |
| Tests (optional) | `tests/docs_courses/test_course_mlflow.py` — mock run, assert params logged |

---

## 9. Suggested helper API (`experiment_tracking/course_mlflow.py`)

Minimal surface for notebook + tests:

```python
def configure_course_mlflow(*, db_path: Path | None = None) -> str: ...

def start_training_run(
    *,
    feature_set: str,
    model_family: str,
    imbalance_strategy: str,
    params: dict,
) -> mlflow.ActiveRun: ...

def log_validation_metrics(metrics: dict, *, prefix: str = "") -> None: ...

def log_training_artifacts(
    model,
    *,
    feature_columns: list[str],
    label_order: list[str],
    confusion_matrix_path: Path | None = None,
) -> None: ...

def select_best_human_run(
    experiment_name: str = "chess_course_human_pattern",
    metric: str = "f1_macro",
) -> dict: ...
```

---

## 10. Implementation tasks (`feature/05_mlflow_integration`)

- [ ] Add `.gitignore` entries for `docs/ai_chess_coach_course/mlflow/`
- [ ] Create `experiment_tracking/course_mlflow.py`
- [ ] Create `05_mlflow_experiment_tracking.ipynb` (reuse Module 04 cells + MLflow wrappers)
- [ ] Log at least 6 model families × 2 feature sets × 2 imbalance strategies (subset OK for CI)
- [ ] Document `mlflow ui` command in notebook header
- [ ] Write `artifacts/module05/best_human_run.json` at end of notebook
- [ ] Optional test: `mlflow.set_tracking_uri` to temp sqlite, one fake run

---

## 11. Out of scope (Module 05)

- PostgreSQL / Docker MLflow (see `docs/devops/MLFLOW_POSTGRES_INTEGRATION.md` for main app)
- Hyperparameter search (Optuna) — future enhancement
- Model deployment / REST serving
- SHAP plots (Module 06)
- Replacing Module 04 notebook (04 stays the intro; 05 is tracking-focused)

---

## 12. References

| Doc | Use |
| --- | --- |
| Module 04 notebook | Training loop to wrap |
| `03-ai_chess_coach_course_shap_human_pattern.md` | Consumes best Human run |
| `02-ai_chess_coach_leakage_detection.md` | Proxy vs Human feature sets |
| `openspec/changes/implement-course-modules-05/` | OpenSpec tasks |
| `src/ml/mlflow_utils.py` | Reference only — patterns, not imports |

---

## 13. Acceptance checklist

- [ ] `mlflow ui` shows multiple runs with comparable params
- [ ] Each run has `f1_macro`, model family, and `feature_set` tag
- [ ] Best Human run is identifiable without rerunning notebook
- [ ] No file >100 MB committed; MLflow store is gitignored
- [ ] Works offline with course parquet + sqlite MLflow only
