# Datasets Volumes Configuration

This document describes the theoretical storage model for datasets and related artifacts in ChessInsightAI.

## Why volume strategy matters

The repository works with PGN files, derived feature datasets, model outputs, notebook artifacts, and ML tracking data. A predictable storage layout helps preserve reproducibility and reduces accidental data loss.

## Relevant repository locations

| Location | Status | Role |
| --- | --- | --- |
| [`../datasets/`](../datasets/) | Existing | Dataset storage root |
| [`../mlartifacts/`](../mlartifacts/) | Existing | ML artifact storage |
| [`../mlruns/`](../mlruns/) | Existing | MLflow run outputs |
| [`../notebooks/`](../notebooks/) | Existing | Notebook workspace |
| [`../src/pipeline/`](../src/pipeline/) | Existing | Pipeline entry points that consume or generate datasets |
| [`../docker-compose.yml`](../docker-compose.yml) | Existing | Container-level volume configuration |
| Formal data retention policy | Future plan | Would define lifecycle and cleanup rules |

## Theoretical layout

A clean data strategy usually separates:

- **raw inputs** such as PGN archives and downloaded game files;
- **processed datasets** such as parquet or CSV feature tables;
- **experiment artifacts** such as models, plots, and MLflow outputs;
- **temporary workspace outputs** that can be regenerated.

## Relationship to current code

Scripts under `../src/scripts/` and `../src/pipeline/` already generate or consume dataset artifacts. The long-term benefit of documenting volumes is to make those scripts predictable across developer machines, CI, and notebook sessions.

## Future plan

- Define canonical mount points for raw, processed, and derived data.
- Add dataset version metadata.
- Clarify which generated outputs belong in Git, Git LFS, or external storage.
