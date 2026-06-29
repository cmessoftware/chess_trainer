# ChessTrainer: Predict Chess Move Error Level

## Overview

Welcome to the **ChessTrainer** Kaggle competition. You will predict human move quality labels using
**position, tactical, and strategic features** — **not** engine evaluation columns (`score_cp`, etc.).

Each row is one human move. Features fall into four groups:

1. **Context** — `player_elo`, `elo_band`, `time_control_bucket`, `phase`, `opening`, `move_number`
2. **Board state** — `fen`, `move_san`, `material_total`, `material_balance`, `num_pieces`,
   `has_castling_rights`, `is_pawn_endgame`
3. **Human-pattern proxies** — mobility, king safety, center control, branching factor,
   `is_low_mobility`, `is_center_controlled`
4. **Tactical motifs** — `tactical_tag` plus one-hot flags (`tag_pin`, `tag_fork`, `tag_check`,
   `tag_discovered_attack`, `tag_mate`) from board-pattern detection on each move (no engine eval)

## Objective

Predict `error_label` for each chess move:

```text
good | inaccuracy | mistake | blunder
```

Submit **lowercase string labels** (not numeric codes).

## Evaluation

**Macro F1 Score** (multiclass, all four labels weighted equally).

## Dataset size (this release — Option A)

| Split | Games |    Rows |
| ----- | ----: | ------: |
| Train | 4,425 | 223,664 |
| Test  | 1,107 |  55,436 |

**Best-effort export:** 7,783 games selected from SQLite
(80.2% of the 9,700-game Kaggle quota target). Bands with fewer available
games are included in full; surplus bands are randomly down-sampled to quota.

## Files

| File                    | Description                              |
| ----------------------- | ---------------------------------------- |
| `train.csv`             | Public features + `error_label`          |
| `test.csv`              | Public features only                     |
| `sample_submission.csv` | `error_label` placeholder per `id`       |
<<<<<<< HEAD
| `id_game_map.csv`       | Maps row `id` → `game_id` for GroupKFold |
| `solution.csv`          | Host only — not in the public download   |
=======
| `solution.csv`          | Private labels for test rows (host only) |
>>>>>>> 3db5739caea16165bf20933d520e21e371a952c2

## Rules

1. **No engine-proxy features** — columns such as `score_cp` are intentionally withheld.
2. Split-aware modeling is recommended: all moves from a game should stay in train or test (Kaggle test
   games are disjoint from train).
3. External datasets are allowed if documented; the baseline uses only competition files.
4. Educational use: the goal is to explain **human mistake patterns**, not reproduce Stockfish.

## Citation

If you use this dataset, cite **ChessTrainer / ChessInsight AI**:

https://github.com/cmessoftware/chessinsightai/tree/main/docs/competition/publish

<<<<<<< HEAD
Documentation and competition overview live in that folder.
=======
Documentation and competition overview live in that folder. **Do not** link to `docs/competition/output/` (maintainer artifacts).
>>>>>>> 3db5739caea16165bf20933d520e21e371a952c2

## Benchmark

The starter **Random Forest baseline** (`baseline_notebook.ipynb`) scores about **0.67–0.71 macro-F1**
on the held-out test set (Public ~0.67, Private ~0.71). Cross-validation on train alone (OOF) is
typically lower (~0.61 with 3-fold GroupKFold) and is for local tuning only — not the leaderboard
reference score.

Leaderboard scores reflect pattern-based move quality, not engine replay accuracy.
