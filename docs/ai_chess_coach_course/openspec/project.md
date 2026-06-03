# AI Chess Coach Course - OpenSpec Project Context

## Scope
This OpenSpec workspace defines requirements for the AI Engineering course based on ChessTrainer.
Only course-related artifacts are in scope: notebooks, teaching pipeline integration, dataset generation, and curriculum evolution.

## System Context
The course reuses existing project infrastructure and does not reimplement core pipeline logic that already exists in the repository.

Base flow:

PGN (.pgn / .pgn.gz)
-> existing feature extraction script
-> features table (database)
-> dataset builder
-> ML prediction
-> pattern detection
-> RAG retrieval
-> LLM explanation
-> report

## Data and Inputs
- PGN datasets live under `data/games/`.
- Current dataset groups: `novice/`, `personal/`, `fide/`, `elite/`, `engine/`.
- Compressed PGN input (`.pgn.gz`) must be supported through existing extraction tooling.

## Architectural Constraints
- Reuse the existing feature extraction script.
- Do not create a new PGN parser for the course workflow.
- Use the existing database-backed `features` source as the canonical input for dataset generation.

## Current Course Status (v1)
- Implemented notebooks:
  - `01_architecture_overview.ipynb`
  - `02_run_feature_pipeline.ipynb`
  - `03_dataset_builder.ipynb`
- Modules 03-12 are planned and currently pending implementation.

## Conventions
- Course requirements are represented in `specs/` as the current accepted state.
- In-progress work is defined in `changes/<change-name>/`.
- Completed changes are moved to `changes/archive/`.
