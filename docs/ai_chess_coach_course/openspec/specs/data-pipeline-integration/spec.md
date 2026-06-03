# Capability: data-pipeline-integration

## Purpose
Define how the course integrates with the existing PGN-to-features pipeline.

## Requirements

### Requirement: Reuse Existing Feature Extraction
The course workflow SHALL reuse the existing feature extraction script from the repository.

#### Scenario: Running the course pipeline notebook
- Given module 01 is executed
- When feature extraction is triggered
- Then the workflow SHALL call the existing script instead of reimplementing extraction logic.

### Requirement: No New PGN Parser
The course SHALL NOT introduce a new PGN parser in course artifacts.

#### Scenario: Handling compressed and plain PGN
- Given PGN input files may be `.pgn` or `.pgn.gz`
- When ingestion is executed
- Then existing project tooling SHALL be used for detection, decompression, and parsing.

### Requirement: Canonical Input Location
Course data ingestion SHALL use `data/games/` as canonical source.

#### Scenario: Dataset type selection
- Given a training run is prepared
- When source folders are selected
- Then sources SHALL map to known dataset groups: `novice/`, `personal/`, `fide/`, `elite/`, `engine/`.
