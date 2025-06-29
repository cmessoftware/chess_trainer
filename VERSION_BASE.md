# CHESS TRAINER - Version: v0.1.20-f9d0260

# ♟ chess_trainer – Analysis and Training with Elite Games

This project automates the import, analysis, labeling, and training from thousands of games played by elite players (ELO >2300), combining tactical analysis with visual exploration and exercise generation.

---

## 📦 Requirements

- Python 3.10+
- Packages:
  ```bash
  pip install -r requirements.txt
  ```
- Stockfish installed (Linux):
  ```bash
  sudo apt install stockfish
  ```

---

## 📂 Project Structure

```
chess_trainer/
├── notebooks/                   # Exploration, clustering, predictions
│   ├── eda_analysis.ipynb
│   ├── pca_clustering_chess.ipynb
│   └── analyze_predictions.ipynb
├── src/
│   ├── data/                    # Lichess Elite base and PGNs
│   │   ├── chess_trainer.db
│   │   └── games/*.pgn
│   ├── models/                  # Trained models
│   │   └── error_label_model.pkl
│   ├── modules/                 # Core (reusable) functionality
│   │   ├── generate_dataset.py
│   │   ├── extractor.py
│   │   └── eda_utils.py
│   ├── scripts/                 # Standalone execution scripts
│   │   ├── run_pipeline.sh
│   │   ├── auto_tag_games.py
│   │   ├── analyze_errors_from_games.py
│   │   ├── generate_exercises_from_elite.py
│   │   ├── save_games_to_db.py
|   |   |__ analize_games_tactics_paralell  
|   |   |__ generate_features_paralell
|   |   |__ generate_pgn_from_chess_server
│   │   └── inspect_db.py
|   |__ services/
│   │   ├── features_export_service.py
│   │   ├── get_lichess_studies.py
│   │   ├── study_importer_service.py
|   |__ tools/ 
│   │   ├── elite_explorer.py
|   |   |__create_issues_from_json
|   ├── pages/                   # Streamlit pages
│   │   ├── elite_explorer.py
│   │   ├── elite_training.py
│   │   ├── elite_stats.py
│   │   └── streamlit_eda.py
│   └── tests/                   # Automated tests with pytest
│       ├── test_elite_pipeline.py
│       └── test_tag_games.py
├── .env                         # Configured path to the database
├── requirements.txt             # Dependencies
└── README.md
```

---

## 🚀 Recommended Workflow

```bash
# Save games to the database
python src/scripts/import_game.py --input src/data/games/lichess_elite_2020-05.pgn

# Label, analyze, generate exercises and cumulative dataset
bash src/scripts/run_pipeline.sh

# Run visual explorer
streamlit run src/pages/elite_explorer.py
```

---

## 🧪 Automated Testing

This project uses `pytest` to verify:
- Database structure
- Existence of labels
- Validity of JSON exercises

```bash
pytest src/tests/
```

---

## 🧠 Environment Variables

Define the SQLite database path in a `.env` file:

```env
CHESS_TRAINER_DB=src/data/chess_trainer.db
STOCKFISH_PATH=/usr/games/stockfish’
```

And load it with:

```python
from dotenv import load_dotenv
load_dotenv()
```

---
## Configure and Run Database Migrations with Alembic and SqlAlchemy 
**Supports multiple engines like Sqlite, MySql, Postgres, MariaDb, etc.**

## 📦 Step 1: Install Alembic if you haven't already
```bash
pip install alembic
```
## 📁 Step 2: Initialize Alembic at the project root (e.g., /app)
```bash
cd /app
alembic init alembic
```
#### This creates an alembic/ folder and an alembic.ini file.

## 🛠️ Step 3: Configure alembic/env.py
#### Replace the target_metadata content and add your engine.

#### In alembic/env.py
```python
from db.database import Base
from db import models  # make sure __init__.py imports all models

target_metadata = Base.metadata
```
## 🧩 Step 4: Configure the database connection
#### Edit alembic.ini and change the sqlalchemy.url line
```python
sqlalchemy.url = postgresql+psycopg2://user:password@localhost:5432/your_db
```
#### Or use an environment variable if you already use dotenv
#### sqlalchemy.url = env:CHESS_TRAINER_DB_URL

## 🧱 Step 5: Generate the migration script
```bash
alembic revision --autogenerate -m "Add columns to Games"
```

## 🚀 Step 6: Apply the migration to the database
```bash
alembic upgrade head
```
## 🧽 Step 7 (optional): Revert a migration
```bash
alembic downgrade -1
```
**Note: the alembic command must be run in the same folder as alembic.ini (e.g., /app)**

---
# Using GIT LFS for Large Datasets and ML Models

**GIT LFS is chosen to reuse GitHub infrastructure, experience, and credentials**

```bash
git lfs install
git lfs track "*.csv"
git add .gitattributes
git add /app/src/data/features_dataset_*.csv #Or the chosen dataset path.
git commit -m "Add dataset to repo with Git LFS"
git push
```

## 📊 Exploratory Data Analysis (EDA)

Explore and visualize the dataset with:

📄 `notebooks/eda_analysis.ipynb`

Includes:
- Error distribution
- Correlations
- Mobility vs score
- Frequent openings

---

## 📤 Publish Games to Lichess

With `publish_to_lichess.py` you can upload games from the database as studies. You need a Lichess token with `study:write` permissions.

---
### 🧠 Project Architecture

![Chess_trainer architecture](../img/architecture.png)

---

## Structure of training_dataset.csv

### 📊 Fields generated by `generate_features_from_game`

| Field                | Source / logic                                                                 |
|----------------------|--------------------------------------------------------------------------------|
| `fen`                | `board.fen()` before the move                                                  |
| `move_san`           | `board.san(move)`                                                              |
| `move_uci`           | `move.uci()`                                                                   |
| `material_balance`   | Material difference (white - black), using values `{P:1, N:3, B:3.25...}`      |
| `material_total`     | Total material on the board                                                    |
| `num_pieces`         | Number of pieces (excluding pawns and kings)                                   |
| `branching_factor`   | `len(legal_moves)` before **+** after the move                                 |
| `self_mobility`      | `len(legal_moves)` for the player **before** the move                          |
| `opponent_mobility`  | `len(legal_moves)` for the opponent **after** simulating the move              |
| `phase`              | `"opening"` (≥24 pieces), `"middlegame"` (12–23), `"endgame"` (<12)            |
| `player_color`       | `"white"` or `"black"` according to `board.turn`                               |
| `has_castling_rights`| `int(board.has_castling_rights())` (0 or 1)                                    |
| `move_number`        | `board.fullmove_number`                                                        |
| `is_repetition`      | `int(board.is_repetition())` (1 if repetition)                                 |
| `is_low_mobility`    | `int(self_mobility <= 5)`                                                      |
| `is_center_controlled`| 1 if the player controls d4/e4/d5/e5 with any piece                           |
| `is_pawn_endgame`    | 1 if only kings and pawns remain on the board                                  |

## Design for Tactical Analysis

| Aspect                                  | Advantage                                     |
|------------------------------------------|-----------------------------------------------|
| depth by phase                           | Saves time without losing accuracy            |
| multipv only when many options           | Doesn't waste CPU resources                   |
| compare_to_best avoids false positives    | Improves label quality                        |
| classify_tactical_pattern still works    | Classic tags like fork, pin, mate             |
| eval_cache                               | Avoids repeated evaluations by FEN            |

## Optimizations to Speed Up Tactical Analysis (reduce from days to hours) 
**Updated: 2025-06-02**

## ✅ List of optimizations in `tactical_analysis.py` - `chess_trainer`

| Nº | Optimization                                    | Status     | Details / Comments                                                                  |
|----|-------------------------------------------------|------------|-------------------------------------------------------------------------------------|
| 1️⃣ | 🔻 Reduce fixed depth                           | ✅ Applied | Uses `depth=6` for moves with `pre_tag`; dynamic values by phase for the rest.      |
| 2️⃣ | ⏭️ Skip first moves                            | ✅ Applied | If `move_number <= 6`, analysis is skipped. Controlled by `opening_move_threshold`. |
| 3️⃣ | 🧠 Variable depth by phase                      | ✅ Applied | Uses `PHASE_DEPTHS` based on game phase (`opening`, `middlegame`, `endgame`).       |
| 4️⃣ | 🧮 Branching factor                             | ✅ Applied | If `branching < 5`, the move is skipped. Used as a low complexity indicator.        |
| 5️⃣ | 🤖 Smart MultiPV                                | ✅ Applied | Uses `multipv=3` if `branching > 10`, and adapted `get_evaluation` and `parse_info`.|
| 6️⃣ | 🧷 Conditional analysis by previous tags         | ✅ Applied | If `classify_simple_pattern` returns a tag, uses `depth=6` and `multipv=1`.         |
| 7️⃣ | ⛓️ Avoid redundant analysis (FEN cache)         | ✅ Applied | Uses `eval_cache` to avoid recalculating evaluations by FEN.                        |
| 8️⃣ | ⚡ Avoid forced moves (`is_forced_move`)         | 🔜 In progress | Detected in `evaluate_tactical_features()`, needs to be used to skip analysis.      |
| 9️⃣ | 🧪 Accurate score difference (`score_diff`)      | ✅ Applied | Uses `extract_score()` and adjusts by player color.                                 |

---

## 📌 Other Implemented Points

| Topic                          | Status     | Comments                                                                  |
|--------------------------------|------------|---------------------------------------------------------------------------|
| 🧩 `classify_simple_pattern`   | ✅ Reused   | Fast tactical pre-classification (check, fork, pin, etc.).                |
| 🔄 `compare_to_best`           | ✅ Used     | Compares actual move with alternatives (`MultiPV`).                       |
| 🧠 `get_game_phase()`          | ✅ Used     | Determines game phase (opening, middlegame, endgame).                     |
| ⏱️ Decorator `@measure_execution_time` | ✅ Applied | On key functions to measure times.                                        |
| 🧪 Manual test of `multipv`    | ✅ Confirmed| Stockfish returns `list[dict]` correctly when using `multipv > 1`.        |

---

## Dataset Separation by Source

```
/data/games/
    ├── personal/
    │   └── cmess1315_games_2020_2024.pgn
    ├── novice/
    │   └── lichess_novice_2023.pgn
    ├── elite/
    │   └── lichess_elite_2023.pgn
    └── stockfish/
        └── stockfish_vs_stockfish_tests.pgn

/data/processed/
    ├── personal_games.parquet
    ├── novice_games.parquet
    ├── elite_games.parquet
    ├── stockfish_games.parquet
    └── training_dataset.parquet  ← final combined dataset
```

### ✅ Why have multiple datasets?

Separating datasets by source (personal, novice, elite, stockfish) offers key advantages:

1. **Control and traceability**
  - Lets you know how many games of each type you have.
  - Makes it easier to analyze errors by source.
  - Prevents mixing data that could bias the model (e.g., humans vs Stockfish).

2. **Targeted training**
  - Enables training specific models:
    - Personal: for personalized recommendations.
    - Novice: to detect frequent beginner mistakes.
    - Elite/Stockfish: to generate datasets of correct or perfect moves.

3. **Strategic balance and mixing**
  - Lets you decide the proportion of each game type in the final dataset.
  - Facilitates techniques like undersampling/oversampling depending on the goal.

🧩 **Why unify the datasets?**
- After processing each dataset separately, you can:
  - Apply the same analysis and feature extraction.
  - Add a `source` field to identify the origin.
  - Combine all into a final dataset for general training, evaluation, or cross-analysis.

The script `generate_combined_dataset.py` automates this process.

---

## 🧩 Optimal Summary of Datasets by Game Type

| Game type                      | Estimated amount | Main use                                                                  |
|--------------------------------|------------------|---------------------------------------------------------------------------|
| **Your own games**             | ~12,000          | Personalized training, error pattern detection, real evaluation           |
| **Novices (ELO < 1500)**       | 50k–200k         | Base training, style comparison, generalization                           |
| **Elite (ELO > 2200)**         | >300k            | Model good play, label correct moves, reference                           |
| **Stockfish vs Stockfish**     | >300k            | Perfect reference, ideal games, score validation                          |


  ### 🎯 Suggested proportions in the training dataset

  | Game type         | % in final dataset | Main reason                                    |
  |-------------------|-------------------|------------------------------------------------|
  | Your games        | 10–20%            | Personalization and evaluation                 |
  | Human novices     | 30–40%            | Base training and typical mistakes             |
  | Elite games       | 20–30%            | Model good play, contrast with novices         |
  | Stockfish test    | 10–20%            | Perfect reference and ideal moves              |

## 🧠 Model Training with DVC

This project uses [DVC](https://dvc.org/) to version datasets, trained models, and predictions. The pipeline automates process stages and ensures reproducibility of results.

### 📦 Basic pipeline structure

```text
export_features_by_source.py  ➜  generates datasets by source
merge_datasets.py             ➜  merges datasets into a general one
train_model.py                ➜  trains the machine learning model
predict_and_eval.py           ➜  generates predictions and evaluation metrics


## 🔜 Suggested next steps

- [#MIGRATED-TODO-1750286988] Apply `is_forced_move` in `detect_tactics_from_game` to skip unavoidable moves.
- [#MIGRATED-TODO-1750287009] Integrate `depth_score_diff`, `threatens_mate`, `is_forced_move` as additional analysis columns.
- [#MIGRATED-TODO-1750287014] Consolidate labels + tactical features in a single dataframe.
- [#MIGRATED-TODO-1750287017] Save Stockfish evaluations in the database for traceability and debugging.
- [#MIGRATED-TODO-1750288408] Implement unit tests for init_db.
- [#MIGRATED-TODO-1750288409] Implement unit tests for get_games.
- [#MIGRATED-TODO-1750288409] Implement unit tests for import_games.
- [#MIGRATED-TODO-1750288409] Implement unit tests for generate_features.
- [#MIGRATED-TODO-1750288410] Implement unit tests for analyze_tactics.
- [#MIGRATED-TODO-1750288410] Implement unit tests for export_dataset.
- [#MIGRATED-TODO-1750288411] Implement unit tests for generate_exercises.
- [#MIGRATED-TODO-1750288411] Consolidate scripts to implement logic for generation/visualization/navigation/editing of Lichess-style studies.
- [#MIGRATED-TODO-1750288412] Analyze EDA, clustering, machine learning notebooks based on generated datasets.


## 📌 Author

> Project created by cmessoftware for the Data Science diploma  
> Contact: [add your email or GitHub if you want]


