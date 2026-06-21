# AI Engineering Course — Portable Setup (SQLAlchemy + SQLite default)

This folder contains the course notebooks, a notebook-friendly helper, and the migration script required to keep the course **portable by default**.

- **Default runtime:** SQLite (`docs/courses/course_data.sqlite`)
- **Portable access layer:** SQLAlchemy
- **Optional backend:** PostgreSQL, only through configuration
- **First preparation step:** migrate/export the source data from PostgreSQL into SQLite

---

## Quick-start

### 1 — One-time migration from PostgreSQL to SQLite

> Skip this step if you already have `course_data.sqlite` in this folder.

Set the source connection variable and run the migration script:

```bash
# Bash / macOS / Linux
export CHESS_TRAINER_DB_URL="postgresql://user:PASSWORD@localhost:5432/chess_trainer_db"
python docs/courses/migrate_to_sqlite.py

# Windows PowerShell
$env:CHESS_TRAINER_DB_URL = "postgresql://user:PASSWORD@localhost:5432/chess_trainer_db"
python docs/courses/migrate_to_sqlite.py
```

The script copies the `games` and `features` rows for player **cmess1315** into `docs/courses/course_data.sqlite`. This SQLite file is the default runtime for the course notebooks and dataset builder.

### 2 — Open the notebooks

```bash
cd docs/courses
jupyter notebook
```

Open notebooks in order:

| #   | File                             | Topic                                     |
| --- | -------------------------------- | ----------------------------------------- |
| 1   | `00_architecture_overview.ipynb` | Architecture & environment check          |
| 2   | `01_run_feature_pipeline.ipynb`  | Migration + feature pipeline verification |
| 3   | `02_dataset_builder.ipynb`       | Dataset building & ML preparation         |
| 4   | `04_ml_training.ipynb`           | Train data using several models           |

---

## Course database configuration

The course code resolves the database in this order:

1. explicit `db_url` argument
2. `CHESS_COURSE_DB_URL` environment variable
3. local SQLite file `docs/courses/course_data.sqlite`

### Default SQLite runtime

No extra configuration is required for the portable path. The helper and the dataset builder automatically use:

```
sqlite:///.../docs/courses/course_data.sqlite
```

### Optional PostgreSQL override

If you want the notebooks/helper to query PostgreSQL directly, set:

```bash
export CHESS_COURSE_DB_URL="postgresql://user:PASSWORD@localhost:5432/chess_trainer_db"
```

This is optional and should not be required for the normal course flow.

---

## Notebook helper

Import the helper directly from the notebook directory:

```python
from notebook_data_helper import CourseDataHelper

course_data = CourseDataHelper()  # SQLite by default
features_df = course_data.load_features(limit=10)
games_df = course_data.load_games(limit=10)
label_df = course_data.error_label_distribution()
```

You can also override the backend explicitly:

```python
from notebook_data_helper import CourseDataHelper

course_data = CourseDataHelper(
    "postgresql://user:PASSWORD@localhost:5432/chess_trainer_db"
)
```

---

## Dataset builder

The portable dataset builder uses the same SQLAlchemy repository layer and keeps `error_label` as the target with the course classes:

- `good`
- `inaccuracy`
- `mistake`
- `blunder`

CLI usage:

```bash
python docs/courses/dataset/build_training_dataset.py
python docs/courses/dataset/build_training_dataset.py --db-url postgresql://...
python docs/courses/dataset/build_training_dataset.py --output data/datasets/course_training_dataset.csv
```

By default it writes to `data/datasets/course_training_dataset.parquet`.

---

## Files introduced for the portable course flow

- `docs/courses/data_access/features_repository.py` — SQLAlchemy repository for `games` and `features`
- `docs/courses/data_access/notebook_data_helper.py` — reusable notebook helper
- `docs/courses/notebook_data_helper.py` — convenience import for notebooks
- `docs/courses/dataset/build_training_dataset.py` — training dataset builder on top of the shared repository
- `docs/courses/migrate_to_sqlite.py` — PostgreSQL → SQLite export step

---

## Why this keeps the course portable

- The default execution path no longer requires a running PostgreSQL service.
- PostgreSQL remains available, but only as a configurable backend or export source.
- The shared SQLAlchemy layer avoids hardcoding engine-specific access code in notebooks and scripts.

---

## Adding `course_data.sqlite` to `.gitignore`

The SQLite file can be large and contains personal game data.  
It is excluded from the repository via `.gitignore` and must be generated locally with the migration script.
