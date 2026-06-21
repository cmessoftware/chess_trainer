# ChessTrainer — Human Chess Move Error Prediction

Public home for the **ChessTrainer** Kaggle dataset and competition materials.

Predict human move quality (`good`, `inaccuracy`, `mistake`, `blunder`) from **position and pattern features** — without engine evaluation columns such as `score_cp`.

---

## Kaggle

| Resource        | Link                                                                    |
| --------------- | ----------------------------------------------------------------------- |
| **Dataset**     | https://www.kaggle.com/datasets/cmessoftware/chesstrainer-kaggle-public |
| **Competition** | *Add your Kaggle competition URL when live*                             |

Download `train.csv`, `test.csv`, and `sample_submission.csv` from Kaggle.  
**Do not commit large CSVs to this repository** — Kaggle is the canonical data host.

---

## Task

Each row = **one human move**. Multiclass target:

```text
good | inaccuracy | mistake | blunder
```

**Evaluation:** Macro F1 (all four classes weighted equally).

**Recommended validation:** group by `game_id` using `id_game_map.csv` so moves from the same game stay in one fold.

---

## Dataset (release v1 — Option A)

| Split | Games |    Rows |
| ----- | ----: | ------: |
| Train | 4,425 | 223,664 |
| Test  | 1,107 |  55,436 |

- **7,783 games** selected from human games (Stockfish-only games excluded)
- **80/20 train/test split by game** (disjoint games)
- Engine-proxy features intentionally withheld

### Label distribution (train)

| Label      | Share |
| ---------- | ----: |
| good       | 45.4% |
| blunder    | 22.2% |
| mistake    | 20.4% |
| inaccuracy | 12.0% |

A strong **human-pattern** baseline is ~**0.40 macro-F1** without engine features.

---

## Features

| Group             | Columns                                                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Context           | `player_elo`, `elo_band`, `time_control_bucket`, `phase`, `opening`, `move_number`                                                   |
| Board             | `fen`, `move_san`, `material_total`, `material_balance`, `num_pieces`, `has_castling_rights`, `is_pawn_endgame`                      |
| Strategic proxies | `branching_factor`, `self_mobility`, `opponent_mobility`, `king_safety`, `center_control`, `is_low_mobility`, `is_center_controlled` |
| Tactical motifs   | `tactical_tag`, `tag_check`, `tag_fork`, `tag_pin`, `tag_discovered_attack`, `tag_mate`                                              |

See [`data_dictionary.md`](data_dictionary.md) for column definitions.

---

## Repository layout

```text
.
├── README.md
├── LICENSE
├── baseline_notebook.ipynb      # Starter model (Random Forest + GroupKFold)
├── data_dictionary.md
├── competition_description.md
├── kaggle_package/              # Export & enrichment tooling (optional)
├── export_competition_dataset.py
├── enrich_competition_tactics.py
└── pack_kaggle_upload.py
```

---

## Baseline

Open [`baseline_notebook.ipynb`](baseline_notebook.ipynb) on Kaggle (attach the dataset) or run locally after downloading CSVs.

The default baseline:

- **Random Forest** with `class_weight='balanced'`
- **StratifiedGroupKFold** by `game_id`
- Excludes high-cardinality text columns (`fen`, `move_san`) from the default feature matrix

---

## Reproducing the export (maintainers)

Requires Python 3.10+, `pandas`, `scikit-learn`, `python-chess`, and a local **course SQLite** snapshot with human games.

```bash
pip install pandas scikit-learn python-chess sqlalchemy

# 1. Tactical tags (competition games only, no Stockfish)
python enrich_competition_tactics.py --db-url /path/to/course_data.sqlite

# 2. Export CSVs
python export_competition_dataset.py --output ./output

# 3. Kaggle upload zips
python pack_kaggle_upload.py
```

Tactical tags use **board-pattern detection** (pin, fork, check, …) from FEN + move — not engine evaluation.

---

## Related projects

| Project                                                           | Role                                                                                    |
| ----------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| [ChessInsight AI](https://github.com/cmessoftware/chessinsightai) | Full application (in development) — ML pipeline, API, coaching                          |
| **AI Chess Coach course**                                         | Separate public repo planned when the course is finalized (SQLite-first, no PostgreSQL) |

This repository is the **standalone public face** for the Kaggle competition. It is decoupled from the production PostgreSQL stack.

---

## License

**Apache License 2.0** — see [LICENSE](LICENSE).

Game PGNs may originate from multiple sources; this dataset publishes **derived features and labels** for research and educational use. Review source terms if you redistribute raw games.

---

## Citation

If you use this dataset or competition, please cite:

```bibtex
@misc{chesstrainer2026,
  title        = {ChessTrainer: Human Chess Move Error Prediction},
  author       = {ChessInsight AI / ChessTrainer},
  year         = {2026},
  howpublished = {Kaggle Dataset},
  url          = {https://github.com/cmessoftware/chesstrainer-kaggle}
}
```

Replace the repository URL with this repo once published. Update the Kaggle dataset URL in the table above.
