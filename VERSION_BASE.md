# CHESS TRAINER - Version: v0.1.20-f9d0260

# ♟ chess_trainer – Analysis and Training with Elite Games

This project automates the import, analysis, labeling, and training from thousands of games played by elite players (ELO >2300), combining tactical analysis with visual exploration and exercise generation.

---

## 📚 Documentation Index

### Core Documentation
- **[Main README](./README.md)** - Project overview and quick start guide
- **[README (Español)](./README_es.md)** - Descripción del proyecto y guía rápida en español
- **[Version Base (English)](./VERSION_BASE.md)** - Complete project documentation (this file)
- **[Version Base (Español)](./VERSION_BASE_es.md)** - Documentación completa del proyecto en español

### Configuration and Setup
- **[Datasets Volumes Configuration](./DATASETS_VOLUMES_CONFIG.md)** - Docker volumes setup for dataset sharing
- **[Configuración de Volúmenes de Datasets](./DATASETS_VOLUMES_CONFIG_es.md)** - Configuración de volúmenes Docker para compartir datasets

### Architecture and Development
- **[System Architecture](./src/architecture.md)** - System architecture diagram and component overview
- **[Arquitectura del Sistema](./src/architecture_es.md)** - Diagrama de arquitectura y descripción de componentes
- **[Feature Generation Enhancement](./src/scripts/GENERATE_FEATURES_ENHANCEMENT.md)** - Feature generation improvements documentation

### Testing
- **[Tests Documentation](./tests/README.md)** - Comprehensive testing guide and runner documentation
- **[Documentación de Pruebas](./tests/README_es.md)** - Guía completa de pruebas y documentación del ejecutor
- **[PostgreSQL Migration](./tests/POSTGRESQL_MIGRATION_COMPLETE.md)** - Database migration documentation
- **[Unification Complete](./tests/UNIFICATION_COMPLETE.md)** - Project unification documentation

### Reports
- **[Test Reports](./test_reports/)** - Automated test execution reports
- **[Analysis Reports](./test_reports/analyze_tactics_parallel_20250629_035806_summary.md)** - Tactical analysis execution summaries

### 📦 Installation & Requirements

**All dependencies are automatically installed via Docker containers:**
- **[Dockerfile](./dockerfile)** - Main application container with Python 3.11+ and all required packages
- **[Dockerfile.notebooks](./dockerfile.notebooks)** - Jupyter environment with Keras, TensorFlow, and data science libraries
- **[requirements.txt](./requirements.txt)** - Complete Python dependencies list
- **[docker-compose.yml](./docker-compose.yml)** - Container orchestration with automatic setup

**Manual installation (if not using Docker):**
```bash
pip install -r requirements.txt  # Python packages
apt install stockfish           # Chess engine (Linux)
```

---

## 🚀 Automated Container Building with Scripts

This project includes scripts to build containers easily, without needing to pass parameters manually.

Available containers are:

| Script                   | Description                                                                               | Generated Image           |
| ------------------------ | ----------------------------------------------------------------------------------------- | ------------------------- |
| `build_app.sh`           | Builds the Streamlit application container                                                | `chess_trainer_app`       |
| `build_notebooks.sh`     | Builds the JupyterLab container with Keras and TensorFlow                                 | `chess_trainer_notebooks` |
| `build_up_clean_all.ps1` | **Windows PowerShell**: Builds both containers, starts services, and cleans unused images | All containers + cleanup  |

---

### 🛠️ Requirements

- Docker version **24.x** or higher (required for `--ignore-file`)
- Scripts with execution permissions

To give permissions:

```bash
chmod +x build_app.sh build_notebooks.sh
```

**For Windows users**, the PowerShell script `build_up_clean_all.ps1` provides automated setup without requiring permission changes.
---

## 🚀 How to Build the Containers

### Linux/macOS Users:
**For the Streamlit application:**
```bash
./build_app.sh
```
**For the JupyterLab environment:**
```bash
./build_notebooks.sh
```

### Windows Users:
**One-command setup (builds, starts, and cleans):**
```powershell
.\build_up_clean_all.ps1
```

This PowerShell script will:
- 🚀 Build both chess_trainer and notebooks images
- ✅ Start all containers in detached mode  
- 🧹 Clean up unused Docker images automatically
- 🏁 Show active containers status

### 🎯 Benefits of Windows PowerShell Automation:
- **Single Command Setup**: Complete environment setup with one command
- **No Permission Management**: Avoids Unix-style `chmod` permission requirements
- **Automatic Cleanup**: Removes unused Docker images to save disk space
- **Background Execution**: Containers run in detached mode for continuous operation
- **Instant Feedback**: Shows running containers status after completion
- **Error Prevention**: Automated sequence reduces manual configuration errors
- **Time Saving**: Eliminates need for multiple individual docker commands

## 📂 Project Structure

```
chess_trainer/
├── alembic/                     # Database migration management
│   ├── env.py
│   ├── versions/
│   └── README
├── data/                        # Game data and databases
│   ├── chess_trainer.db
│   └── Undestanding ML/
├── img/                         # Project images and diagrams
│   ├── architecture.png
│   └── chessboard.png
├── logs/                        # Application logs
├── notebooks/                   # Jupyter notebooks for analysis
│   ├── chess_evaluation.ipynb
│   ├── eda_advanced.ipynb
│   ├── eda_analysis.ipynb
│   ├── ml_analize_tacticals_embedings.ipynb
│   └── data/
├── src/                         # Main source code
│   ├── config/                  # Configuration files
│   ├── data/                    # Data processing utilities
│   ├── db/                      # Database utilities and models
│   │   ├── postgres_utils.py
│   │   └── repository/
│   ├── decorators/              # Python decorators
│   ├── modules/                 # Core business logic modules
│   │   ├── generate_dataset.py
│   │   ├── extractor.py
│   │   ├── tactics_generator.py
│   │   └── eda_utils.py
│   ├── pages/                   # Streamlit UI pages
│   │   ├── elite_explorer.py
│   │   ├── elite_stats.py
│   │   ├── elite_training.py
│   │   ├── export_exercises.py
│   │   ├── tag_games_ui.py
│   │   └── streamlit_eda.py
│   ├── pipeline/                # Data processing pipelines
│   ├── scripts/                 # Standalone execution scripts
│   │   ├── analyze_games_tactics_parallel.py
│   │   ├── generate_features_parallel.py
│   │   ├── generate_pgn_from_chess_server.py
│   │   ├── generate_exercises_from_elite.py
│   │   ├── inspect_db.py
│   │   └── run_pipeline.sh
│   ├── services/                # Service layer components
│   │   ├── features_export_service.py
│   │   ├── get_lichess_studies.py
│   │   └── study_importer_service.py
│   ├── tools/                   # Utility tools
│   │   ├── elite_explorer.py
│   │   └── create_issues_from_json.py
│   ├── validators/              # Data validation utilities
│   └── app.py                   # Main Streamlit application
├── tests/                       # Unified test suite
│   ├── test_elite_pipeline.py
│   ├── test_db_integrity.py
│   ├── test_analyze_games_tactics_parallel.py
│   └── run_tests.sh
├── test_reports/                # Test execution reports
├── docker-compose.yml           # Container orchestration
├── dockerfile                   # Main app container
├── dockerfile.notebooks         # Jupyter container
├── build_app.sh                 # App container build script
├── build_notebooks.sh           # Notebook container build script
├── build_up_clean_all.ps1       # Windows PowerShell: Complete setup script
├── alembic.ini                  # Database migration config
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables
└── README.md                    # Project documentation
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

## Design for Tactical Analysis

| Aspect                                 | Advantage                          |
| -------------------------------------- | ---------------------------------- |
| depth by phase                         | Saves time without losing accuracy |
| multipv only when many options         | Doesn't waste CPU resources        |
| compare_to_best avoids false positives | Improves label quality             |
| classify_tactical_pattern still works  | Classic tags like fork, pin, mate  |
| eval_cache                             | Avoids repeated evaluations by FEN |

## Optimizations to Speed Up Tactical Analysis (reduce from days to hours) 
**Updated: 2025-06-02**

## ✅ List of optimizations in `tactical_analysis.py` - `chess_trainer`

| Nº  | Optimization                               | Status        | Details / Comments                                                                   |
| --- | ------------------------------------------ | ------------- | ------------------------------------------------------------------------------------ |
| 1️⃣   | 🔻 Reduce fixed depth                       | ✅ Applied     | Uses `depth=6` for moves with `pre_tag`; dynamic values by phase for the rest.       |
| 2️⃣   | ⏭️ Skip first moves                         | ✅ Applied     | If `move_number <= 6`, analysis is skipped. Controlled by `opening_move_threshold`.  |
| 3️⃣   | 🧠 Variable depth by phase                  | ✅ Applied     | Uses `PHASE_DEPTHS` based on game phase (`opening`, `middlegame`, `endgame`).        |
| 4️⃣   | 🧮 Branching factor                         | ✅ Applied     | If `branching < 5`, the move is skipped. Used as a low complexity indicator.         |
| 5️⃣   | 🤖 Smart MultiPV                            | ✅ Applied     | Uses `multipv=3` if `branching > 10`, and adapted `get_evaluation` and `parse_info`. |
| 6️⃣   | 🧷 Conditional analysis by previous tags    | ✅ Applied     | If `classify_simple_pattern` returns a tag, uses `depth=6` and `multipv=1`.          |
| 7️⃣   | ⛓️ Avoid redundant analysis (FEN cache)     | ✅ Applied     | Uses `eval_cache` to avoid recalculating evaluations by FEN.                         |
| 8️⃣   | ⚡ Avoid forced moves (`is_forced_move`)    | 🔜 In progress | Detected in `evaluate_tactical_features()`, needs to be used to skip analysis.       |
| 9️⃣   | 🧪 Accurate score difference (`score_diff`) | ✅ Applied     | Uses `extract_score()` and adjusts by player color.                                  |

---

## 📌 Other Implemented Points

| Topic                                 | Status      | Comments                                                           |
| ------------------------------------- | ----------- | ------------------------------------------------------------------ |
| 🧩 `classify_simple_pattern`           | ✅ Reused    | Fast tactical pre-classification (check, fork, pin, etc.).         |
| 🔄 `compare_to_best`                   | ✅ Used      | Compares actual move with alternatives (`MultiPV`).                |
| 🧠 `get_game_phase()`                  | ✅ Used      | Determines game phase (opening, middlegame, endgame).              |
| ⏱️ Decorator `@measure_execution_time` | ✅ Applied   | On key functions to measure times.                                 |
| 🧪 Manual test of `multipv`            | ✅ Confirmed | Stockfish returns `list[dict]` correctly when using `multipv > 1`. |

---

## 🧠 Model Training with DVC

This project uses [DVC](https://dvc.org/) to version datasets, trained models, and predictions. The pipeline automates process stages and ensures reproducibility of results.

### 📦 Basic pipeline structure

```text
export_features_by_source.py  ➜  generates datasets by source
merge_datasets.py             ➜  merges datasets into a general one
train_model.py                ➜  trains the machine learning model
predict_and_eval.py           ➜  generates predictions and evaluation metrics
```

## 🧠 Tactics Generator Module (`tactics_generator.py`)

This module is part of the automatic tactical exercise generation system for the `chess_trainer` project. Its goal is to analyze previously processed games, detect moves with instructional value, and store them as reusable tactical exercises.

### ✅ Implemented functionalities

- Automatically creates the `tactics` table if it doesn't exist.
- Extracts positions with tactical tags (`tactical_tags`) from the `features` table.
- Filters candidate moves based on criteria such as:
  - Significant material loss or gain (`score_diff`)
  - Presence of patterns like pins, double attacks, sacrifices, etc.
- Generates a unique `tactic_id` per move.
- Inserts exercises into the database with the following structure:
  - `tactic_id`
  - `fen`
  - `move_uci`
  - `error_label`
  - `tags`
  - `game_id`
  - `ply`
  - `mate_in`
  - `depth_score_diff`
  - Timestamps and status

### 🔄 Typical usage

The module is invoked as part of the pipeline with:

```bash
python -m app.src.modules.tactics_generator
```

## 🧠 Next Steps (Roadmap)
 - Connect generated exercises with existing or new studies in the studies table.
 - Add source field (e.g. auto, manual, lichess_import) to distinguish their origin.
 - Integrate interface in Streamlit to visualize and interact with them.
 - Suggest similar exercises based on the most frequent tactical error (error_label).
 - Export selected exercises as PGN, JSON or PDF.

## 🧩 Current State of Predictive Functionalities in `chess_trainer`

| Aspect                                | Status            | Description                                                                          |
| ------------------------------------- | ----------------- | ------------------------------------------------------------------------------------ |
| Game and opening analysis             | ✅ Implemented     | Detailed evaluation of moves and openings using Stockfish.                           |
| Position evaluation                   | ✅ Implemented     | Traditional heuristic function to evaluate positions.                                |
| Personalized training based on errors | ✅ Implemented     | Adaptation of sessions based on user's frequent errors.                              |
| Game database integration             | ✅ Implemented     | Trend and pattern analysis from a game database.                                     |
| User playing style analysis           | ⚠️ Partial         | Basic style analysis, lacks deep characterization (speed, risk, strategic patterns). |
| Neural networks for evaluation        | ❌ Not implemented | Neural networks are not used to evaluate positions or moves.                         |
| Self-learning training                | ❌ Not implemented | Self-play module for self-learning is missing.                                       |
| Endgame databases (tablebases)        | ❌ Not implemented | Tablebases are not used for perfect endgames.                                        |
| Opponent playing style analysis       | ❌ Not implemented | Opponent style is not analyzed.                                                      |
| Progress and metrics visualization    | ❌ Not implemented | Interface to show user progress and metrics is missing.                              |

### 💡 Ideas to Consider

- **Neural networks for evaluation:** Integrate NNUE-type models to improve positional evaluation.
- **Self-learning (self-play):** Allow the engine to play against itself to discover new strategies.
- **Advanced playing style analysis:** Characterize user style (aggressive, defensive, etc.) using data analysis.
- **Tablebase integration:** Use bases like Syzygy for endgame precision.
- **Opponent analysis:** Analyze previous games of rivals to adapt strategies.
- **Progress visualization:** Develop dashboards with user metrics and evolution.

---

## ✅ Recommended Next Steps

1. **Implement neural networks for evaluation:** Explore NNUE or similar integration.
2. **Develop self-learning system:** Create self-play module for autonomous training.
3. **Expand playing style analysis:** Deepen user and opponent characterization.
4. **Integrate endgame databases:** Incorporate Syzygy to improve endgame play.
5. **Develop progress visualization interface:** Dashboard in Streamlit or own panel.

---

## 🛠️ Implementation Roadmap

### Stage 1: Diagnosis and Personalization (High Priority)

| Task                      | Objective                          | Technique / Tool                             | Estimated Time |
| ------------------------- | ---------------------------------- | -------------------------------------------- | -------------- |
| 🔍 Advanced style analysis | Identify user profile              | Clustering + metrics (score_diff, risk, etc) | 3 days         |
| 📊 Progress visualization  | Show evolution and frequent errors | Dashboard in Streamlit                       | 2 days         |
| ⚙️ Opponent analysis       | Detect patterns in frequent rivals | Filtering and simplified clustering          | 2 days         |

**Result:** Chess_trainer adapts to the user, showing profile, errors and key rivals.

---

### Stage 2: AI Enhancement (Medium Priority)

| Task                        | Objective                                  | Technique / Tool                  | Estimated Time |
| --------------------------- | ------------------------------------------ | --------------------------------- | -------------- |
| 🧠 NNUE-based evaluator      | More contextual and positional evaluations | Open source NNUE models           | 4-6 days       |
| ♟️ Tablebase integration     | Perfect endgame play                       | Syzygy + python-chess             | 2 days         |
| 🔁 Self-learning (Self-Play) | Autonomous system training                 | Game simulation and reinforcement | 5 days         |

---

### Stage 3: Studies and Dynamic Tactical Flow

| Task                          | Objective                                      | Technique / Tool                            | Estimated Time |
| ----------------------------- | ---------------------------------------------- | ------------------------------------------- | -------------- |
| 🧩 Automatic study generator   | Create interactive Lichess-style studies       | Extraction of segments with high score_diff | 2 days         |
| 🧠 Tactical training suggester | Recommend exercises based on frequent failures | tactical_recommender.py                     | 2 days         |

---

### Stage 4: Optional Extras and R&D

| Task                            | Objective                                 | Technique / Tool                   | Status   |
| ------------------------------- | ----------------------------------------- | ---------------------------------- | -------- |
| 🧮 Future performance prediction | Predict result based on opening and moves | Logistic Regression / RandomForest | New idea |
| 🎮 Video game-like interface     | Gamification and level achievements       | Badge system + SQLite tracking     | New idea |

---

## ✅ Pros and Cons of Functionalities

| Aspect                   | Advantages                        | Disadvantages                           |
| ------------------------ | --------------------------------- | --------------------------------------- |
| Tactical personalization | Focused and motivating training   | Requires good labeling and clustering   |
| NNUE evaluation          | More positional precision         | Moderate technical complexity           |
| Self-learning            | Autonomous and replicable system  | Can consume CPU if not optimized        |
| Progress visualization   | Clear perception of improvement   | Can generate frustration if no progress |
| Tablebases               | Perfect endgame play              | Only applies to specific cases          |
| Opponent analysis        | Better preparation against rivals | Depends on available previous games     |

## 🧠 Machine Learning Summary in `chess_trainer`

### ✅ Implemented / sketched modules

| Module / File              | Description                                                              | Status               |
| -------------------------- | ------------------------------------------------------------------------ | -------------------- |
| `tactical_evaluator.py`    | Evaluates moves with Stockfish and labels tactical errors                | ✅ Implemented        |
| `training_dataset.parquet` | Dataset generated with multiple features per move (tactical, positional) | ✅ Generated          |
| `eda_feedback.ipynb`       | Exploratory analysis of tactical dataset with graphs and boxplots        | ✅ In use             |
| `feedback_analysis.ipynb`  | Analyzes frequent errors, problematic openings, blunder patterns         | ✅ Base implemented   |
| `error_label_model.ipynb`  | Trains a supervised model to predict error type (`error_label`)          | ⚠️ Partially done     |
| `predictions.parquet`      | Saves ML model predictions per move                                      | ✅ Implemented        |
| `tactical_recommender.py`  | Recommends tactical exercises based on detected weaknesses               | ✅ Implemented (base) |

---

### 📊 Applied or prepared ML techniques

| Technique                      | Use                                                  | Status                    |
| ------------------------------ | ---------------------------------------------------- | ------------------------- |
| Supervised learning            | Error classification (`error_label`) per move        | ⚠️ Partial (initial model) |
| Clustering (K-Means)           | Grouping moves by error type, phase, etc.            | ⚠️ In notebooks            |
| PCA                            | Dimensionality reduction for visualization           | ✅ Applied in EDA          |
| Feature Engineering            | Building metrics like `score_diff`, `mobility`, etc. | ✅ Done                    |
| Decision trees / Random Forest | Candidate model for classifying tactical errors      | 💡 Suggested idea          |
| Logistic regression            | Binary prediction of blunder / no blunder            | 💡 Suggested idea          |

---

### 📁 Features extracted per move

**Already implemented in the dataset:**

- `score_diff` (engine evaluation)
- `material_total`, `material_balance`
- `num_pieces`, `phase`
- `branching_factor`, `self_mobility`, `opponent_mobility`
- `is_low_mobility`, `is_center_controlled`, `is_pawn_endgame`
- `move_number`, `player_color`, `has_castling_rights`
- `is_repetition`, `threatens_mate`, `is_forced_move`, `depth_score_diff`
- `tactical_tags` (pin, double attack, etc.)

**Pending implementation:**
- mate_in
- standardized_elo

---

### ❌ Missing in ML pipeline

| Missing                  | Description                                                           |
| ------------------------ | --------------------------------------------------------------------- |
| Formal model training    | Define and train final model (e.g: RandomForest, Logistic Regression) |
| Model evaluation         | Cross-validation, confusion matrix, F1 or accuracy metrics            |
| Model export             | Serialize as `.pkl` or `.joblib` for production use                   |
| Production inference     | Load model from Python and label new moves on the fly                 |
| Prediction visualization | Show `predictions.csv` in interface for user feedback                 |

---

### 🗂️ Suggested next steps to complete ML

| Step | Action                                                        | Module/Notebook  |
| ---- | ------------------------------------------------------------- | ---------------- |
| 1️⃣    | Finish `error_label_model.ipynb` training complete model      | Jupyter          |
| 2️⃣    | Evaluate model and save as `trained_model.pkl`                | Jupyter + joblib |
| 3️⃣    | Create `ml_predictor.py` module to load model and label moves | Python           |
| 4️⃣    | Integrate to `full_pipeline.py` or `tactical_analysis.py`     | Python           |
| 5️⃣    | Visualize predictions in Streamlit with examples and feedback | Streamlit        |


## 📌 Author

> Project created by cmessoftware for the Data Science diploma  
> Contact: [add your email or GitHub if you want]


