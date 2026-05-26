# Module Taxonomy

## Domains and Submodules

| Domain | Submodules |
| --- | --- |
| core-analysis | pgn-parser, stockfish-analysis, feature-extraction, tactical-tagging, phase-detection, evaluation-normalization, ml-error-classification, ml-critical-blunder-sequence, ml-playstyle-clustering, ml-model-evaluation, ml-shap-explainability |
| core-orchestration | planner, executor, critic, memory, execution-policies, fallback-strategies, validation-rules |
| core-knowledge | chess-document-extraction, chess-embeddings, chromadb-indexing, rag-retrieval, llm-grounding, llm-prompt-engineering, llm-explanation-generation, hallucination-control |
| core-contracts | analysis-result-schema, evidence-schema, recommendation-schema, versioned-domain-contracts |
| ext-api-fastapi | rest-contracts, dto-schemas, orchestrated-analysis-api, auth-security, websocket-streaming, api-versioning |
| ext-ui | dashboard, pgn-upload, move-analysis-viewer, chessboard-ui, training-center, player-profile, explainability-ui |
| ext-observability | mlflow-tracking, prompt-logging, critic-metrics, execution-metrics, telemetry, audit-trails, inference-monitoring |
| ext-devops | docker, deployment, feature-flags, migrations, rollback-strategies, ci-cd, infrastructure |
| ext-testing | unit-tests, integration-tests, e2e-tests, llm-evaluation, regression-tests, prompt-tests, critic-validation-tests, synthetic-games |
| ext-research | notebooks, experiments, datasets-analysis, feature-ideas, sequence-analysis-research, model-benchmarks |

## Classification Rule

- A module is **core** if it can run and produce domain analysis without UI or transport dependencies.
- A module is an **extension** if it adapts, exposes, visualizes, or operates core capabilities.

## Ownership Convention

- Each submodule must have one technical owner and one backup owner.
- Ownership metadata must be tracked in issue templates and roadmap items.
