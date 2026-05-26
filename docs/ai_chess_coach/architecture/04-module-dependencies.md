# Module Dependency Document

## Domain Dependencies

```mermaid
graph TD
CA[core-analysis] --> CO[core-orchestration]
CA --> CK[core-knowledge]
CO --> CK
CK --> CC[core-contracts]
CC --> API[ext-api-fastapi]
CC --> UI[ext-ui]
CC --> BATCH[batch and external clients]
CO --> OBS[ext-observability]
API --> OBS
CO --> DEV[ext-devops]
CA --> TEST[ext-testing]
CO --> TEST
CK --> TEST
TEST --> RES[ext-research]
```

## Policy

- Higher-level domains cannot bypass critical validation in orchestration.
- RAG/LLM can consume evidence but cannot mutate engine truth.
- Testing dependencies are mandatory before phase closure.
- Extension layers must only depend on stable core contracts, never on core internal state.
