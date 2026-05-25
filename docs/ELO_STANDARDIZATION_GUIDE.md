# ELO Standardization Guide

This guide describes why rating normalization matters in ChessInsightAI and which modules currently implement that logic.

## Why ELO standardization matters

The repository works with games from multiple platforms. Ratings from Chess.com, Lichess, FIDE, and manually curated datasets are not always directly comparable. A standardization layer improves dataset quality and reduces misleading model signals.

## Existing implementation map

| Module | Status | Purpose |
| --- | --- | --- |
| [`../src/ml/elo_standardization.py`](../src/ml/elo_standardization.py) | Existing | Main rating normalization logic |
| [`../src/ml/complete_elo_standardization.py`](../src/ml/complete_elo_standardization.py) | Existing | Extended orchestration for the standardization workflow |
| [`../src/ml/update_pipeline_elo_standardization.py`](../src/ml/update_pipeline_elo_standardization.py) | Existing | Connects normalization into the broader pipeline |
| [`../test_elo_standardization.py`](../test_elo_standardization.py) | Existing | Root-level validation script |
| [`../tests/test_elo_standardization.py`](../tests/test_elo_standardization.py) | Existing | Test-suite coverage |
| Cross-platform benchmark package | Future plan | Could formalize conversion baselines and uncertainty ranges |

## Theoretical model

A strong rating standardization system should:

- detect invalid or out-of-range ratings;
- map platform-specific scales into a comparable domain;
- flag anomalies that need manual review;
- preserve provenance so downstream models know which normalization path was used.

## Project impact

Standardized ratings improve:

- player segmentation;
- feature consistency across datasets;
- training comparability between sources;
- recommendation quality for future coaching outputs.

## Known relationship to other modules

- `../src/modules/ml_preprocessing.py` can use normalized rating features.
- `../src/ml/run_datasets_analysis.py` benefits from comparable rating distributions.
- `../src/ml/chess_error_predictor.py` can consume rating-aware features more safely when rating scales are harmonized.
