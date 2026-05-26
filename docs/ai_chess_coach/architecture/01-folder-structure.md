# ChessInsightAI Documentation Folder Structure

## Scope

This structure separates implementation, research, testing, and operations documentation.

## Target Tree

```text
docs/
├── architecture/
├── modules/
├── roadmap/
│   └── templates/
├── testing/
├── devops/
├── observability/
├── research/
├── ai_chess_coach/
├── ml_analysis/
└── sdd_engine/
```

## Domain Taxonomy (Implementation Domains)

```text
core-analysis
core-orchestration
core-knowledge
core-contracts
ext-api-fastapi
ext-ui
ext-observability
ext-devops
ext-testing
ext-research
```

## Design Rules

- LLM never decides.
- LLM only explains grounded evidence.
- Keep PoCs and notebooks out of production implementation docs.
- Every module must map to roadmap phases and issue labels.
