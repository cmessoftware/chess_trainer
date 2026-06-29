# ChessTrainer — Human Chess Move Error Prediction

> Copy each section below into the matching field on the Kaggle competition page.

---

## Overview

Welcome to **ChessTrainer**!

Your task is to predict the **quality of a human chess move** from position and pattern features — **without** engine evaluation columns such as `score_cp`.

Each row represents **one human move** in a real game. Classify it into one of four move-quality labels:

```text
good | inaccuracy | mistake | blunder
```

This is a **multiclass classification** problem focused on **human mistake patterns**, not reproducing Stockfish evaluations. Engine-proxy features were intentionally withheld to prevent label leakage.

### Dataset highlights

| | Games | Rows |
|---|------:|-----:|
| **Train** | 4,425 | 223,664 |
| **Test** | 1,107 | 55,436 |

- **7,783 human games** total (Stockfish-only games excluded)
- **80/20 train/test split by game** — test games are disjoint from train
- **Random seed:** 42

The starter **Random Forest baseline** (`baseline_notebook.ipynb`) scores about **0.67–0.71 macro-F1** on the held-out test set (Public ~0.67, Private ~0.71). Cross-validation on train alone (OOF) is typically ~0.61 — useful for local tuning, not the leaderboard benchmark.

### Files

| File | Description |
|------|-------------|
| `train.csv` | Public features + target column `error_label` |
| `test.csv` | Public features only (no labels) |
| `sample_submission.csv` | Submission template |
| `id_game_map.csv` | Maps row `id` → `game_id` for game-level cross-validation |

---

## Evaluation

**Metric:** **Macro F1 Score** (multiclass)

Macro F1 averages the F1 score across all four classes with **equal weight**:

- `good`
- `inaccuracy`
- `mistake`
- `blunder`

**Why macro F1?**

- All error types matter equally (including the minority class `inaccuracy`)
- Well suited for **imbalanced** labels
- Treats labels as **nominal categories**, not an ordered scale

**Target type:** Multiclass classification (**nominal**). Although labels reflect increasing move severity in chess annotation, the competition evaluates them as independent categories.

### Label distribution (train)

| Label | Share |
|-------|------:|
| `good` | 45.4% |
| `blunder` | 22.2% |
| `mistake` | 20.4% |
| `inaccuracy` | 12.0% |

---

## Submission format

Submit a CSV with exactly **two columns**:

```csv
id,error_label
69,good
70,inaccuracy
71,mistake
72,blunder
```

### Rules

- One row per `id` in `test.csv`
- `error_label` must be a **lowercase string**, exactly one of:  
  `good`, `inaccuracy`, `mistake`, `blunder`
- **Do not submit numeric codes** (`0`, `1`, `2`, `3`) — use the string labels as in `train.csv`
- File must include a header row

See `sample_submission.csv` for the expected format.

---

## Dataset Description

### Overview

**ChessTrainer** is a tabular dataset for predicting **human chess move quality**. Each row represents **one move played by a human** in a real game.

The goal is to classify the move into one of four quality labels using **position, context, and pattern features** — **not** engine evaluation columns such as `score_cp` or `score_diff`.

This release is a **best-effort export (Option A)**: human games only (Stockfish-only games excluded), stratified by player strength, with an **80/20 train/test split by game**.

### Target variable

**Column:** `error_label`  
**Type:** Multiclass classification (**nominal** — not ordinal)  
**Classes (string labels):**

```text
good | inaccuracy | mistake | blunder
```

Submit predictions as **lowercase strings**, exactly as shown in `train.csv` (not numeric codes).

### Feature groups

Features are grouped into four blocks:

**1. Context** — player and game metadata  
`player_elo`, `elo_band`, `time_control_bucket`, `phase`, `opening`, `move_number`

**2. Board state** — position before the move  
`fen`, `move_san`, `material_total`, `material_balance`, `num_pieces`, `has_castling_rights`, `is_pawn_endgame`

**3. Human-pattern proxies** — strategic/tactical signals without engine eval  
`branching_factor`, `self_mobility`, `opponent_mobility`, `king_safety`, `center_control`, `is_low_mobility`, `is_center_controlled`

**4. Tactical motifs** — board-pattern detection (no Stockfish)  
`tactical_tag`, `tag_check`, `tag_fork`, `tag_pin`, `tag_discovered_attack`, `tag_mate`

### Data dictionary

| Column | Type | Description | Example / values |
|--------|------|-------------|------------------|
| `id` | int | Unique row identifier (one chess move) | `1 … N` |
| `player_elo` | int | ELO of the player who made the move | `600–3000` |
| `elo_band` | category | Player strength band from `player_elo` | `<1200`, `1200-1399`, …, `2400+` |
| `time_control_bucket` | category | Normalized time control | `bullet`, `blitz`, `rapid`, `classical` |
| `phase` | category | Game phase for the position | `opening`, `middlegame`, `endgame` |
| `opening` | string | Opening name from game metadata | free text (`unknown` if missing) |
| `move_number` | int | Full-move counter | `≥ 1` |
| `fen` | string | FEN of the position **before** the move | standard FEN |
| `move_san` | string | Move played in SAN notation | `Nf3`, `exd5`, … |
| `material_total` | float | Total material on the board | `≥ 0` |
| `material_balance` | float | Material balance (positive = side to move) | integer-ish |
| `num_pieces` | int | Piece count on the board | `≥ 0` |
| `has_castling_rights` | int | Castling rights remain | `0` or `1` |
| `is_pawn_endgame` | int | Pawn endgame flag | `0` or `1` |
| `branching_factor` | int | Legal move count (complexity proxy) | `≥ 0` |
| `self_mobility` | int | Mobility of side to move | `≥ 0` |
| `opponent_mobility` | int | Mobility of opponent | `≥ 0` |
| `king_safety` | int | King safety proxy (`self − opponent` mobility) | integer |
| `center_control` | int | Center control proxy | `≥ 0` |
| `is_low_mobility` | int | Low mobility flag for side to move | `0` or `1` |
| `is_center_controlled` | int | Center controlled flag | `0` or `1` |
| `tactical_tag` | category | Primary tactical motif for the move | `normal`, `check`, `fork`, `pin`, `discovered_attack`, `mate`, … |
| `tag_check` | int | Move gives check | `0` or `1` |
| `tag_fork` | int | Knight fork on major pieces | `0` or `1` |
| `tag_pin` | int | Move creates a pin | `0` or `1` |
| `tag_discovered_attack` | int | Discovered attack | `0` or `1` |
| `tag_mate` | int | Position is checkmate | `0` or `1` |
| `error_label` | category | **Train only.** Move quality label | `good`, `inaccuracy`, `mistake`, `blunder` |

### Intentionally excluded columns

To prevent **label leakage**, engine-derived features used to create labels are **not** published, including:

`score_cp`, `score_diff`, `depth_score_diff`, `mate_in`, `cp_loss`, and similar engine-evaluation fields.

Also excluded from public CSVs: `game_id` (use `id_game_map.csv` instead), player names, PGN, and raw `tags` JSON.

---

## Recommended approach

- **Validate by game**, not by row: join with `id_game_map.csv` and use `GroupKFold` or `StratifiedGroupKFold` on `game_id`
- **Local CV (OOF)** on train often scores lower than a model fit on the full train set evaluated on test (~0.61 OOF vs ~0.67–0.71 test for the starter baseline) — only test submissions count on the leaderboard
- **Class imbalance:** consider `class_weight='balanced'` or similar strategies
- **High-cardinality text:** `fen` and `move_san` are included for exploration; the starter baseline excludes them or engineers derived features
- **External data:** allowed if documented; the starter baseline uses only competition files

---

## Rules

1. **No engine-proxy features** — columns such as `score_cp` are not in the public files and must not be reconstructed from external engine runs for the purpose of bypassing the competition design.
2. **External datasets** are allowed if documented in your write-up.
3. This competition is for **research and educational use** — leaderboard scores reflect pattern-discovery progress, not engine replay accuracy.

---

## Citation

If you use this competition or dataset, please cite:

**ChessTrainer / ChessInsight AI**  
https://github.com/cmessoftware/chessinsightai/tree/main/docs/competition/publish

Starter baseline: use the pinned notebook on this competition’s **Code** tab (not the maintainer export folder).

```bibtex
@misc{chesstrainer2026,
  title        = {ChessTrainer: Human Chess Move Error Prediction},
  author       = {ChessInsight AI / ChessTrainer},
  year         = {2026},
  howpublished = {Kaggle Competition},
  url          = {https://github.com/cmessoftware/chessinsightai/tree/main/docs/competition/publish}
}
```

---

## Kaggle field mapping

| Kaggle section | Paste from |
|----------------|------------|
| **Overview** | [Overview](#overview) |
| **Evaluation** | [Evaluation](#evaluation) |
| **Submission** | [Submission format](#submission-format) |
| **Dataset Description** | [Dataset Description](#dataset-description) through [Intentionally excluded columns](#intentionally-excluded-columns) |
| **Rules / Citation** | [Rules](#rules) + [Citation](#citation) |
