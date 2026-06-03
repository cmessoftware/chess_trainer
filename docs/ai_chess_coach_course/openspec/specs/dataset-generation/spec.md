# Capability: dataset-generation

## Purpose
Define dataset generation behavior for course module 02 from the database `features` table.

## Requirements

### Requirement: Features Table as Source
Training dataset generation SHALL read from the `features` table as source of truth.

#### Scenario: Build training dataset
- Given course module 02 execution
- When dataset generation starts
- Then records SHALL be loaded from the `features` table.

### Requirement: Canonical Target Label
The target label SHALL be `error_label`.

#### Scenario: Build supervised dataset
- Given a dataset split is prepared
- When labels are assigned
- Then the target SHALL be `error_label`.

### Requirement: Canonical Error Classes
The allowed course baseline classes SHALL be `good`, `inaccuracy`, `mistake`, and `blunder`.

#### Scenario: Label validation
- Given label cleaning is executed
- When class values are validated
- Then labels outside the canonical set SHALL be flagged for normalization.

### Requirement: Repository and Builder Entry Points
The course codebase SHALL expose dedicated files for feature access and dataset build orchestration.

#### Scenario: Course code navigation
- Given a developer inspects the course implementation
- When data access and dataset build files are checked
- Then the expected entry points SHALL include:
  - `data_access/features_repository.py`
  - `dataset/build_training_dataset.py`
