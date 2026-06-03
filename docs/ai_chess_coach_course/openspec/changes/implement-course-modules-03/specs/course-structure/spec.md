# Delta: course-structure

## ADDED Requirements

### Requirement: Module 03 Canonical Artifact
Module 03 (Feature Analysis) SHALL provide one canonical executable notebook.

#### Scenario: Module 03 artifact check
- Given module 03 is implemented
- When course artifacts are reviewed
- Then `03_feature_analysis.ipynb` SHALL exist and be runnable top-to-bottom.

### Requirement: Module 03 Analysis Coverage
Module 03 SHALL include the baseline analysis set defined in the course roadmap.

#### Scenario: Coverage validation
- Given a user executes module 03 notebook
- When outputs are generated
- Then the notebook SHALL include at least:
  - error distribution
  - error by ELO
  - error by opening
  - centipawn-loss analysis

