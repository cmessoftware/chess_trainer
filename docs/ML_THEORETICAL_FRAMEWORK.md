# ML Theoretical Framework

This document summarizes the machine-learning concepts behind ChessInsightAI and connects them to current repository modules.

## Problem framing

ChessInsightAI transforms chess games into machine-learning-ready observations. A game can be represented as a sequence of moves plus engineered attributes such as opening information, tactical signals, engine evaluations, player ratings, and outcome context.

## Core ML tasks

| Task | Theory | Repository references | Status |
| --- | --- | --- | --- |
| Classification | Predict error labels, tactical categories, or recommendation buckets | [`../src/modules/predict_error_label.py`](../src/modules/predict_error_label.py), [`../src/ml/chess_error_predictor.py`](../src/ml/chess_error_predictor.py) | Existing |
| Feature engineering | Convert PGN and engine outputs into numeric inputs | [`../src/modules/feature_engineering.py`](../src/modules/feature_engineering.py), [`../src/modules/features_generator.py`](../src/modules/features_generator.py) | Existing |
| Preprocessing | Clean, normalize, and structure training data | [`../src/modules/ml_preprocessing.py`](../src/modules/ml_preprocessing.py) | Existing |
| Training | Fit models and compare experiments | [`../src/ml/train_error_model.py`](../src/ml/train_error_model.py) | Existing |
| Real-time inference | Apply trained models to new inputs | [`../src/ml/realtime_predictor.py`](../src/ml/realtime_predictor.py) | Partial |
| Explainability and coaching | Turn predictions into user-facing advice | `../src/ai_coach/` | Future-facing |

## Feature families

Typical features in this project include:

- move quality and engine score deltas;
- tactical motifs and tactical failure labels;
- opening or phase-of-game indicators;
- rating context and normalized player strength;
- aggregate game outcome signals.

## Why theory matters here

A strong theoretical framework keeps the data pipeline aligned with the user-facing goal: helping players understand mistakes, train more effectively, and eventually receive coaching-style recommendations.
