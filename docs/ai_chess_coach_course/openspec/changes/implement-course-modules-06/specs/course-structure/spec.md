# Delta: course-structure

## ADDED Requirements

### Requirement: Module 06 Canonical Delivery
Module 06 SHALL be implemented as an independently trackable course change.

#### Scenario: Module 06 implementation check
- Given change implement-course-modules-06 is active
- When implementation artifacts are reviewed
- Then notebook 06_shap_analysis.ipynb SHALL exist and reflect Module 06 objectives.

### Requirement: Module 06 Deliverable Coverage
Module 06 SHALL include all declared deliverables in its change tasks.

#### Scenario: Module 06 deliverable validation
- Given Module 06 tasks are marked complete
- When outputs are validated
- Then all required deliverables SHALL be verifiable in the notebook and/or supporting artifacts.
