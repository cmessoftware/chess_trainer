# Phase Roadmap

## Planned Phases

| Phase | Scope | Key Deliverable | Tasks |
| --- | --- | --- | --- |
| 1 | core-engine + minimal api | stable PGN analysis pipeline with API endpoint | [02-phase-01-core-engine-minimal-api.md](02-phase-01-core-engine-minimal-api.md) |
| 2 | ml-error-classification | production-ready error classifier | [03-phase-02-ml-error-classification.md](03-phase-02-ml-error-classification.md) |
| 3 | orchestration | planner/executor/critic/memory integrated | [04-phase-03-orchestration.md](04-phase-03-orchestration.md) |
| 4 | rag | retrieval-backed knowledge injection | [05-phase-04-rag.md](05-phase-04-rag.md) |
| 5 | llm-grounding | grounded explanation service | [06-phase-05-llm-grounding.md](06-phase-05-llm-grounding.md) |
| 6 | advanced critic | stronger rule system and contradiction detection | [07-phase-06-advanced-critic.md](07-phase-06-advanced-critic.md) |
| 7 | memory + personalization | player profile and adaptive coaching | [08-phase-07-memory-personalization.md](08-phase-07-memory-personalization.md) |
| 8 | advanced ml | explainability and clustering extensions | [09-phase-08-advanced-ml.md](09-phase-08-advanced-ml.md) |
| 9 | critical-blunder-sequence | sequence detector in production | [10-phase-09-critical-blunder-sequence.md](10-phase-09-critical-blunder-sequence.md) |
| 10 | playstyles | playstyle profiling and recommendations | [11-phase-10-playstyles.md](11-phase-10-playstyles.md) |
| ext-ui | ACC UI renewal (chessops + Chessground) | Analysis workstation; one ID per `features/acc_ui_*` branch | [12-acc-ui-renewal-implementation-plan.md](12-acc-ui-renewal-implementation-plan.md) |

## Exit Criteria Per Phase

- Functional acceptance criteria met.
- Automated tests green for impacted domains.
- Observability metrics emitted and validated.
- Rollback path documented and tested.
