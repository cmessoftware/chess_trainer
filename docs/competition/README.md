# Kaggle Competition Package (ChessTrainer)

Isolated tooling under `docs/competition/` — does **not** modify course notebooks or `docs/ai_chess_coach_course/dataset/`.

## Step 1 — Gap diagnosis (current)

Compare Kaggle **8-band elo quotas** (9,700 games, no Stockfish) against human games in course SQLite:

```powershell
python docs/competition/diagnose_kaggle_gaps.py `
  --json-out docs/competition/output/kaggle_gap_report.json
```

Default DB: `docs/ai_chess_coach_course/course_data.sqlite`

Exit code `0` = ≥95% of quota reachable; `1` = below target (review warnings).

## Latest run (your SQLite)

| Metric | Value |
|--------|------:|
| Human games available | 10,000 |
| Best-effort exportable | **7,783** (80.2% of 9,700) |
| Feature rows | 464,867 |

Main gaps: `1800-1999` (13%), `1600-1799` (55%), `2400+` (71%). Several bands would be **capped** (sample down).

See `output/kaggle_gap_report.json` for full detail.

## Step 2 — Tactical enrichment (competition games only)

Board-pattern tags (`pin`, `fork`, `check`, …) for the ~7,783 selected games — **no Stockfish**, uses FEN + move from SQLite:

```powershell
python docs/competition/enrich_competition_tactics.py
```

Resume-safe checkpoint: `output/tactical_enrichment_checkpoint.json`.

## Step 3 — Export (Option A: best-effort as-is)

```powershell
python docs/competition/export_competition_dataset.py `
  --output docs/competition/output
```

Produces `train.csv`, `test.csv`, `sample_submission.csv`, `solution.csv`, `id_game_map.csv`, `competition_description.md`, `data_dictionary.md`, and `export_report.json`.

| Metric | Value |
|--------|------:|
| Games selected | 7,783 (80.2% of 9,700 quota) |
| Train / test games | 4,425 / 1,107 (80/20 by `game_id`) |
| Train / test rows | 223,664 / 55,436 |

Main gaps: `1800-1999` (13%), `1600-1799` (55%), `2400+` (71%). Several bands are **capped** (sample down).

See `output/export_report.json` and `output/kaggle_gap_report.json` for full detail.

## Baseline notebook

```powershell
python docs/competition/_gen_baseline_nb.py
```

Creates `baseline_notebook.ipynb` — Random Forest + GroupKFold by `game_id`. Excludes `fen` / `move_san` from the default feature matrix.

## Kaggle upload bundles

```powershell
python docs/competition/pack_kaggle_upload.py
```

| Zip | Contents | Where to upload |
|-----|----------|-----------------|
| `output/chesstrainer_kaggle_public.zip` | train, test, sample_submission, id_game_map, docs | [Kaggle Dataset](https://www.kaggle.com/datasets) → attach to competition |
| `output/chesstrainer_kaggle_host_solution.zip` | solution.csv only | Competition admin → private answer key |

Then attach the dataset to your competition, set metric to **Macro F1**, and publish `baseline_notebook.ipynb` as a starter kernel.

## Alternatives (not chosen)

- **B** Relax Kaggle quotas in `kaggle_package/config.py`
- **C** Re-import from PG (outside this folder)
