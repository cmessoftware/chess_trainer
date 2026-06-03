# Delta: course-structure

## ADDED Requirements

### Requirement: Module 12 Canonical Delivery
Module 12 SHALL be implemented as an independently trackable course change.

#### Scenario: Module 12 implementation check
- Given change implement-course-modules-12 is active
- When implementation artifacts are reviewed
- Then notebook 12_mvp_ui_fastapi.ipynb SHALL exist and reflect Module 12 objectives.

### Requirement: Module 12 Deliverable Coverage
Module 12 SHALL include all declared deliverables in its change tasks.

#### Scenario: Module 12 deliverable validation
- Given Module 12 tasks are marked complete
- When outputs are validated
- Then all required deliverables SHALL be verifiable in the notebook and/or supporting artifacts.
