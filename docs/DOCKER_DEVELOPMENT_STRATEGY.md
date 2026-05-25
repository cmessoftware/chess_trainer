# Docker Development Strategy

This document explains the intended Docker-based development workflow for ChessInsightAI and points to the implementation files that already exist.

## Primary repository references

| File | Status | Responsibility |
| --- | --- | --- |
| [`../docker-compose.yml`](../docker-compose.yml) | Existing | Service orchestration |
| [`../dockerfile`](../dockerfile) | Existing | Main application image |
| [`../dockerfile.notebooks`](../dockerfile.notebooks) | Existing | Notebook-oriented image |
| [`../build_up_clean_all.ps1`](../build_up_clean_all.ps1) | Existing | Windows-first automation entry point |
| [`../debug-entrypoint.sh`](../debug-entrypoint.sh) | Existing | Container startup/debug support |
| [`../quick-helpers.sh`](../quick-helpers.sh) | Existing | Shell helper workflow |
| [`../quick-helpers.ps1`](../quick-helpers.ps1) | Existing | PowerShell helper workflow |

## Strategy

The Docker setup is designed to keep analysis, dataset generation, and notebook work reproducible. The recommended development posture is:

1. build containers from versioned definitions;
2. mount project code and data consistently;
3. run database-backed or engine-backed workflows inside the same environment family;
4. keep notebooks isolated enough to avoid polluting the main application runtime.

## Why this matters for the project

ChessInsightAI mixes several concerns: PGN processing, Stockfish analysis, dataset generation, notebooks, and ML experimentation. Docker reduces local-environment drift when those concerns depend on different binaries or services.

## Future plan

- Document each compose service with its exact development role.
- Separate developer convenience containers from CI-oriented containers.
- Add explicit artifact and dataset volume ownership rules.
