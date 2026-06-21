# ChessTrainer — Feature Importance & Leakage Detection (Course Spec)

> **Scope:** documentation only (Module 03 / 04 design).  
> **Status:** v2 — aligned with notebooks `01`–`03`, `prepare_feature_frame`, and game-level splits.  
> **Supersedes:** `ai_chess_coach_leakege_detention.md` (typo filename; content replaced here).

---

## 1. Objective

Extend the AI Chess Coach course with a **reproducible workflow** to:

1. Understand which features discriminate `error_label` (`good`, `inaccuracy`, `mistake`, `blunder`).
2. Distinguish **Stockfish-proxy signal** from **human-pattern signal**.
3. Detect and document **target leakage** before training models in Module 04.
4. Produce educational tables and plots suitable for students.

This spec defines **what** each module must cover. Implementation lives in notebooks and shared Python helpers — not in PostgreSQL schema changes.

---

## 2. ChessTrainer modeling philosophy

Stockfish (or the configured engine) is the **ground-truth labeler**. Labels are not the training goal by themselves.

| Model family | Goal | Role in course |
|--------------|------|----------------|
| **Stockfish Proxy** | Predict `error_label` using engine-derived features | Baseline — “how well can we replay the labeling rule?” |
| **Human Pattern** | Explain *why* humans err using position/context features | Preferred for coaching — explainable, pedagogical |

**Human Pattern models should not rely on features that encode the same engine evaluation used to assign the label.**

Examples of human factors the course cares about:

- king safety, undeveloped pieces, hanging material  
- weak pawn structure, low mobility, poor coordination  
- time pressure context (`time_control_bucket`), strength context (`player_elo`)

---

## 3. Placement in the course pipeline

```
Module 01  run feature pipeline     → PostgreSQL features
Module 02  dataset builder         → prepare_feature_frame, encode, split by game_id, parquet
Module 03  feature analysis (EDA)  → THIS SPEC — sections 4–6 only (no model training)
Module 04  ML training             → THIS SPEC — section 7 (Proxy vs Human, game-level split)
Module 05+ explainability / MLflow   → builds on Module 04 outputs
```

### Module 03 (canonical notebook: `03_feature_analysis.ipynb`)

**Already required by openspec:**

- error distribution  
- error by ELO (`elo_band` / `player_elo`)  
- error by opening  
- centipawn-loss analysis (`score_cp` / `cp_loss_abs`)

**Added by this spec:**

- candidate feature inventory (engine vs human vs metadata)  
- numerical summaries and boxplots by class  
- mutual information ranking (exploratory only)  
- leakage risk table and narrative summary  
- **no** `train_test_split`, **no** Random Forest / XGBoost training

### Module 04 (canonical notebook: `04_ml_training.ipynb`)

**Added by this spec:**

- train **Proxy** and **Human Pattern** models on the **same** game-level splits  
- compare balanced accuracy / macro-F1  
- interpret performance gap as leakage / label-proxy signal vs genuine human signal

---

## 4. Canonical feature sets

Derived from `dataset/feature_engineering.py`, `dataset/build_training_dataset.py`, and the SQLite course export.

### 4.1 Target

| Column | Type | Notes |
|--------|------|--------|
| `error_label` | categorical | `good`, `inaccuracy`, `mistake`, `blunder` |

### 4.2 Stockfish Proxy features (engine / label pipeline)

Use for **baseline models only**. High predictive power here often means “replaying Stockfish’s rule,” not human explanation.

| Column | In DB today | Notes |
|--------|-------------|--------|
| `score_cp` | yes | Centipawn eval from player perspective; primary leakage suspect. In PG export, often aliased from `score_diff` (`features_repository`) |
| `score_diff` | yes | Raw engine score on the features row; same leakage class as `score_cp` |
| `depth_score_diff` | yes (often 0 in course export) | Engine depth delta when populated |
| `mate_in` | yes (placeholder 0 in course export) | Mate distance when populated |

**Not in schema (do not reference in course code):**  
`cp_loss`, `best_move_score`, `best_score_cp`, `played_score_cp`, `score_delta` — use `score_cp` / `score_diff` as proxies in EDA.

### 4.3 Human Pattern features (coaching models)

Preferred for Module 04 **Human Pattern** runs:

| Column | Notes |
|--------|--------|
| `player_elo` | Strength context; use instead of bare `elo` |
| `move_number` | Game phase proxy |
| `material_total`, `num_pieces` | Material / complexity |
| `king_safety` | Derived: mobility differential |
| `center_control` | Derived: branching factor proxy |
| `self_mobility`, `opponent_mobility`, `branching_factor` | Activity / tactics context |
| `has_castling_rights`, `is_pawn_endgame` | Structure flags |

### 4.4 Context features (encode for ML; also use in EDA)

| Column | Encoding in Module 02 |
|--------|------------------------|
| `opening` | one-hot (`opening_*`) |
| `time_control_bucket` | one-hot (`time_control_bucket_*`) |
| `phase` | categorical (opening / middlegame / endgame) — one-hot if used in ML |

### 4.5 Metadata only — never ML features

| Column | Purpose |
|--------|---------|
| `source` | Audit trail; exclude `stockfish` in `prepare_feature_frame` |
| `elo_band` | EDA and reporting bands (8 bins) |
| `skill_group`, `export_skill_group`, `skill_group_description` | Balanced import quotas / quality checks |
| `game_id`, `player_color` | Splitting and traceability (`move_number` is an ML feature, not metadata) |
| `white_elo`, `black_elo`, `time_control`, `white_player`, `black_player`, `result` | Reporting |

**Note:** Balancing is by **ELO / skill_group**, not by `source` (see `course_dataset_generation_guidelines.md`).

---

## 5. Leakage rules (ChessTrainer)

### 5.1 Label leakage

A feature is a **label-leakage suspect** if it is computed from (or is monotonic with) the engine evaluation used to assign `error_label`.

- **Suspects:** `score_cp`, `score_diff`, `depth_score_diff`, `mate_in`, and any future cp-threshold features.  
- **Expected EDA outcome:** these rank highest in MI / boxplot separation — that confirms label quality; it does **not** justify using them in Human Pattern models.

### 5.2 Split leakage

- **Forbidden:** row-level random split (`train_test_split` on moves).  
- **Required:** `split_by_game_id()` (Module 02) — all moves of a game stay in one fold.  
- Module 03 MI / summaries may use the full prepared frame; Module 04 must respect game splits.

### 5.3 Temporal leakage (future note)

If training on games ordered by `date_played`, document risk of future information. Current course parquet does not enforce temporal split; mention in Module 04 appendix.

### 5.4 What is not leakage

- `player_elo`, `time_control_bucket`, material and mobility **before** the labeled move  
- `opening`, `phase` as context  
- Metadata columns used only for filtering or reporting

---

## 6. Module 03 — EDA & leakage awareness (spec)

**Input:** `df_raw` from course DB or Module 02 parquet, passed through `prepare_feature_frame()`.

**Output:** student-facing tables/plots + a short “leakage memo” markdown cell.

### 6.1 Feature inventory cell

- Build lists: `ENGINE_PROXY_FEATURES`, `HUMAN_PATTERN_FEATURES`, `CONTEXT_FEATURES`, `METADATA_COLUMNS`.  
- Intersect with `df.columns`; print missing vs available.  
- Do not hard-code obsolete column names.

### 6.2 Numerical summary by `error_label`

- Group by target; aggregate mean / median / std for numeric human + engine columns.  
- Purpose: see which variables separate classes.

### 6.3 Boxplots by class

- One plot per numeric feature in `{engine} ∪ {human}` (subset for notebook runtime).  
- Order x-axis: `good`, `inaccuracy`, `mistake`, `blunder`.  
- Overlap with existing §7 (`cp_loss_abs`) is intentional — keep one centipawn view.

### 6.4 Mutual information (exploratory)

- One-hot encode categoricals (`opening`, `time_control_bucket`, `phase` if used).  
- `mutual_info_classif` on full encoded matrix; rank features.  
- Flag rows where feature name ∈ engine proxy set.  
- **Do not** use a fixed MI threshold as sole leakage test; use **feature set membership + ranking**.

### 6.5 Leakage risk table (markdown + code)

| Feature group | Example columns | Use in Proxy model | Use in Human model | EDA role |
|---------------|-----------------|--------------------|--------------------|----------|
| Engine | `score_cp`, … | yes | **no** | label-quality check |
| Human | `king_safety`, … | optional | **yes** | coaching signal |
| Context | `opening`, … | yes | yes | context |
| Metadata | `source`, `export_skill_group` | no | no | audit / balance |

Student takeaway:

> High MI for `score_cp` is expected. The question is whether the model still works when engine columns are removed.

### 6.6 Module 03 summary cell

Print top MI features, list engine suspects present, recommend Module 04 feature sets.  
**Do not train classifiers in Module 03.**

### 6.7 Coexistence with existing Module 03 sections

| Existing section | Action |
|------------------|--------|
| §4 Error distribution | keep |
| §5 Error by ELO | keep; prefer `player_elo` / `elo_band` |
| §6 Error by opening | keep |
| §7 Centipawn loss | keep; aligns with engine leakage discussion |
| §8 Next steps | point to Module 04 Proxy vs Human comparison |

---

## 7. Module 04 — Proxy vs Human comparison (spec)

**Prerequisites:** Module 02 parquet (or `build_training_dataset.py` output) with game-level splits saved.

### 7.1 Feature matrices

```text
X_proxy  = ENGINE_PROXY + HUMAN_PATTERN + CONTEXT (encoded)
X_human  = HUMAN_PATTERN + CONTEXT (encoded)
y        = error_label (encoded)
```

Use the **same** train/validation/test `game_id` sets from Module 02.

### 7.2 Models (minimum)

- One strong tabular model (e.g. Random Forest or LightGBM) per feature set.  
- Same hyperparameters per family for fair comparison.  
- Metrics: balanced accuracy, macro-F1, confusion matrix.

### 7.3 Interpretation guide for students

| Observation | Meaning |
|-------------|---------|
| Proxy ≫ Human accuracy | Most signal is engine-evaluation replay |
| Human still reasonable (e.g. macro-F1 clearly above chance) | Position/context explains errors |
| Human ≈ Proxy after removing engine cols | Engine cols were doing all the work |

Optional later: permutation importance with **grouped CV by `game_id`** (Module 05/06).

---

## 8. Integration with Modules 01–02

| Module | Relationship to this spec |
|--------|---------------------------|
| **01** | Produces PostgreSQL `features`; no schema changes required |
| **02** | Single source of truth: `prepare_feature_frame`, `encode_training_features`, `validate_dataset_quality`, `split_by_game_id` |
| **02** | Quality checks use `export_skill_group` for import balance (not `source` share) |
| **02** | Future optional enhancement (out of scope for spec v2): export `course_training_proxy.parquet` vs `course_training_human.parquet` |

Module 03 must **not** reimplement cleaning logic inline; always call `prepare_feature_frame`.

---

## 9. Openspec alignment

Update `implement-course-modules-03` when implementing Module 03 extensions:

**ADDED requirements (proposed):**

- Feature inventory (engine / human / metadata)  
- Mutual information ranking with engine features flagged  
- Leakage risk section (markdown + table)  
- Explicit statement: no classifier training in Module 03  

Module 04 openspec should reference dual feature sets and game-level evaluation.

---

## 10. Implementation constraints

- Keep notebook cells readable; prefer shared helpers in `dataset/` for repeated logic.  
- Do **not** modify PostgreSQL schema for this work.  
- Use `player_elo` for ML strength; `elo_band` for EDA and balance reporting.  
- Exclude metadata columns in `encode_training_features` (already enforced).  
- Document *why* leakage matters for coaching products, not only for leaderboard accuracy.  
- All derived fields (`player_elo`, `elo_band`, `time_control_bucket`, `skill_group`) come from `prepare_feature_frame` — do not persist new derived columns in PG.

---

## 11. Document history

| Version | Change |
|---------|--------|
| v1 | Original prompt-style notebook steps (`ai_chess_coach_leakege_detention.md`) |
| v2 | Split Module 03 vs 04; real column names; game-level split rule; dual feature sets; metadata/balance alignment |
