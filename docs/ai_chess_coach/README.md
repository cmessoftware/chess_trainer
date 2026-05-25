# AI Chess Coach - Technical Documentation

## Overview

This directory contains the active technical documentation for the **ChessInsightAI** AI Chess Coach project.

The documentation has been reorganized into domain-based sections so implementation, roadmap, testing, operations, observability, and research stay clearly separated.

## Documentation Structure

- [`architecture/`](architecture/) — high-level architecture, dependency maps, and migration guidance
- [`modules/`](modules/) — module taxonomy, labels, aliases, and implementation-domain references
- [`roadmap/`](roadmap/) — phased delivery planning and future work sequencing
- [`testing/`](testing/) — testing strategy and release quality gates
- [`devops/`](devops/) — delivery, deployment, rollback, and operational constraints
- [`observability/`](observability/) — metrics, logging, alerting, and traceability strategy
- [`research/`](research/) — research boundaries and experiment-to-production promotion rules

## OpenSpec Workflow

OpenSpec is managed from this directory (`docs/ai_chess_coach`).

Operational command convention:

```powershell
mamba run -n chess_trainer npx -y @fission-ai/openspec <command>
```

Examples:

```powershell
mamba run -n chess_trainer npx -y @fission-ai/openspec list
mamba run -n chess_trainer npx -y @fission-ai/openspec validate gestionar-specs-ai-chess-coach
mamba run -n chess_trainer npx -y @fission-ai/openspec show migrate-pgn-feature-specs --type change --no-interactive
```

Definition of Done for requirement changes:

- Every requirement change MUST be created as an OpenSpec change.
- Every change MUST include `proposal.md`, `design.md`, `specs/`, and `tasks.md`.
- `openspec validate <change-name>` MUST pass before implementation starts.
- No implementation should start without an active OpenSpec change.

## Recommended Reading

### Getting Started
1. [`architecture/03-consolidated-architecture.md`](architecture/03-consolidated-architecture.md) — consolidated system view and logical flow
2. [`architecture/01-folder-structure.md`](architecture/01-folder-structure.md) — target documentation tree and domain taxonomy
3. [`modules/01-module-taxonomy.md`](modules/01-module-taxonomy.md) — implementation domains and submodules

### Planning and Delivery
1. [`roadmap/01-phase-roadmap.md`](roadmap/01-phase-roadmap.md) — phased roadmap and exit criteria
2. [`testing/01-testing-strategy.md`](testing/01-testing-strategy.md) — test pyramid, mandatory gates, and release gates
3. [`devops/01-delivery-rules.md`](devops/01-delivery-rules.md) — deployment, rollback, and CI/CD requirements

### Architecture and Governance
1. [`architecture/04-module-dependencies.md`](architecture/04-module-dependencies.md) — dependency relationships between domains
2. [`modules/02-label-taxonomy.md`](modules/02-label-taxonomy.md) — issue label taxonomy
3. [`modules/03-technical-aliases.md`](modules/03-technical-aliases.md) — stable technical aliases and mandatory issue metadata
4. [`observability/01-observability-strategy.md`](observability/01-observability-strategy.md) — metrics and alerting strategy
5. [`research/01-research-boundary.md`](research/01-research-boundary.md) — separation between experimentation and production

## Core Architecture Principles

- **LLM never decides.**
- **LLM only explains grounded evidence.**
- Stockfish, ML, RAG, and validation rules are evidence sources with distinct responsibilities.
- Higher-level layers must not bypass orchestration safeguards.
- Research artifacts must remain isolated from production implementation documentation.

## Logical Flow

```text
PGN -> Core Engine -> ML Evaluation -> Orchestration Planner -> Executor -> Critic Validation -> RAG Retrieval -> LLM Explanation -> API/UI Report
```

## Implementation Domains

```text
01-core-engine
02-ml
03-orchestration
04-rag-llm
05-api
06-ui
07-observability
08-devops
09-testing
10-research
```

## Governance Rules

- Every module must map to roadmap phases and issue labels.
- Each submodule must have one technical owner and one backup owner.
- Every issue must include domain, type, priority, and status labels.
- Issues should also include alias, domain, phase, and owner where applicable.
- No phase is complete until testing, observability, and rollback criteria are satisfied.

## Migration Status

The documentation structure replaces older references under legacy paths.

For migration details, see:
- [`architecture/02-document-migration-plan.md`](architecture/02-document-migration-plan.md)

## Notes

- Legacy material under `obsoletes-specs` should be treated as reference-only.
- Active documentation should link only to the new structure under `docs/ai_chess_coach/`.
- New documents should include roadmap, testing, and rollback sections where applicable.
