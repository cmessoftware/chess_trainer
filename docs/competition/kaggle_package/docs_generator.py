"""Generate competition markdown documentation."""

from __future__ import annotations

from pathlib import Path

from kaggle_package.config import (
    PUBLIC_FEATURE_COLUMNS,
    TARGET_CLASSES,
    TARGET_COLUMN,
)
from kaggle_package.gap_report import KaggleGapReport


def write_competition_description(
    path: Path,
    *,
    gap_report: KaggleGapReport,
    train_games: int,
    test_games: int,
    train_rows: int,
    test_rows: int,
) -> None:
    content = f"""# ChessTrainer: Predict Chess Move Error Level

## Overview

Welcome to the **ChessTrainer** Kaggle competition. You will predict human move quality labels using
**position, tactical, and strategic features** — **not** engine evaluation columns (`score_cp`, etc.).

Each row is one human move. Features fall into three groups:

1. **Context** — `player_elo`, `elo_band`, `time_control_bucket`, `phase`, `opening`, `move_number`
2. **Board state** — `fen`, `move_san`, `material_total`, `material_balance`, `num_pieces`,
   `has_castling_rights`, `is_pawn_endgame`
3. **Human-pattern proxies** — mobility, king safety, center control, branching factor,
   `is_low_mobility`, `is_center_controlled`
4. **Tactical motifs** — `tactical_tag` plus one-hot flags (`tag_pin`, `tag_fork`, `tag_check`,
   `tag_discovered_attack`, `tag_mate`) from board-pattern detection on each move (no engine eval)

## Objective

Predict `{TARGET_COLUMN}` for each chess move:

```text
{' | '.join(TARGET_CLASSES)}
```

## Evaluation

**Macro F1 Score** (multiclass, all four labels weighted equally).

## Dataset size (this release — Option A)

| Split | Games | Rows |
|-------|------:|-----:|
| Train | {train_games:,} | {train_rows:,} |
| Test  | {test_games:,} | {test_rows:,} |

**Best-effort export:** {gap_report.total_exportable:,} games selected from SQLite
({gap_report.completion_ratio:.1%} of the 9,700-game Kaggle quota target). Bands with fewer available
games are included in full; surplus bands are randomly down-sampled to quota.

## Files

| File | Description |
|------|-------------|
| `train.csv` | Public features + `{TARGET_COLUMN}` |
| `test.csv` | Public features only |
| `sample_submission.csv` | `{TARGET_COLUMN}` placeholder per `id` |
| `solution.csv` | Private labels for test rows (host only) |

## Rules

1. **No engine-proxy features** — columns such as `score_cp` are intentionally withheld.
2. Split-aware modeling is recommended: all moves from a game should stay in train or test (Kaggle test
   games are disjoint from train).
3. External datasets are allowed if documented; the baseline uses only competition files.
4. Educational use: the goal is to explain **human mistake patterns**, not reproduce Stockfish.

## Citation

If you use this dataset, cite the **ChessTrainer / ChessInsight AI** project and link to the repository.

## Educational purpose

High macro-F1 without engine features is difficult (~0.4 is a strong human-pattern baseline). Treat
leaderboard scores as pattern-discovery progress, not engine replay accuracy.
"""
    path.write_text(content, encoding="utf-8")


def write_data_dictionary(path: Path) -> None:
    rows = [
        ("id", "int", "Unique row identifier (one chess move).", "1 … N"),
        ("player_elo", "int", "ELO of the player who made the move.", "600–3000"),
        ("elo_band", "category", "Player strength band derived from player_elo.", "<1200, 1200-1399, …, 2400+"),
        ("time_control_bucket", "category", "Normalized time control.", "bullet, blitz, rapid, classical"),
        ("phase", "category", "Game phase for the position.", "opening, middlegame, endgame"),
        ("opening", "string", "Opening name from the game metadata.", "free text"),
        ("move_number", "int", "Full-move counter.", "≥ 1"),
        ("fen", "string", "FEN of the position before the move.", "standard FEN"),
        ("move_san", "string", "Move played in SAN notation.", "e.g. Nf3, exd5"),
        ("material_total", "float", "Total material on the board.", "≥ 0"),
        ("material_balance", "float", "Material balance (positive = advantage for side to move).", "integer-ish"),
        ("num_pieces", "int", "Piece count.", "≥ 0"),
        ("has_castling_rights", "int", "1 if castling rights remain.", "0 or 1"),
        ("is_pawn_endgame", "int", "1 if pawn endgame.", "0 or 1"),
        ("branching_factor", "int", "Legal move count (complexity proxy).", "≥ 0"),
        ("self_mobility", "int", "Mobility of side to move.", "≥ 0"),
        ("opponent_mobility", "int", "Mobility of opponent.", "≥ 0"),
        ("king_safety", "int", "King safety (self − opponent mobility).", "integer"),
        ("center_control", "int", "Center control proxy (branching-based).", "≥ 0"),
        ("is_low_mobility", "int", "1 if side to move has low mobility.", "0 or 1"),
        ("is_center_controlled", "int", "1 if center squares are controlled.", "0 or 1"),
        ("tactical_tag", "category", "Primary tactical motif for the move.", "normal, check, fork, pin, …"),
        ("tag_check", "int", "1 if the move gives check.", "0 or 1"),
        ("tag_fork", "int", "1 if the move is a knight fork on major pieces.", "0 or 1"),
        ("tag_pin", "int", "1 if the move creates a pin.", "0 or 1"),
        ("tag_discovered_attack", "int", "1 if the move is a discovered attack.", "0 or 1"),
        ("tag_mate", "int", "1 if the position is checkmate.", "0 or 1"),
        (TARGET_COLUMN, "category", "Move quality label (train only).", ", ".join(TARGET_CLASSES)),
    ]
    lines = [
        "# Data Dictionary — ChessTrainer Kaggle Competition",
        "",
        "| Column | Type | Description | Values |",
        "|--------|------|-------------|--------|",
    ]
    for name, dtype, desc, values in rows:
        lines.append(f"| {name} | {dtype} | {desc} | {values} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
