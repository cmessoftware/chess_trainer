## Phase 00 - AI Engineering Course Based on ChessTrainer

--- v1 Status ---
Notebooks available in docs/courses/ (alongside this file):
  00_architecture_overview.ipynb   — Module 0: Foundations  ✅
  01_run_feature_pipeline.ipynb    — Module 1: Data Pipeline  ✅
  02_dataset_builder.ipynb         — Module 2: Dataset Generation  ✅
Modules 4-12: pending future implementation.
-----------------


The course must reuse the project's existing infrastructure.
It must not reimplement the feature extraction pipeline.

## System Architecture
### Base Pipeline
Plain text

PGN (.pgn / .pgn.gz)
      ↓
feature extraction script (existing)
      ↓
features table (database)
      ↓
dataset builder
      ↓
ML prediction
      ↓
pattern detection
      ↓
RAG retrieval
      ↓
LLM explanation
      ↓
report

PGN files can be compressed.
Location:

data/games/
Dataset Types:

      novice/
      personal/
      fide/
      elite/
      engine/

Existing Script
There is a script that:

      detects pgn.gz files
      decompresses them
      parses games
      executes analysis
      generates features
      saves features to database
      Copilot must reuse it.
Expected Example:
Python
subprocess.run(["python", "scripts/generate_features.py"])
Do not create a new parser.
Database
Main Table:

features
Expected Columns:

game_id
move_number
fen
elo
opening
material_total
num_pieces
king_safety
center_control
has_castling_rights
is_pawn_endgame
score_cp
mate_in
depth_score_diff
error_label
tags
Copilot Must Generate:

data_access/features_repository.py
Dataset Builder
Pipeline:

features table
      ↓
dataset cleaning
      ↓
feature encoding
      ↓
training dataset
File:

dataset/build_training_dataset.py
Target:

error_label
Classes:

good
inaccuracy
mistake
blunder
## Course Structure
Copilot Must Generate:

### ai_engineer_course/
modules:

### Phase 1: Foundations + notebooks + helper scripts (NO UI, NO agentic orchestration)

Scope constraints for Phase 1:
- Use notebooks and helper scripts only.
- Do not implement UI.
- Do not implement planner -> executor -> critic -> memory in this phase.
- Show baseline LLM limitations in tests (inconsistencies and hallucinations) as part of learning goals.

- 00_foundations
- 01_data_pipeline
- 02_dataset_generation
- 03_feature_analysis
- 04_machine_learning
- 05_mlflow_experiment_tracking
- 06_shap_model_evaluation
- 07_rag_system
- 08_llm_explanations
- 09_llm_consistency_and_hallucination_tests

### Phase 2: Agentic architecture (planner -> executor -> critic -> memory)

- 10_phase2_agentic_architecture
- 11_capstone

### Phase 3: MVP delivery (basic UI + FastAPI) and production bridge

- 12_mvp_ui_fastapi
- 13_react_vite_production_bridge

## Phase 1
### Module 0 — Foundations
Objective:
understand complete pipeline.
Notebook:

00_architecture_overview.ipynb  [v1 — available in docs/ai_chess_coach_course/]

### Module 1 — Data Pipeline
Do not implement parsing.
Notebook:

01_run_feature_pipeline.ipynb  [v1 — available in docs/ai_chess_coach_course/]
Executes existing script.

### Module 2 — Dataset Generation
Notebook:

02_dataset_builder.ipynb  [v1 — available in docs/ai_chess_coach_course/]
Reads features table.

### Module 3 — Feature Analysis
Notebook:

03_feature_analysis.ipynb
Analysis:

error distribution
error by elo
error by opening
centipawn loss

### Module 4 — Machine Learning
Notebook:

04_ml_training.ipynb

Models:

Multi Class LogistRegression
KNN
SVM
RandomForest
LightGBM
XGBoost
CatBoost

Scripts:

ml/train_random_forest.py
ml/train_lightgbm.py
ml/train_xgboost.py
ml/train_catboost.py

### Module 5 — MLflow Experiment Tracking

Notebook:
05_mlflow_experiment_tracking.ipynb

Notebook must contain:

- Setup MLflow using sqlite backend for local tracking.
- Data loading and exploration with MLflow logging.
- Feature engineering steps with MLflow tracking.
- Model training with params/metrics/artifacts logged.
- Run comparison and best-model selection criteria.

### Module 6 — Model Explainability

Notebook:
06_shap_analysis.ipynb

Methods:

SHAP
feature importance

### Module 7 — RAG
Notebook:
07_rag_analysis.ipynb

Sources:

chess books
annotated games
stored explanations
Pipeline:

text chunking
embedding
vector database
retrieval
Tools:

ChromaDB
LangChain

### Module 8 — LLM Explanation

Notebook:
08_llm_explanation.ipynb

Pipeline:

ML prediction
↓
pattern detection
↓
RAG retrieval
↓
LLM explanation
Stack:

LangChain
Ollama
llama3.2:3b
Files:

llm/prompt_templates.py
llm/llm_explainer.py

### Module 9 — LLM Consistency and Hallucination Tests
Objective:
make LLM limitations explicit before agentic safeguards are introduced.

Deliverables:

- test suite with inconsistent/hallucinated response examples
- baseline guardrails and evaluation checks
- report documenting failure patterns and mitigations to be addressed in Phase 2

## Phase 2

### Module 10 — Advanced Agentic Architecture
This phase introduces architecture with:

Planner
Executor
Critic
Memory

Phase 2 Architecture

analysis_request
      ↓
planner
      ↓
executor
      ↓
critic
      ↓
memory
      ↓
final explanation

Components

Planner
Decides which steps to execute.
Example:

analyze_position
detect_patterns
retrieve_context
generate_explanation
File:

agents/planner.py

Executor
Executes tools.
Available Tools:

stockfish_tool
feature_lookup_tool
dataset_search_tool
rag_retriever
File:

agents/executor.py

Critic
Verifies consistency.
Must detect:

contradictions with Stockfish
incorrect explanations
conceptual errors
File:

agents/critic.py

Memory
Stores:

analysis history
detected patterns
player's frequent errors
Allows personalization.
File:

agents/memory.py

Complete Phase 2 Flow

position
↓
planner
↓
executor
↓
pattern detection
↓
RAG retrieval
↓
LLM explanation
↓
critic validation
↓
memory update
↓
final report

### Module 11 — Capstone (Agentic Backend Integration)
Objective:
integrate all Phase 1 + Phase 2 backend components in one coherent AI Chess Coach workflow.

Scope:

- no full UI required yet
- backend and orchestration integration first

Mandatory Capstone Features:

- upload/read PGN input
- run existing feature pipeline (reuse, no parser rewrite)
- predict move quality/errors
- generate grounded explanation (RAG + LLM)
- validate explanation consistency via critic
- persist memory signals for personalization

Mandatory Evidence:

- demo script or notebook running end-to-end
- MLflow run references for model stage
- evaluation report including inconsistency/hallucination findings and improvements vs Module 9 baseline

## Phase 3

### Module 12 — MVP UI + FastAPI (Final Course Demo)
Objective:
deliver a quick MVP of AI Chess Coach visible to end users.

Architecture:

Basic UI (Streamlit or minimal web UI)
↓
FastAPI
↓
ML + RAG + LLM + Agentic backend services
↓
database

Endpoints:

/analyze_game
/predict_move_quality
/explain_position

### Module 13 — React + Vite Production Bridge
Objective:
define migration path from course MVP to production-grade ChessInsight rebuild using React + Vite.

Deliverables:

- UI/API contract definition for frontend migration
- component/page map from MVP to React + Vite
- phased migration plan from course MVP to production ChessInsight architecture

Expected Result
Copilot must generate approximately:

30 notebooks
40 scripts
Complete ML pipeline
RAG pipeline
LLM explanation system
agentic architecture
MVP API + basic UI
React + Vite migration foundation

Everything built on the real ChessTrainer system.
