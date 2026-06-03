# Capability: course-structure

## Purpose
Define the current structure and progression of the AI Engineering course based on ChessTrainer.

## Requirements

### Requirement: Modular Course Progression
The course SHALL be organized into sequential modules from 00 to 12.

#### Scenario: Canonical module list
- Given the current course definition
- When the module map is reviewed
- Then it SHALL include modules `00_foundations` through `12_phase2_agentic_system`.

### Requirement: Current Implemented Baseline
The course SHALL treat modules 00, 01, and 02 as the implemented baseline for v1.

#### Scenario: Implemented notebooks are available
- Given the v1 baseline
- When implemented artifacts are listed
- Then the available notebooks SHALL include:
  - `01_architecture_overview.ipynb`
  - `02_run_feature_pipeline.ipynb`
  - `03_dataset_builder.ipynb`

### Requirement: Pending Scope Visibility
Modules 03-12 SHALL remain explicitly marked as planned/pending until implemented through tracked changes.

#### Scenario: Reviewing pending modules
- Given the current OpenSpec state
- When a user asks what remains
- Then modules 03-12 SHALL be identified as pending implementation.
