# ChessTrainer Course Dataset Generation Guidelines

## Objective

Generate a training dataset for the AI Chess Coach course that is:

* Representative of human chess errors.
* Balanced across player strengths.
* Balanced across time controls.
* Small enough to be distributed in a public repository.
* Large enough to train and evaluate classical machine learning models.

The dataset should prioritize educational value over raw volume.
<!-- @import "[TOC]" {cmd="toc" depthFrom=1 depthTo=6 orderedList=false} -->

The dataset must be created an isolated sqllite db.

---

# Data Source Principles

The `source` field (`novice`, `elite`, `fide`, `stockfish`) is considered metadata only.

It should NOT be used as a machine learning feature.

The relevant variables are:

* `player_elo`
* `time_control_bucket`
* chess features extracted from the position

The dataset generation process should derive all balancing decisions from ELO and time control rather than source labels.

---

# Player ELO

## Derivation

```python
player_elo = (
    white_elo if player_color == 1
    else black_elo
)
```

Rows with invalid or missing ELO values should be excluded.

Recommended valid range:

```text
600 <= player_elo <= 3000
```

---

# ELO Bands

Generate the following derived feature:

```python
elo_band
```

Using:

| Band      | Range     |
| --------- | --------- |
| <1200     | 600-1199  |
| 1200-1399 | 1200-1399 |
| 1400-1599 | 1400-1599 |
| 1600-1799 | 1600-1799 |
| 1800-1999 | 1800-1999 |
| 2000-2199 | 2000-2199 |
| 2200-2399 | 2200-2399 |
| 2400+     | 2400+     |

---

# Time Control Normalization

Convert all time controls into total base seconds.

Examples:

| Original | Seconds |
| -------- | ------: |
| 60+0     |      60 |
| 180+0    |     180 |
| 300+0    |     300 |
| 600+5    |     600 |
| 900+10   |     900 |
| 1800+0   |    1800 |
| 7200+60  |    7200 |

Ignore correspondence games and malformed values.

Examples to exclude:

```text
1 day per move
14 days per move
1/604800
1/1209600
-
```

---

# Time Control Buckets

Generate the derived feature:

```python
time_control_bucket
```

Using:

| Bucket    | Range (seconds) |
| --------- | --------------: |
| bullet    |           < 180 |
| blitz     |         180-599 |
| rapid     |        600-1799 |
| classical |         >= 1800 |

Implementation:

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

# Target Dataset Size

Target:

```text
10,000 games
```

This should produce approximately:

```text
350,000 - 450,000 feature rows
```

before optional sampling.

---

# Recommended ELO Distribution

Balance the dataset by player strength rather than source.

| ELO Band  | Games |
| --------- | ----: |
| <1200     | 1,500 |
| 1200-1399 | 1,500 |
| 1400-1599 | 1,500 |
| 1600-1799 | 1,500 |
| 1800-1999 | 1,200 |
| 2000-2199 | 1,000 |
| 2200-2399 |   800 |
| 2400+     |   700 |
| Stockfish |   300 |

Total:

```text
10,000 games
```

---

# Recommended Time Control Distribution

Aim for:

| Bucket    | Target |
| --------- | -----: |
| bullet    |    15% |
| blitz     |    40% |
| rapid     |    40% |
| classical |     5% |

Reasoning:

* Blitz and rapid represent the majority of online human chess.
* Bullet introduces realistic tactical mistakes.
* Classical positions provide deeper strategic examples.
* Overrepresentation of classical games may distort the behavior of amateur players.

---

# Machine Learning Features

Persist in database:

```text
white_elo
black_elo
player_color
time_control
```

Generate during dataset creation:

```text
player_elo
elo_band
time_control_bucket
```

Use for training:

```text
player_elo
time_control_bucket
existing chess features
```

Use for reporting and balancing:

```text
elo_band
time_control_bucket
source
```

---

# Quality Checks

Before exporting the final dataset verify:

1. Skill group / ELO distribution matches the target quotas (balanced import).
2. Time control distribution is reviewed (informational warnings only).
3. `source` is metadata for traceability only — not a balancing dimension.
4. Error labels remain reasonably balanced.
5. Good moves remain below approximately 55% of total samples.
6. Blunders remain above approximately 8% of total samples.
7. All ELO and time control derived fields are generated dynamically rather than persisted.
