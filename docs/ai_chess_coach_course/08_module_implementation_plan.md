# Module 08 Implementation Plan — ChessInsight

## Objective

Implement **after Module 07** a layer that turns 07’s structured chess evidence into a **practical decision profile**: how hard the choice was, how unique/fragile/robust it was, and what can be trained — without repeating Stockfish analysis or inventing causes from a FEN.

```text
PGN
→ Module 07: positions, MultiPV, played-move comparison, diagnosis
→ Module 08: decision metrics
→ Module 08: auditable rules
→ Module 08: reason / training codes
→ Module 08: deterministic explanation
→ (later) LLM verbalization of 08 output only
→ HITL optional
```

**Last status update:** 2026-09-01.

### Current progress


| Area           | Status    | Notes                                                                                                                                |
| -------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Source spec    | 📄 Draft   | `ChessInsight_Modulo_08_Modelo_Decision_Practica.md` (Cursor prompt, not an implementation plan).                                    |
| Module 07 gate | ⬜ Blocked | 08 must not start until 07 first increment includes MultiPV + played-move comparison (F07-014/015/016/019) and abstention (F07-028). |
| This plan      | ✅ Written | Roadmap only. No 08 code.                                                                                                            |




### Naming (avoid collision)

The **course** OpenSpec change `implement-course-modules-08` is **LLM explanations** (`08_llm_explanation.ipynb`). This document is the **analysis product Module 08** (decision complexity / practical quality), stacked on **analysis Module 07**. Do not merge the two in the same package or notebook series without an explicit rename.

---



## Coherence with Module 07 and the suggested spec



### What is coherent

- Same layers as 07: evidence → metrics → inference → narrative → human confirmation.
- LLM does not decide chess; it may only verbalize structured output (aligns with F07-040/043).
- Player-side eval, mates, `UNKNOWN` / `NEEDS_REVIEW`, golden fixtures without live Stockfish, no FastAPI/Streamlit in the MVP.
- Suggested dataclasses match 07’s frozen DTO style (`engine_eval.py`, `criticality.py`).
- “Do not duplicate UCI” matches 07’s engine isolation.



### Gaps and conflicts (must resolve before coding)


| Topic                                  | Issue                                                                                                                                           | Decision for this plan                                                                                                                                                                                                            |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **07 is not a finished producer**      | Spec assumes critical positions, MultiPV, comparison, and structured diagnosis. Locally 07 is Done only through F07-012.                        | **Hard gate.** 08 consumes 07 contracts; it does not implement MultiPV.                                                                                                                                                           |
| **ONLY_MOVE**                          | F07-007 is a *criticality trigger*. Spec 08 `only_move` is a *metric + reason*.                                                                 | Keep both. 07 may fire `ONLY_MOVE`; 08 computes gap/count from the same MultiPV and may emit `ONLY_MOVE_REQUIRED`. One engine pass.                                                                                               |
| **Complexity**                         | F07-011 `COMPLEX_POSITION` vs 08 `LOW/MEDIUM/HIGH` profile.                                                                                     | 07 trigger = “this position is critical because it is complex”. 08 profile = “how hard was the *decision* given candidates/replies”. Different outputs; share MultiPV inputs.                                                     |
| **Explanation**                        | 07 F07-039 report vs 08 template renderer. Spec §2 example talks about the c-file and piece readiness — that is 07.4 diagnosis, not 08 metrics. | 08 renderer speaks **metrics and process codes**. Positional story only if 07 diagnosis is present in the payload. Never invent structure from FEN.                                                                               |
| **Cognitive codes**                    | F07-041 (`MISSED_THREAT`, …) vs 08 (`CRITICAL_REPLY_OMITTED`, `TACTICAL_RESOURCE_MISSED`).                                                      | 07 hypotheses stay labeled as hypotheses. 08 codes are rule outputs from metrics. Map later; do not duplicate detectors.                                                                                                          |
| **POV**                                | Spec §11: “side to move”. 07 F07-004: **analyzed player**.                                                                                      | For the analyzed player’s ply, STM = that player. All 08 metrics use **analyzed-player POV** (reuse `normalize_for_player`). Never White-POV raw scores.                                                                          |
| **Stability / fragility / robustness** | Need multi-depth and replies along the PV. 07 `analyze_ply` is single depth, no MultiPV.                                                        | Metrics 5–7 are **P1**. MVP returns `UNKNOWN` until 07 (or a thin 08 reader of 07 MultiPV JSON) exposes those fields.                                                                                                             |
| `player_confidence`                    | Correctly forbidden as inference.                                                                                                               | Same as 07.7: only HITL. Field stays `null`.                                                                                                                                                                                      |
| **Config**                             | Spec suggests YAML `module_08:`. Repo uses `.env` and Python constants.                                                                         | Start with a typed config object + defaults in code; YAML/env later. Version the config string on every assessment.                                                                                                               |
| **Training codes**                     | Spec has `training_recommendation_codes` but no catalog.                                                                                        | Add an explicit small catalog (F08-020) befo-********************************************************************************************************************************************************************re the renderer. |




### Suggested spec vs this plan

The Cursor prompt is a **good architecture brief**, not an implementable catalog: no feature IDs, no 07 gate, no overlap table, and it asks to implement immediately. This file is the 07-style roadmap. **Do not execute the prompt until the 07 gate is met.**

---



## Principles

- Implement one verifiable capability at a time.
- Consume Module 07 outputs; do not call Stockfish from 08.
- Keep evidence, metrics, rule inference, narrative, and HITL separate.
- Do not use the LLM to decide chess evaluations or causes.
- Missing data → `None` / `UNKNOWN` / `NEEDS_REVIEW`. Never fill gaps.
- Do not present centipawns as win probability.
- Do not start UI, API, RAG, or Lc0 in this module.
- Add golden cases with human justification (same test-case fields as 07 §3).

---



## 1. Module breakdown


| Submodule | Responsibility            | Deliverable                                                                 |
| --------- | ------------------------- | --------------------------------------------------------------------------- |
| 08.0      | 07 adapter                | Typed input from 07 (candidates, evals, played move, optional diagnosis)    |
| 08.1      | Decision metrics          | Gap, acceptable count, only-move, replies, fragility, robustness, stability |
| 08.2      | Complexity profile        | `LOW` / `MEDIUM` / `HIGH` / `UNKNOWN` plus component metrics                |
| 08.3      | Rule engine               | Reason codes + training codes + trace                                       |
| 08.4      | Diagnostic confidence     | Coverage-based `HIGH`/`MEDIUM`/`LOW`/`UNKNOWN`; never player confidence     |
| 08.5      | Deterministic explanation | Spanish templates: what / why hard / process / training                     |
| 08.6      | Golden + HITL             | Fixtures and optional review-pack fields                                    |
| 08.7      | LLM verbalization         | Later; same constraints as F07-040/043                                      |


---



## 2. Feature catalog



### Status legend


| Status        | Meaning                       |
| ------------- | ----------------------------- |
| ⬜ Todo        | Not started (default)         |
| 🟡 In Progress | Implementation underway       |
| 🧪 In Testing  | Implemented; under validation |
| ❌ Canceled    | Out of scope or superseded    |
| ✅ Done        | Completed and accepted        |




### 08.0 — Integration with Module 07


| ID      | Feature            | Input                              | Verifiable output                        | Real-PGN test                                 | Priority | Status | Comments                                  |
| ------- | ------------------ | ---------------------------------- | ---------------------------------------- | --------------------------------------------- | -------- | ------ | ----------------------------------------- |
| F08-001 | 07 payload adapter | 07 position+candidates JSON or DTO | `DecisionContext` with player-POV scores | Map one 07 fixture without calling UCI        | P0       | ⬜ Todo | Fail closed if MultiPV missing            |
| F08-002 | Partial evidence   | Incomplete 07 payload              | Explicit `None`/`UNKNOWN` per metric     | Drop PV replies; expect stability UNKNOWN     | P0       | ⬜ Todo |                                           |
| F08-003 | Config snapshot    | Thresholds                         | Versioned config id on assessment        | Change threshold; golden still records config | P0       | ⬜ Todo | Defaults from spec §11; not “chess truth” |




### 08.1 — Deterministic metrics (MVP)


| ID      | Feature                    | Input                                    | Verifiable output                         | Real-PGN test                    | Priority | Status | Comments                                 |
| ------- | -------------------------- | ---------------------------------------- | ----------------------------------------- | -------------------------------- | -------- | ------ | ---------------------------------------- |
| F08-004 | Best-move gap              | MultiPV player-POV                       | `best_move_gap_cp` + evidence             | Unique vs two-equal candidates   | P0       | ⬜ Todo |                                          |
| F08-005 | Acceptable candidate count | MultiPV + `acceptable_candidate_loss_cp` | Integer count                             | Threshold 50 cp; count changes   | P0       | ⬜ Todo | Threshold not hardcoded in domain ifs    |
| F08-006 | Only-move indicator        | Gap + count                              | `only_move` bool **and** numeric evidence | Single defense that holds eval   | P0       | ⬜ Todo | Complements F07-007; does not replace it |
| F08-007 | Played-move vs best        | 07 played-move eval (F07-015/019)        | Gap of played vs PV1, same POV            | Move not in MultiPV still scored | P0       | ⬜ Todo |                                          |




### 08.1 — Metrics requiring richer 07 data (P1)


| ID      | Feature                | Input                         | Verifiable output           | Real-PGN test                               | Priority | Status | Comments                     |
| ------- | ---------------------- | ----------------------------- | --------------------------- | ------------------------------------------- | -------- | ------ | ---------------------------- |
| F08-008 | Critical reply count   | Opponent replies on PV        | Count + which moves         | High-branching defense position             | P1       | ⬜ Todo | UNKNOWN if 07 has no replies |
| F08-009 | Continuation fragility | Only-moves along PV (N plies) | Immediate vs accumulated    | Sacrifice that needs a series of only-moves | P1       | ⬜ Todo | Cap `fragility_max_plies`    |
| F08-010 | Robustness             | Eval vs top opponent replies  | Score not equal to raw eval | Attractive but brittle line                 | P1       | ⬜ Todo |                              |
| F08-011 | Evaluation stability   | Same position, ≥2 depths      | Stability metric or UNKNOWN | Unstable eval fixture; no fake number       | P1       | ⬜ Todo | 07 must store depths first   |




### 08.2 — Complexity profile


| ID      | Feature                       | Input                              | Verifiable output                 | Real-PGN test                             | Priority | Status | Comments                       |
| ------- | ----------------------------- | ---------------------------------- | --------------------------------- | ----------------------------------------- | -------- | ------ | ------------------------------ |
| F08-012 | Complexity classification     | Configurable rules on 08.1 metrics | `LOW`/`MEDIUM`/`HIGH`/`UNKNOWN`   | Quiet vs tactical FEN pair                | P0       | ⬜ Todo | Keep component metrics visible |
| F08-013 | Fragility / robustness levels | F08-009/010                        | Separate `AssessmentLevel` fields | Fragile sacrifice vs solid simplification | P1       | ⬜ Todo | UNKNOWN until P1 metrics exist |




### 08.3 — Rule engine and taxonomies


| ID      | Feature                           | Input                  | Verifiable output                                                                                                                                                           | Real-PGN test                                     | Priority | Status | Comments                       |
| ------- | --------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | -------- | ------ | ------------------------------ |
| F08-014 | Reason codes (MVP)                | Metrics + rules        | `ONLY_MOVE_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `NEEDS_HUMAN_REVIEW`                                                                                                         | One code per fixture with rule id                 | P0       | ⬜ Todo |                                |
| F08-015 | Reason codes (extended)           | P1 metrics             | `CRITICAL_REPLY_OMITTED`, `HIGH_REPLY_BRANCHING`, `FRAGILE_CONTINUATION`, `LOW_ROBUSTNESS`, `UNSTABLE_EVALUATION`                                                           | See spec §7                                       | P1       | ⬜ Todo |                                |
| F08-016 | Reason codes (needs 07 diagnosis) | 07 diagnosis + metrics | `PREMATURE_SIMPLIFICATION`, `UNNECESSARY_COMPLEXITY`, `FAILED_FINAL_POSITION_EVALUATION`, `TACTICAL_RESOURCE_MISSED`, `OPPONENT_THREAT_MISREAD`, `BEST_MOVE_NOT_CONSIDERED` | Only if 07.4 present                              | P2       | ⬜ Todo | Do not infer from FEN          |
| F08-017 | Rule trace                        | Fired rules            | `rule_id`, inputs, config version                                                                                                                                           | Golden asserts trace, not only code               | P0       | ⬜ Todo |                                |
| F08-020 | Training recommendation codes     | Reason codes           | Small catalog (e.g. review checks/captures/threats)                                                                                                                         | Maps `CRITICAL_REPLY_OMITTED` → one training code | P1       | ⬜ Todo | Catalog missing in source spec |




### 08.4 — Diagnostic confidence


| ID      | Feature                | Input                           | Verifiable output                     | Real-PGN test                  | Priority | Status | Comments                         |
| ------- | ---------------------- | ------------------------------- | ------------------------------------- | ------------------------------ | -------- | ------ | -------------------------------- |
| F08-018 | Diagnostic confidence  | Coverage of PV, replies, depths | `HIGH`/`MEDIUM`/`LOW`/`UNKNOWN`       | Incomplete MultiPV → not HIGH  | P0       | ⬜ Todo | Never named as player confidence |
| F08-019 | Player confidence slot | HITL only                       | Always `null` unless 07.7 supplies it | Assert not inferred from clock | P0       | ⬜ Todo |                                  |




### 08.5 — Deterministic explanation


| ID      | Feature                | Input               | Verifiable output                                       | Real-PGN test                        | Priority | Status | Comments                  |
| ------- | ---------------------- | ------------------- | ------------------------------------------------------- | ------------------------------------ | -------- | ------ | ------------------------- |
| F08-021 | Template renderer (es) | Assessment + codes  | Four blocks: occurred / difficulty / process / training | Snapshot or structured string test   | P1       | ⬜ Todo | After F08-014             |
| F08-022 | No extra claims        | Renderer + evidence | Every sentence maps to a code or metric                 | Inject missing field; no invented PV | P1       | ⬜ Todo | Align with F07-043 spirit |




### 08.6 — Validation


| ID      | Feature                | Input                   | Verifiable output                 | Real-PGN test                          | Priority | Status | Comments              |
| ------- | ---------------------- | ----------------------- | --------------------------------- | -------------------------------------- | -------- | ------ | --------------------- |
| F08-023 | Golden set (8 classes) | Fixtures                | Spec §12 cases 1–7 + one full PGN | Listed in test-catalog                 | P0       | ⬜ Todo | Engine-free fixtures  |
| F08-024 | Live 07→08 PGN         | Real game after 07 gate | One end-to-end assessment         | `sample_game4.pgn` or later golden PGN | P1       | ⬜ Todo | Integration, not unit |
| F08-025 | Review-pack fields     | 08 assessment           | JSON block 07 can attach          | Export one position                    | P2       | ⬜ Todo | After F07-035         |




### 08.7 — Later LLM


| ID      | Feature           | Input        | Verifiable output                     | Real-PGN test                | Priority | Status | Comments                               |
| ------- | ----------------- | ------------ | ------------------------------------- | ---------------------------- | -------- | ------ | -------------------------------------- |
| F08-026 | LLM verbalization | 08 JSON only | Natural language, no new chess claims | Same critic rules as F07-043 | P3       | ⬜ Todo | After 07.8 if both exist, share critic |


---



## 3. Per-feature test format

Reuse Module 07 §3 fields. Add:


| Field               | Description                                    |
| ------------------- | ---------------------------------------------- |
| `module08_expected` | Metrics, levels, reason codes, `UNKNOWN` flags |
| `rule_ids`          | Rules that must fire                           |
| `config_version`    | Threshold bundle id                            |


---



## 4. Documentation structure (when implementing)

```text
docs/ai_chess_coach_course/
├── 08_module_implementation_plan.md    # this file
├── ChessInsight_Modulo_08_Modelo_Decision_Practica.md  # original brief
└── (later)
    analysis/decision_quality/          # suggested package; confirm at 07 gate
    tests/docs_courses/test_f08_*.py
```

Do not create `analysis/decision_quality/` until Phase 0 of implementation.

---



## 5. First implementable increment (after 07 gate)



### 07 gate (required)

- [ ] F07-013 ranking (or an explicit list of positions to score)
- [ ] F07-014 MultiPV=3
- [ ] F07-015 played move evaluated if absent from MultiPV
- [ ] F07-016 legal SAN/UCI
- [ ] F07-019 played vs candidates
- [ ] F07-028 abstention on thin evidence



### 08 increment goal

```text
07 candidate payload
→ best_move_gap + acceptable count + only_move
→ complexity LOW/MEDIUM/HIGH/UNKNOWN
→ ONLY_MOVE_REQUIRED | INSUFFICIENT_EVIDENCE
→ diagnostic_confidence
→ Spanish template (short)
```



### Included features

- [ ] F08-001 — 07 adapter
- [ ] F08-002 — Partial evidence
- [ ] F08-003 — Config snapshot
- [ ] F08-004 — Best-move gap
- [ ] F08-005 — Acceptable count
- [ ] F08-006 — Only-move indicator
- [ ] F08-007 — Played vs best
- [ ] F08-012 — Complexity classification
- [ ] F08-014 — MVP reason codes
- [ ] F08-017 — Rule trace
- [ ] F08-018 — Diagnostic confidence
- [ ] F08-019 — Player confidence stays null
- [ ] F08-023 — Golden cases 1, 2, 7 (only-move, equal candidates, insufficient evidence)



### Out of scope for the first 08 increment

- Fragility, robustness, multi-depth stability (UNKNOWN)
- Positional prose without 07 diagnosis
- LLM
- FastAPI / Streamlit
- Probability of human error / Elo-calibrated difficulty
- Course notebook 08 (LLM) unless explicitly scoped as a consumer

---



## 6. Implementation phases



### Phase 0 — Discovery (start of 08 work)

- [ ] Confirm 07 gate artifacts and real payload shape.
- [ ] Choose package path (course `analysis/` vs `src/`).
- [ ] List 07 fields present vs missing (replies, depths).
- [ ] Freeze MVP reason-code subset.

**Completion criterion:** a one-page integration map (07 DTO → 08 `DecisionContext`) with no invented fields.

### Phase 1 — Contracts

- [ ] `DecisionContext`, `DecisionMetrics`, `PracticalDecisionAssessment`, `MetricEvidence`.
- [ ] Serialization round-trip.
- [ ] Partial payload tests.



### Phase 2 — MVP metrics + rules

- [ ] F08-004–007, 012, 014, 017, 018.
- [ ] Unit tests without Stockfish.



### Phase 3 — P1 metrics

- [ ] F08-008–011, 013, 015, 020.
- [ ] UNKNOWN when 07 lacks replies/depths.



### Phase 4 — Explanation

- [ ] F08-021, F08-022.



### Phase 5 — Vertical slice

- [ ] F08-024 one real PGN through 07 then 08.
- [ ] Document limitations.



### Phase 6 — LLM (optional)

- [ ] F08-026 after 07.8 critic exists or a shared critic.

---



## 7. MVP acceptance criteria

- [ ] Consumes a real or fixture 07 candidate payload (no UCI inside 08).
- [ ] Distinguishes only-move, several acceptable moves, and insufficient evidence.
- [ ] Complexity level is reproducible and shows component metrics.
- [ ] `diagnostic_confidence` ≠ player confidence (`player_confidence` is null unless HITL).
- [ ] Reason codes are stable strings with rule traces.
- [ ] Deterministic Spanish explanation without new chess claims.
- [ ] At least one full PGN path 07→08 (after gate).
- [ ] Unit + contract + golden tests; live engine tests remain in 07.
- [ ] Config version recorded on each assessment.

---



## 8. Priority order

```text
P0 (after 07 gate)
1. Adapter + UNKNOWN
2. Gap / acceptable count / only-move / played vs best
3. Complexity + diagnostic confidence
4. MVP reason codes + trace
5. Golden: only-move, equal candidates, thin evidence

P1
6. Critical replies, fragility, robustness, stability
7. Extended reason + training codes
8. Deterministic renderer
9. Real PGN 07→08

P2
10. Codes that need 07.4 diagnosis
11. Review-pack attachment

P3
12. LLM verbalization + critic
```

---



## 9. Decision on existing code

- **Do not** implement 08 inside `analysis/mental_model/` (disposable 07 prototype).
- **Do not** call `open_stockfish` from 08.
- **Reuse** `normalize_for_player` / player-POV units from 07; do not fork eval sign conventions.
- **Reuse** 07 test layout: `tests/docs_courses/test_f08_*.py`.
- Treat `ChessInsight_Modulo_08_Modelo_Decision_Practica.md` as the architecture brief; **this file** is the implementation authority.

