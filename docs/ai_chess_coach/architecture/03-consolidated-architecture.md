# Consolidated Architecture

## Principle

LLM never decides. LLM only explains evidence.

## Evidence Sources

- Stockfish
- ML
- RAG
- validation rules

## Logical Flow

```mermaid
flowchart LR
A[PGN] --> B[Core Engine]
B --> C[ML and Heuristic Analysis]
B --> D[Orchestration Planner]
D --> E[Executor]
E --> F[Critic Validation]
F --> G[RAG Retrieval]
G --> H[LLM Explanation]
H --> I[Analysis Contract]
I --> J1[FastAPI Extension]
I --> J2[UI Extension]
I --> J3[Batch and External Consumers]
```

## Layered View

| Layer | Responsibility |
| --- | --- |
| core-analysis | deterministic analysis, model scoring, evidence generation |
| core-orchestration | execution order, safeguards, policy enforcement |
| core-contracts | stable domain outputs for any consumer |
| ext-api-fastapi | transport and client-facing API surface |
| ext-ui | rendering, interaction, and user workflows |
| ext-observability/ext-devops/ext-testing | operational and quality satellites |

## Architectural Constraint

- Extension modules can orchestrate input/output but must not mutate core evidence semantics.
- Core modules expose stable contracts and remain presentation-agnostic.
