# Phase 03 -  ChessTrainer — SHAP Explainability for Human Pattern Model (Course Spec)

> **Placement:** Module 06 (`06_shap_analysis.ipynb`)  
> **Module 05:** MLflow experiment tracking (unchanged, separate)  
> **Status:** v2 — aligned with Modules 02–04, `feature_engineering.py`, game-level splits  
> **Scope:** Phases 1–4 only. Pattern Engine / player profiles / coaching JSON → Module 08+

---

## 1. Context (Module 04 results)

| Model                            | Balanced Accuracy | Macro F1 |
| -------------------------------- | ----------------: | -------: |
| Proxy (engine + human + context) |            ~0.998 |   ~0.998 |
| Human Pattern (human + context)  |            ~0.470 |   ~0.411 |

**Conclusions:**

1. Engine features almost perfectly replay Stockfish labels.
2. Human/context features still carry meaningful signal (~41% macro-F1).
3. Explainability work targets the **Human Pattern** model only.
4. SHAP explains **model behavior**, not Stockfish ground truth.

---

## 2. Objective (Phases 1–4)

Build a reproducible explainability layer on the best **Human Pattern** tabular model:

| Phase | Deliverable                                                                   |
| ----- | ----------------------------------------------------------------------------- |
| **1** | Train/compare LightGBM (baseline), XGBoost, CatBoost on identical game splits |
| **2** | Global SHAP (summary + bar + `global_shap_importance_df`)                     |
| **3** | Per-class SHAP for `good`, `inaccuracy`, `mistake`, `blunder`                 |
| **4** | Local explanations: `explain_prediction(row)` + waterfall examples            |

**Out of scope (v1):** `pattern_engine.py`, `aggregate_player_patterns`, `build_explanation_context` → future modules.

---

## 3. Prerequisites

| Input           | Source                                                                |
| --------------- | --------------------------------------------------------------------- |
| Encoded dataset | `data/datasets/course_training_dataset.parquet` (Module 02)           |
| Feature set     | `resolve_model_feature_columns(..., feature_set='human')`             |
| Splits          | `split_by_game_id()` — same seed/ratios as Module 04 (`42`, 70/15/15) |
| Sanitization    | `split_features_and_target(..., sanitize_feature_names=True)`         |

### Human features (canonical)

**Numeric:** `player_elo`, `move_number`, `material_total`, `num_pieces`, `king_safety`, `center_control`, `self_mobility`, `opponent_mobility`, `branching_factor`, `has_castling_rights`, `is_pawn_endgame`

**Context (one-hot):** `opening_*`, `time_control_bucket_*`, `phase_*`

### Never use in Human Pattern / SHAP

```text
score_cp, score_diff, depth_score_diff, mate_in
```

Legacy fictional names (not in schema): `cp_loss`, `best_move_score`, `hanging_piece`, etc.

---

## 4. Phase 1 — Human Pattern model selection

Train on **train** split; compare on **validation**; refit best model on train+val before test/SHAP (optional) or use train-only model for SHAP on test sample.

| Model    | Role                                |
| -------- | ----------------------------------- |
| LightGBM | Baseline (same family as Module 04) |
| XGBoost  | Candidate                           |
| CatBoost | Candidate                           |

**Metrics:** balanced accuracy, macro-F1 (primary for selection among Human models).

**Persist artifacts** (`artifacts/module06/`):

```text
human_model.joblib          # best estimator
model_comparison.json       # metrics table
feature_columns.json        # human feature list (pre-sanitize names)
label_order.json
selected_model_name.txt
```

**Hyperparameters:** fixed across candidates for fair comparison (`n_estimators=200`, class balancing, `random_state=42`).

---

## 5. Phase 2 — Global SHAP

- Sample up to **5,000 rows** from **test split**, stratified by `game_id` (not row-random).
- Use `shap.TreeExplainer` on the selected tree model.
- Outputs:
  - `shap.summary_plot` (beeswarm)
  - `shap.plots.bar` (mean |SHAP|)
  - `global_shap_importance_df` with columns `feature`, `mean_abs_shap`
- **Opening grouping:** aggregate `opening_*` into `opening (grouped)` for ranked bar tables (329 dummies are not individually interpretable).

---

## 6. Phase 3 — Per-class SHAP

For each `error_label` class:

- Filter sample rows to that class (or use class-specific SHAP slice for multiclass).
- Summary plot + save `class_shap_results[label]` → `class_shap_importance_{label}.parquet`.

Student questions:

- What human factors associate with **blunders** vs **good** moves in the Human model?

---

## 7. Phase 4 — Local SHAP

```python
explain_prediction(row) -> {
    "predicted_label": str,
    "predicted_probabilities": dict,
    "top_positive_features": [{"feature": str, "impact": float}, ...],
    "top_negative_features": [...],
}
```

- Input row: single encoded dataframe row aligned with training columns.
- Optional `shap.waterfall_plot` for 3–5 random test examples.
- Document that impacts are **SHAP contributions for the predicted class**, not chess causality.

---

## 8. Design principles

1. **Stockfish** remains label source; ML does not replace it.
2. **Human Pattern** is the explainability model; Proxy is baseline only (Module 04).
3. **SHAP** = evidence; chess concepts translation → later Pattern Engine module.
4. Success = *can we explain why the Human model flagged this move?* not *can we replay Stockfish?*

---

## 9. Module boundaries

| Module | Responsibility                                      |
| ------ | --------------------------------------------------- |
| 04     | Proxy vs Human comparison (LightGBM)                |
| 05     | MLflow tracking                                     |
| **06** | **This spec — model selection + SHAP (phases 1–4)** |
| 08+    | Pattern engine, player memory, LLM coaching context |

---

## 10. Implementation artifacts

| Artifact | Location                                                                    |
| -------- | --------------------------------------------------------------------------- |
| Spec     | `ai_chess_coach_course_shap_human_pattern.md`                               |
| Notebook | `06_shap_analysis.ipynb`                                                    |
| Python   | `explainability/human_pattern_models.py`, `explainability/shap_analysis.py` |
| Tests    | `tests/docs_courses/test_shap_human_pattern.py`                             |

---

## 11. Document history

| Version | Change                                                                                               |
| ------- | ---------------------------------------------------------------------------------------------------- |
| v1      | Original prompt (phases 1–7, fictional features, implied Module 05)                                  |
| v2      | Module 06 placement; phases 1–4 only; real columns; XGB/CatBoost vs LightGBM; game-level SHAP sample |
