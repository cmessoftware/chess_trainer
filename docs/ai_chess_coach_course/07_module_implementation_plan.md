# Module 07 Implementation Plan — ChessInsight

## Objective

Implement and validate progressively the following flow:

```text
PGN
→ critical positions
→ candidate moves
→ comparison with the played move
→ structured diagnosis
→ human validation
→ longitudinal patterns
→ pedagogical explanation
```

The current code in `analysis/mental_model/` is considered a disposable prototype. It may be modified or replaced entirely.

**Last status update:** 2026-09-01.

### Current progress

| Area | Status | Notes |
|---|---|---|
| 07.0 Game import (F07-001) | ✅ Done | PGN text, PGN file, and course DB → `NormalizedGame` / `PlyRecord`. Tests: `tests/docs_courses/test_f07_001_game_import.py`. Lab Paso 1. |
| Product ingest (feeds 07.0 DB path) | ✅ Done | `src/modules/player_ingest.py` + `src/scripts/player_ingest.py` (Chess.com / Lichess → PostgreSQL `games` + features, with ingest report). Not a Module 07 analysis feature. |
| 07.0 Player selection (F07-002) | ✅ Done | `select_analyzed_player` / `NormalizedGame.select_player`; tests White and Black. |
| 07.0 Stockfish (F07-003) | ✅ Done | `analyze_ply`; lab Paso 3; interactive board + `ChessinsightBoard.jsx`. |
| 07.0 Eval normalization (F07-004) | ✅ Done | `normalize_for_player` / `analyze_ply_for_player`; White/Black + mate flip. |
| 07.0 Evaluation loss (F07-005) | ✅ Done | `evaluation_loss` / `ply_evaluation_loss`; Scholar `3...Nf6`. |
| 07.1 Significant loss (F07-006) | ✅ Done | `EVALUATION_DROP` at 150 cp; Scholar `Nf6` vs Ruy `a6`. |
| 07.1 Criticality score (F07-012) | ✅ Done | 0–10 + Routine/Relevant/Critical/HighlyCritical from `EVALUATION_DROP`. |
| 07.1 Position ranking (F07-013) | ✅ Done | Top N by `criticality_score`; Scholar `Nf6` rank 1. |
| 07.2 MultiPV (F07-014) | ✅ Done | `analyze_multipv`; 3 lines + PV + player-POV eval. |
| 07.2 Played-move eval (F07-015) | ✅ Done | Rank in MultiPV or independent `root_moves` analysis. |
| 07.2 UCI/SAN (F07-016) | ✅ Done | `analysis/notation.py`; Scholar all-plies roundtrip. |
| 07.3 Played vs candidates (F07-019) | ✅ Done | Eval gap, D1–D5 purpose proxy, one-ply consequence. |
| 07.4 Abstention (F07-028) | ✅ Done | `UNKNOWN` / `NEEDS_REVIEW` / `NONE`; startpos vs Scholar `Nf6`. |
| 07.7 Review pack (F07-035) | ✅ Done | JSON FEN/PGN/candidates/evidence; `PENDING_REVIEW` until HITL. |
| 07.1 Only move (F07-007) | ✅ Done | `ONLY_MOVE` from sole legal move or MultiPV gap ≥150. |
| 07.1 Character change (F07-008) | ✅ Done | `POSITION_TRANSFORMATION`: pawn break / shield drop / opposite castling. |
| 07.1 Immediate threat (F07-009) | ⬜ Todo | Next P1 (lowest remaining ID). |
| 07.1–07.8 | ⬜ Todo | Remaining 07.1+ features not started. |

## Principles

- Implement one verifiable capability at a time.
- Test each feature with real games in PGN format.
- Keep evidence, inference, and human confirmation separate.
- Do not use the LLM to decide chess evaluations.
- Use structured contracts before generating textual explanations.
- Do not advance to UI, API, RAG, or Lc0 until the core is validated.
- Add validated real cases to the golden dataset.

## 1. Module breakdown

| Submodule | Responsibility | Deliverable |
|---|---|---|
| 07.0 | Analysis infrastructure | PGN converted into positions and Stockfish analysis |
| 07.1 | Critical positions | Prioritized list of critical positions |
| 07.2 | Candidate moves | MultiPV and candidate classification |
| 07.3 | Decision evaluation | Comparison between the played move and candidates |
| 07.4 | Chess diagnosis | Decision type and probable cause of the error |
| 07.5 | Suboptimal sequences | Grouping of related decisions |
| 07.6 | Player patterns | Trends across multiple games |
| 07.7 | Human validation | Confirmation, correction, or rejection of the diagnosis |
| 07.8 | Pedagogical explanation | Deterministic report and LLM verbalization |

## 2. Feature catalog

### Status legend (submodules 07.0–07.8)

| Status | Meaning |
|---|---|
| ⬜ Todo | Not started (default) |
| 🟡 In Progress | Implementation underway |
| 🧪 In Testing | Implemented; under validation |
| ❌ Canceled | Out of scope or superseded |
| ✅ Done | Completed and accepted |

### 07.0 — PGN and analysis infrastructure

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-001 | Game import | PGN file or text | Normalized game with moves, FEN, and metadata | Reconstruct all positions from an own game | P0 | ✅ Done | `analysis/game_models.py`, `analysis/position_extractor.py` (`import_game_from_pgn`, `import_game_from_file`, `load_game_from_db`); lab Paso 1; `tests/docs_courses/test_f07_001_game_import.py`. Product data: `src/scripts/player_ingest.py`. |
| F07-002 | Player selection | PGN and username or color | Moves attributable to the analyzed player | Test one game as White and one as Black | P0 | ✅ Done | `select_analyzed_player` in `analysis/game_models.py`; `tests/docs_courses/test_f07_002_player_selection.py`; lab Paso 1b |
| F07-003 | Stockfish analysis per position | FEN | Evaluation before and after the move | Compare with a Lichess-analyzed game | P0 | ✅ Done | `analyze_ply` in `analysis/engine_eval.py`; tests + lab Paso 3; Jupyter Windows Proactor loop |
| F07-004 | Evaluation normalization | Engine score | Evaluation from the player's perspective | Test turn changes and mate scores | P0 | ✅ Done | `normalize_for_player`, `analyze_ply_for_player`; `tests/docs_courses/test_f07_004_eval_normalization.py` |
| F07-005 | Evaluation loss | Previous and current evaluation | `eval_loss` or `cp_loss` | Detect a known error move | P0 | ✅ Done | `evaluation_loss` / `ply_evaluation_loss` in `engine_eval.py`; Scholar `3...Nf6`; `tests/docs_courses/test_f07_005_eval_loss.py` |

### 07.1 — Critical position detection

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-006 | Significant loss | `eval_loss` | Trigger `EVALUATION_DROP` | Compare an obvious blunder with a stable game | P0 | ✅ Done | `evaluation_drop_trigger` / `ply_evaluation_drop`; threshold 150 cp; Scholar `Nf6` vs Ruy `a6`; `tests/docs_courses/test_f07_006_evaluation_drop.py` |
| F07-007 | Only move | MultiPV | Trigger `ONLY_MOVE` | Use a position with a single sufficient defense | P1 | ✅ Done | `only_move_trigger` / `ply_only_move`; back-rank `Rxd1`; opening does not fire; `tests/docs_courses/test_f07_007_only_move.py` |
| F07-008 | Character change | Evaluations and features | Trigger `POSITION_TRANSFORMATION` | Detect a pawn break or king exposure | P1 | ✅ Done | `position_transformation_trigger`; `sample_game4` `f5` / `O-O-O`; startpos `e4` quiet; `tests/docs_courses/test_f07_008_position_transformation.py` |
| F07-009 | Immediate threat | FEN and variations | Trigger `IMMEDIATE_THREAT` | Position before mate or material loss | P1 | ⬜ Todo | |
| F07-010 | Irreversible decision | Move and position | Trigger `IRREVERSIBLE_DECISION` | Structural change, sacrifice, or critical exchange | P1 | ⬜ Todo | |
| F07-011 | Complexity | MultiPV, branching, volatility | Trigger `COMPLEX_POSITION` | Compare a tactical and a quiet position | P2 | ⬜ Todo | |
| F07-012 | Criticality score | Active triggers | Score and criticality level | Score all positions in one game | P0 | ✅ Done | `criticality_from_triggers` / `score_player_game`; 07-base §7.4 bands; Scholar all Black plies; `tests/docs_courses/test_f07_012_criticality.py` |
| F07-013 | Position ranking | Game results | Top N critical positions | Compare top 5 with human review | P0 | ✅ Done | `rank_critical_positions` / `rank_player_game`; Scholar `Nf6` #1; `tests/docs_courses/test_f07_013_ranking.py` |

### 07.2 — Candidate generation

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-014 | Stockfish MultiPV | Critical FEN | Three candidates with PV and evaluation | Run on critical positions from a PGN | P0 | ✅ Done | `analyze_multipv` in `analysis/multipv.py`; Scholar FEN + startpos; `tests/docs_courses/test_f07_014_multipv.py` |
| F07-015 | Played-move evaluation | Move and MultiPV | Rank or independent analysis | Test when the move is not in MultiPV | P0 | ✅ Done | `evaluate_played_move`; Scholar `Nf6` independent; `tests/docs_courses/test_f07_015_played_move.py` |
| F07-016 | UCI/SAN conversion | Moves and board | Readable, legal notation | Validate all generated moves | P0 | ✅ Done | `uci_to_san` / `san_to_uci` / `pv_uci_to_san`; Scholar every ply; `tests/docs_courses/test_f07_016_notation.py` |
| F07-017 | Candidate type | Position, move, and PV | Tactical, defensive, break, improvement, exchange, or prophylaxis | Manually review ten positions | P1 | ⬜ Todo | |
| F07-018 | Candidate purpose | Candidate and features | Structured chess objective | Compare with human annotation | P1 | ⬜ Todo | |

### 07.3 — Decision evaluation

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-019 | Played move vs candidates | Played move and candidates | Evaluation, purpose, and consequence diffs | Test known errors from own games | P0 | ✅ Done | `compare_played_to_candidates`; Scholar `Nf6` gap ≥150; purpose D1–D5 until F07-018; `tests/docs_courses/test_f07_019_played_vs_candidates.py` |
| F07-020 | Decision type | Critical position | `TACTICAL`, `STRATEGIC`, `PROPHYLACTIC`, `DYNAMIC`, `STATIC`, `DEFENSIVE`, `TECHNICAL`, `PRACTICAL`, `OPENING`, `ENDGAME` | Manually label twenty positions | P1 | ⬜ Todo | Align with 07.1 §5.2 |
| F07-021 | Structured position assessment | FEN and engine data | Ten MVP factors: `MATERIAL`, `KING_SAFETY`, `DEVELOPMENT`, `SPACE`, `CENTER_CONTROL`, `PAWN_STRUCTURE`, `PIECE_ACTIVITY`, `PIECE_COORDINATION`, `INITIATIVE`, `WORST_PIECE` | Compare assessment with human review on ten positions | P1 | ⬜ Todo | Replaces separate factor rows; see 07.1 §25 |
| F07-022 | Opponent threat detection | FEN and variations | Identified threats to king, material, or structure | Test positions with hanging pieces or mate threats | P1 | ⬜ Todo | MVP item 3 in 07.1 §25 |
| F07-023 | Static–dynamic balance | Position and variations | Position character and required action | Compare a closed position with a dynamic attack | P1 | ⬜ Todo | Maps to `Static-Dynamic Evaluator` |

### 07.4 — Chess diagnosis

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-026 | Primary chess error | Prior evidence | `primary_error` with supporting evidence | Contrast with human comment | P1 | ⬜ Todo | |
| F07-027 | Alternative causes | Ambiguous evidence | Hypotheses with confidence level | Verify no single cause is asserted | P2 | ⬜ Todo | |
| F07-028 | Abstention | Insufficient evidence | `UNKNOWN` or `NEEDS_REVIEW` | Use an ambiguous position | P1 | ✅ Done | `assess_diagnosis_abstention`; opening `d4` → `NEEDS_REVIEW`; Scholar `Nf6` → `NONE`; `tests/docs_courses/test_f07_028_abstention.py` |
| F07-029 | Anti-blunder check | Previous position | Checks, captures, threats, attacked pieces | Test a hanging piece or simple tactic | P1 | ⬜ Todo | Pre-decision safety gate (S1–S4) |
| F07-041 | Cognitive process hypotheses | Move, candidates, assessment | Up to five MVP process errors with confidence tier | Verify hypotheses are not stated as facts | P1 | ⬜ Todo | `MISSED_THREAT`, `SINGLE_CANDIDATE`, `PREMATURE_CALCULATION_STOP`, `FAILURE_TO_REASSESS`, `UNJUSTIFIED_SACRIFICE` |
| F07-042 | Overlooked factor identification | Assessment and played move | Factor the move failed to address | Contrast with best candidate purpose | P1 | ⬜ Todo | |

### 07.5 — Suboptimal sequences

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-030 | Suboptimal sequence | Consecutive positions | Start, development, and consequence | Use a game where deterioration precedes the blunder | P2 | ⬜ Todo | Minimum two related moves |
| F07-031 | Related errors | Diagnoses from one game | Sequences grouped by theme | Verify errors are not treated in isolation | P2 | ⬜ Todo | |

### 07.6 — Longitudinal patterns

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-032 | Longitudinal aggregation | PGN collection | Frequencies and recurring patterns | Process at least fifty games | P2 | ⬜ Todo | |
| F07-033 | Phase segmentation | Diagnoses and metadata | Opening, middlegame, and endgame patterns | Compare results by phase | P2 | ⬜ Todo | |
| F07-034 | Context segmentation | Elo, clock, and time control | Patterns by opponent level and pace | Compare blitz, rapid, and Elo bands | P3 | ⬜ Todo | |

### 07.7 — Human validation

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-035 | Review pack | Structured result | JSON with FEN, PGN, candidates, and evidence | Export one complete position | P0 | ✅ Done | `build_review_pack` / `write_review_pack`; Scholar `Nf6`; `tests/docs_courses/test_f07_035_review_pack.py` |
| F07-036 | Player confirmation | Review pack | Confirm, reject, or correct | Record candidates considered during the game | P1 | ⬜ Todo | Maps to `PLAYER_CONFIRMED` |
| F07-037 | Coach validation | Automatic diagnosis | Corrected label and comment | Review a set of real cases | P1 | ⬜ Todo | Integrates with 6.6 HITL |
| F07-038 | Golden dataset | Validated cases | Versioned dataset | Run regressions after rule changes | P1 | ⬜ Todo | |

### 07.8 — Pedagogical explanation

| ID | Feature | Input | Verifiable output | Real-PGN test | Priority | Status | Comments |
|---|---|---|---|---|---|---|---|
| F07-039 | Deterministic report | Validated diagnosis | Text without LLM and without new claims | Generate the full report for one game | P1 | ⬜ Todo | |
| F07-040 | LLM verbalization | Validated JSON | Natural, traceable explanation | Link each statement to its evidence | P3 | ⬜ Todo | LLM verbalizes only; does not decide |
| F07-043 | Post-LLM claim validator | LLM output and evidence | Reject or flag claims not in evidence | Inject a fabricated variant; expect failure | P2 | ⬜ Todo | Critic layer; see 7.1-T20 |
| F07-044 | Pedagogical exercise generation | Validated diagnosis | One typed exercise per diagnosis | Compare exercise with coach suggestion | P2 | ⬜ Todo | MVP item 10 in 07.1 §25 |
| F07-045 | UER metric | Golden explanation set | Unsupported Explanation Rate | Run on ≥20 validated explanations | P2 | ⬜ Todo | Target UER < 5% (GATE-7.1) |

## 3. Per-feature test format

Each feature must have at least one test case based on a real game.

| Field | Description |
|---|---|
| `feature_id` | Feature identifier |
| `case_id` | Stable case identifier |
| `game_id` | Game identifier |
| `pgn_source` | Original file, text, or URL |
| `player` | Analyzed player |
| `player_color` | `WHITE` or `BLACK` |
| `move_number` | Move number |
| `fen_before` | FEN before the decision |
| `played_move` | Move played |
| `expected_result` | Expected result |
| `actual_result` | Algorithm result |
| `human_label` | Manual label or comment |
| `evidence` | Evaluations, variations, and features |
| `status` | `PASS`, `FAIL`, or `NEEDS_REVIEW` |
| `notes` | Review justification |

### Example

```json
{
  "feature_id": "F07-019",
  "case_id": "F07-019-001",
  "game_id": "cmess1315-vs-ahmed-jon-2026-08-18",
  "pgn_source": "test-catalog/pgn/cm1315_ahmed_jon_20260818.pgn",
  "player": "cmess1315",
  "player_color": "WHITE",
  "move_number": 17,
  "fen_before": "...",
  "played_move": "Nxf6+",
  "expected_result": {
    "critical": true,
    "played_move_in_candidates": true,
    "decision_type": "TACTICAL"
  },
  "actual_result": {},
  "human_label": {
    "confirmed": true,
    "comment": "Knight and bishop double check."
  },
  "evidence": {
    "engine": "Stockfish",
    "multipv": 3,
    "variations": []
  },
  "status": "PASS",
  "notes": ""
}
```

## 4. Documentation structure

```text
module07/
├── 07_overview.md
├── 07_0_pgn_and_engine_analysis.md
├── 07_1_critical_position_detection.md
├── 07_2_candidate_generation.md
├── 07_3_move_comparison.md
├── 07_4_decision_diagnosis.md
├── 07_5_suboptimal_sequences.md
├── 07_6_player_patterns.md
├── 07_7_human_validation.md
├── 07_8_explanation_composer.md
├── contracts/
│   ├── critical_position.schema.json
│   ├── candidate.schema.json
│   ├── diagnosis.schema.json
│   └── human_review.schema.json
└── test-catalog/
    ├── feature_matrix.md
    ├── golden_cases.jsonl
    └── pgn/
```

## 5. First implementable increment

### Goal

Complete a minimal vertical slice on real games:

```text
PGN
→ position reconstruction
→ Stockfish evaluation
→ critical position detection
→ MultiPV
→ comparison with the played move
→ review pack
→ golden tests
```

### Included features

- [x] F07-001 — Game import
- [x] F07-002 — Player selection
- [x] F07-003 — Stockfish analysis
- [x] F07-004 — Evaluation normalization
- [x] F07-005 — Evaluation loss
- [x] F07-006 — Significant-loss trigger
- [x] F07-012 — Initial criticality score
- [x] F07-013 — Critical position ranking
- [x] F07-014 — Stockfish MultiPV
- [x] F07-015 — Played-move evaluation
- [x] F07-016 — UCI/SAN conversion
- [x] F07-019 — Played move vs candidates
- [x] F07-028 — Diagnostic abstention
- [x] F07-035 — Review pack
- [ ] F07-038 — Golden dataset

### Out of scope for this increment

- Lc0
- LLM
- RAG
- FastAPI
- Streamlit
- Cognitive hypotheses
- Full strategic taxonomy
- Suboptimal sequences
- Longitudinal patterns
- Exercise generation

## 6. Implementation phases

### Phase 1 — Contracts and test cases

- [x] Define canonical DTOs (import only: `NormalizedGame`, `PlyRecord`).
- [ ] Create JSON Schemas.
- [ ] Select 10–20 real positions.
- [ ] Store original PGNs.
- [ ] Document the expected result for each case.
- [ ] Mark each case as fact, inference, or human confirmation.

**Completion criterion:** cases can be described without depending on the current `analysis/mental_model/` code. *(Not met: schemas and golden cases still open.)*

### Phase 2 — PGN and Stockfish

- [x] Import PGN.
- [x] Identify the analyzed player (F07-002).
- [x] Reconstruct FENs.
- [x] Analyze a ply with Stockfish (F07-003; full-game loop still open).
- [x] Normalize evaluations (F07-004).
- [x] Compute evaluation loss.
- [x] Handle mate evaluations (sign flip with player color).

**Completion criterion:** one full game produces coherent evaluations from the player's perspective.

### Phase 3 — Critical positions

- [x] Implement `EVALUATION_DROP`.
- [x] Define a minimal `criticality_score`.
- [x] Rank positions.
- [x] Select top N.
- [x] Compare ranking with human review.

**Completion criterion:** known decisive positions appear near the top of the ranking.

### Phase 4 — Candidates and comparison

- [x] Run MultiPV=3.
- [x] Convert candidates to SAN.
- [x] Evaluate the played move even when not in MultiPV.
- [x] Compute objective differences.
- [x] Compare main variations.
- [x] Abstain when evidence is insufficient.

**Completion criterion:** each critical position contains three candidates, the played move, and a structured comparison.

### Phase 5 — Validation

- [x] Generate one review pack per position.
- [ ] Record human review.
- [ ] Convert confirmed cases into golden tests.
- [ ] Run regressions automatically.
- [ ] Measure agreement between algorithm and review.

**Completion criterion:** validated cases can be re-run after any change without full manual review.

## 7. First-increment acceptance criteria

- [ ] Processes at least five complete real games.
- [x] Correctly attributes moves for the player as White and as Black (F07-002; full coaching analysis still open).
- [x] Legally reconstructs all moves and FENs (F07-001 tests on sample PGN; full five-game set still open).
- [ ] Correctly normalizes centipawns and mate scores.
- [ ] Detects known objective errors.
- [ ] Returns a reproducible critical-position ranking.
- [ ] Obtains three legal candidates via MultiPV.
- [ ] Evaluates the played move even when not among the candidates.
- [x] Generates review packs in JSON.
- [ ] Includes at least ten golden cases.
- [ ] Does not generate explanations via LLM.
- [ ] Does not present inferences as facts.
- [ ] Does not depend on the current `analysis/mental_model/` implementation.

## 8. Priority order

```text
P0
1. Contracts
2. Real PGN cases
3. Stockfish analysis
4. Normalization
5. Basic criticality
6. MultiPV
7. Comparison
8. Review pack

P1
9. Golden dataset
10. Additional triggers
11. Decision taxonomy
12. Anti-blunder
13. Human validation
14. Deterministic report
15. Ten-factor assessment
16. Cognitive hypotheses

P2
17. Strategic features
18. Suboptimal sequences
19. Longitudinal patterns
20. Post-LLM validator
21. Exercise generation
22. UER metric

P3
23. Advanced segmentation
24. LLM verbalization
25. Lc0
26. API and UI
```

## 9. Decision on existing code

The current package:

```text
analysis/mental_model/
```

is considered a proof of concept.

- Do not preserve interfaces solely for compatibility.
- Do not adapt definitive contracts to the existing draft.
- Reuse only components backed by PGN cases.
- Replace any implementation that hinders traceability.
- Keep engine analysis separate from interpretation.
- Accept a full rewrite if it simplifies the vertical flow.
