# Cursor Prompt: Create a Kaggle Competition Package for ChessTrainer

## Context

I want to transform the current ChessTrainer Phase 1 dataset into a complete Kaggle-style machine learning competition.

The goal of the competition is to predict the chess move quality label:

```text
good
inaccuracy
mistake
blunder
```

using human-oriented chess features.

The competition should encourage participants to discover patterns behind human mistakes rather than reproduce Stockfish evaluations.

---

# Project Goal

Create all scripts, documentation, datasets, and exports required to publish a Kaggle competition named:

```text
ChessTrainer: Predict Chess Move Error Level
```

The competition package should be fully reproducible from the PostgreSQL database.

---

# Competition Objective

Participants receive a set of chess position features and must predict:

```python
error_label
```

Possible classes:

```text
good
inaccuracy
mistake
blunder
```

Evaluation metric:

```text
Macro F1 Score
```

---

# Dataset Design

Generate the following files:

```text
competition/
│
├── train.csv
├── test.csv
├── sample_submission.csv
├── solution.csv
├── data_dictionary.md
├── competition_description.md
├── baseline_notebook.ipynb
└── export_competition_dataset.py
```

---

# Dataset Generation Requirements

The dataset must be generated from the PostgreSQL database.

Use the existing ChessTrainer pipeline.

The export process must:

1. Load games and features.
2. Generate derived fields.
3. Apply balancing rules.
4. Split train/test.
5. Export CSV files.

---

# Derived Features

Generate:

```python
player_elo
elo_band
time_control_bucket
```

Player ELO:

```python
player_elo = (
    white_elo
    if player_color == 1
    else black_elo
)
```

---

# ELO Bands

```text
<1200
1200-1399
1400-1599
1600-1799
1800-1999
2000-2199
2200-2399
2400+
```

---

# Time Control Buckets

```python
if seconds < 180:
    bucket = "bullet"
elif seconds < 600:
    bucket = "blitz"
elif seconds < 1800:
    bucket = "rapid"
else:
    bucket = "classical"
```

---

# Dataset Balancing Strategy

Target approximately:

| ELO Band  | Games |
| --------- | ----: |
| <1200     |  1500 |
| 1200-1399 |  1500 |
| 1400-1599 |  1500 |
| 1600-1799 |  1500 |
| 1800-1999 |  1200 |
| 2000-2199 |  1000 |
| 2200-2399 |   800 |
| 2400+     |   700 |
| Stockfish |   300 |

Target:

```text
~10,000 games
```

Expected:

```text
300k - 500k feature rows
```

---

# Time Control Distribution

Target approximately:

```text
bullet      15%
blitz       40%
rapid       40%
classical    5%
```

---

# Leakage Prevention

The public dataset MUST NOT include engine-derived features that directly encode the labeling rule.

Exclude any available columns such as:

```text
score_cp
depth_score_diff
cp_loss
best_move_score
played_score_cp
score_delta
best_score_cp
```

If a column was used directly to create error_label, it must not appear in train.csv or test.csv.

These fields may remain available internally for dataset generation.

---

# Recommended Public Features

Include features such as:

```text
player_elo
elo_band
time_control_bucket
phase
move_number
material_total
num_pieces
has_castling_rights
is_pawn_endgame
branching_factor
self_mobility
opponent_mobility
```

Use the existing ChessTrainer feature set whenever possible.

---

# Train/Test Split

Very important:

Split by:

```text
game_id
```

Never split randomly by feature row.

A game must belong entirely to train or test.

This prevents data leakage between moves of the same game.

Recommended:

```text
80% train games
20% test games
```

---

# Exported Files

## train.csv

Contains:

```text
id
all public features
error_label
```

---

## test.csv

Contains:

```text
id
all public features
```

No target column.

---

## sample_submission.csv

Format:

```csv
id,error_label
1,good
2,good
3,good
```

---

## solution.csv

Contains:

```csv
id,error_label
...
```

Used only for Kaggle scoring.

---

# Competition Description

Generate a Markdown file:

```text
competition_description.md
```

including:

* competition overview
* objective
* evaluation metric
* dataset description
* leaderboard explanation
* rules
* citation requirements
* educational purpose

---

# Data Dictionary

Generate:

```text
data_dictionary.md
```

Document every column.

Include:

* feature name
* data type
* description
* allowed values

---

# Baseline Notebook

Generate:

```text
baseline_notebook.ipynb
```

The notebook should:

1. Load train.csv
2. Perform preprocessing
3. Encode categoricals
4. Train a Random Forest baseline
5. Evaluate using cross-validation
6. Create predictions for test.csv
7. Export:

```text
submission.csv
```

Use clean educational code and extensive comments in English.

---

# Validation

Before exporting:

Generate EDA reports verifying:

## Error Label Distribution

```python
error_label.value_counts(normalize=True)
```

---

## ELO Distribution

```python
elo_band.value_counts(normalize=True)
```

---

## Time Control Distribution

```python
time_control_bucket.value_counts(normalize=True)
```

---

## Leakage Scan

Automatically verify that forbidden columns are absent from:

```text
train.csv
test.csv
```

---

# Deliverables

Implement:

```text
export_competition_dataset.py
competition_description.md
data_dictionary.md
baseline_notebook.ipynb
sample_submission.csv template
```

Use the existing ChessTrainer architecture and SQLAlchemy-based data access layer whenever possible.

All code should be production-quality, fully typed where practical, and documented in English.
