# AI Engineering Course — Portable Setup (SQLite)

This folder contains the three course notebooks and a migration script so the
course can be run **without a running ChessTrainer PostgreSQL service**.

---

## Quick-start

### 1 — One-time migration (requires PostgreSQL access)

> Skip this step if you already have `course_data.sqlite` in this folder.

Set the connection variable and run the migration script:

```bash
# Bash / macOS / Linux
export CHESS_TRAINER_DB_URL="postgresql://chess:chess_pass@localhost:5432/chess_trainer_db"
python docs/courses/migrate_to_sqlite.py

# Windows PowerShell
$env:CHESS_TRAINER_DB_URL = "postgresql://chess:chess_pass@localhost:5432/chess_trainer_db"
python docs/courses/migrate_to_sqlite.py
```

The script extracts all games of player **cmess1315** and the related feature
rows, then writes them to `docs/courses/course_data.sqlite`.

Run `python docs/courses/migrate_to_sqlite.py --help` for all options.

### 2 — Open the notebooks

```bash
cd docs/courses
jupyter notebook
```

Open notebooks in order:

| # | File | Topic |
|---|------|-------|
| 1 | `01_architecture_overview.ipynb` | Architecture & environment check |
| 2 | `02_run_feature_pipeline.ipynb`  | Feature pipeline & data verification |
| 3 | `03_dataset_builder.ipynb`       | Dataset building & ML preparation |

---

## Required PostgreSQL environment variables (migration only)

| Variable | Description | Example |
|----------|-------------|---------|
| `CHESS_TRAINER_DB_URL` | Full PostgreSQL DSN | `postgresql://chess:chess_pass@localhost:5432/chess_trainer_db` |

These are **only needed once** to run `migrate_to_sqlite.py`.  
After that the notebooks use only the local SQLite file.

---

## Generated SQLite file

| Detail | Value |
|--------|-------|
| Default path | `docs/courses/course_data.sqlite` |
| Tables | `games`, `features` |
| Player | `cmess1315` |

The notebooks locate the file via a path relative to the notebook directory:

```python
from pathlib import Path
SQLITE_DB = Path(__file__).parent / "course_data.sqlite"   # scripts
# or inside a notebook cell:
SQLITE_DB = Path(".") / "course_data.sqlite"
```

---

## Migration script options

```
python migrate_to_sqlite.py [--pg-url PG_URL] [--player PLAYER] [--output OUTPUT]

Options:
  --pg-url   PostgreSQL connection URL (overrides CHESS_TRAINER_DB_URL)
  --player   Player username to export  (default: cmess1315)
  --output   Path for the SQLite output (default: course_data.sqlite next to this script)
```

The script is **idempotent** — running it again replaces the data cleanly.

---

## How the notebooks connect to SQLite

```python
import sqlite3, pandas as pd
from pathlib import Path

SQLITE_DB = Path(".").resolve() / "course_data.sqlite"
conn = sqlite3.connect(str(SQLITE_DB))
df = pd.read_sql("SELECT * FROM features LIMIT 10", conn)
conn.close()
```

---

## Adding `course_data.sqlite` to `.gitignore`

The SQLite file can be large and contains personal game data.  
It is excluded from the repository via `.gitignore` and must be generated
locally with the migration script.
