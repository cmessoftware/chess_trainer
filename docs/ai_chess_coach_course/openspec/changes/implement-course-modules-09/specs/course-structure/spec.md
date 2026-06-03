# Delta: course-structure

## ADDED Requirements

### Requirement: Module 09 Canonical Delivery
Module 09 SHALL be implemented as an independently trackable course change.

#### Scenario: Module 09 implementation check
- Given change implement-course-modules-09 is active
- When implementation artifacts are reviewed
- Then notebook 09_llm_consistency_tests.ipynb SHALL exist and reflect Module 09 objectives.

### Requirement: Module 09 Deliverable Coverage
Module 09 SHALL include all declared deliverables in its change tasks.

#### Scenario: Module 09 deliverable validation
- Given Module 09 tasks are marked complete
- When outputs are validated
- Then all required deliverables SHALL be verifiable in the notebook and/or supporting artifacts.
