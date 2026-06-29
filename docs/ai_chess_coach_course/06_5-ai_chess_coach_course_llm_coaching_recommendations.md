# Module 6.5 — LLM Coaching Recommendations (Gemini 2.5 Flash)

> **Placement:** between Module 06 (SHAP) and Module 07 (RAG)  
> **Architecture input:** [6.5_llm_integration_architecture.md](./6.5_llm_integration_architecture.md)  
> **V2 design (root cause):** [accc_llm_coaching_recommendations_V2.md](./accc_llm_coaching_recommendations_V2.md)  
> **Extended pattern catalog (future):** [04-ai_chess_coach_course_llm_recommendationsf_from_shap_+_pattern_engine.md](./04-ai_chess_coach_course_llm_recommendationsf_from_shap_+_pattern_engine.md)  
> **Notebook:** `06_5_llm_coaching_recommendations.ipynb`  
> **Goal:** end-to-end course pipeline that turns Human Pattern + SHAP + **root-cause analysis** into **grounded coaching text** via a provider-agnostic LLM layer (Gemini 2.5 Flash first).

---

## 1. Why Module 6.5 exists

Modules 06–09 originally split explainability, RAG, LLM, and evaluation across four steps. For a **first shippable course arc**, students should see one working coaching pipeline **before** building vector stores and local LLMs.

Module 6.5 delivers:

```text
PGN + engine features (SQLite / parquet)
    ↓
Human Pattern model (Module 04/05) + SHAP (Module 06)
    ↓
Pattern Engine v1 (aggregate themes across moves)
    ↓
Root Cause Analysis + Instructional Patterns v2 (per critical moment)
    ↓
Verbal game brief / profile context JSON
    ↓
Prompt Builder (coaching rules, Spanish)
    ↓
LLMProvider → Gemini 2.5 Flash  (manual / optional in notebook)
    ↓
Coaching recommendation (text)
```

**Problem addressed (v2):** coaching that only cites the move where eval collapses (symptom) instead of the earlier move that caused it (root cause). RCA groups related mistakes into one lesson for **any game**, not a single demo.

**Explicitly out of scope for 6.5:** ChromaDB / RAG (Module 07), Ollama / local models (Module 08), live Stockfish at coaching time, `best_move` from engine, agentic orchestration (Module 10+).

---

## 2. Prerequisites

| Input | Source |
|-------|--------|
| Best Human Pattern run | `artifacts/module06/human_model.joblib` |
| SHAP explainer | computed in notebook from Module 06 model |
| Encoded dataset / splits | `data/datasets/course_training_dataset.parquet` + `split_by_game_id` |
| Course DB (PGN, timeline) | `docs/ai_chess_coach_course/course_data.sqlite` via `CourseFeaturesRepository` |
| API key (optional, live LLM) | `GEMINI_API_KEY` in repo `.env` (never committed) |

---

## 3. Package layout (course-local, portable)

```text
docs/ai_chess_coach_course/
├── llm/
│   ├── base.py                   # LLMProvider ABC
│   ├── gemini_provider.py        # google-genai + gemini-2.5-flash
│   ├── provider_factory.py
│   ├── dry_run_provider.py       # no API key
│   ├── resilient_provider.py
│   ├── generate.py               # generate_coaching_text() + quota fallback
│   ├── errors.py
│   └── settings.py               # LLMSettings, load_course_env()
├── coaching/
│   ├── pattern_engine.py         # v1: features/SHAP → named patterns
│   ├── instructional_patterns.py # v2: pedagogical motifs (loose_piece, …)
│   ├── root_cause.py             # RCA + incident grouping (any game)
│   ├── game_timeline.py          # full-game feature rows by game_id
│   ├── game_analysis.py          # complete-game selection, player filter
│   ├── pgn_context.py            # context_pgn windows, tactical_line
│   ├── human_brief.py            # verbal Spanish brief + critical_moves
│   ├── context_builder.py        # profile JSON (Phase B)
│   ├── prompt_builder.py         # coaching prompt templates
│   └── pipeline.py               # explain_player_games()
├── artifacts/module06_5/
│   ├── single_game_prompt.txt
│   ├── sample_context.json
│   ├── sample_prompt.txt
│   └── (optional) *_recommendation.txt  # only after manual Gemini call
├── _gen_llm_coaching_nb.py
└── 06_5_llm_coaching_recommendations.ipynb
```

Dependency: `google-genai` (optional; only for live Gemini). `python-chess` used for PGN parsing.

---

## 4. LLM provider layer

### 4.1 Interface

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...
```

### 4.2 Gemini 2.5 Flash (default)

- SDK: `from google import genai`
- Model: `gemini-2.5-flash` (override via `LLM_MODEL` in `.env`)
- Config: `LLMSettings(provider="gemini", model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))`
- Quota: retries on 429; `generate_coaching_text()` can return Spanish placeholder + saved prompt

### 4.3 Invocation policy

| Context | Gemini called? |
|---------|----------------|
| `pytest` / CI | **Never** — dry-run providers and fixtures only |
| Notebook pipeline cells (Phase A/B build) | **No** — saves prompts to `artifacts/module06_5/` |
| Notebook optional cells / `LLM_AUTO_CALL=true` | **Yes** — user-initiated |

No coaching component imports vendor SDKs directly except `GeminiProvider`.

---

## 5. Pattern Engine

### 5.1 v1 — aggregate themes (SHAP + features)

Used for `recurring_themes` across many moves / games:

| Pattern ID | Trigger (example) |
|------------|-------------------|
| `unsafe_king` | low `king_safety` + high \|SHAP on king_safety\| |
| `low_mobility` | low `self_mobility` |
| `opening_unfamiliarity` | dominant `opening_*` + mistake/blunder |
| `tactical_blind_spot` | high `branching_factor` / tactical SHAP |
| `endgame_technique` | `is_pawn_endgame` + material features |
| `uncastled_king` | no castling rights early |

### 5.2 v2 — instructional patterns (per critical moment)

Diagnoses **in Python**; LLM explains only. Implemented in `instructional_patterns.py`:

| Pattern ID | Meaning |
|------------|---------|
| `loose_piece` | piece lost sufficient defense |
| `hanging_piece` | piece left en prise |
| `undefended_pawn` | pawn push left a pawn capturable |
| `tactical_oversight` | missed forcing tactic |
| `passive_piece` | piece restricted / misplaced |
| `king_safety` | genuine king exposure (strict threshold — avoid overuse) |

Signals: `error_label`, `score_diff`, `move_san`, opponent reply from PGN, v1 SHAP hints.  
**Rule:** SHAP numeric values and engine cp stay in Python; LLM gets verbal `eval_shift` only.

---

## 6. Root Cause Analysis (v2)

Applies to **any** `game_id` with features in the course DB.

### 6.1 Critical move candidates

- Source: `error_label in ("mistake", "blunder")` on coached-player rows (engine classification at feature time).
- Not filtered by ML prediction for inclusion.

### 6.2 Root detection (game-agnostic)

1. **Short walkback** (default 5 plies): earliest player mistake/blunder in the lookback window.
2. **Incident clustering** (default ≤ 8 player moves between errors): merges long forcing sequences so late blunders (symptoms) roll up to the first error in the chain.
3. Output: one **root cause** per incident; later errors listed in `consequence_moves` (omitted from top-N coaching moments).

### 6.3 PGN enrichment

- `context_pgn`: ±4 ply window around root move (from `games.pgn`, not full PGN to LLM).
- `tactical_line`: opponent follow-up plies parsed from PGN (e.g. `21...Rxe5`).

---

## 7. LLM input contracts

### 7.1 Phase A — single game brief (`build_verbal_game_brief`)

Spanish verbal JSON. Example `critical_moves` entry:

```json
{
  "move_number": 21,
  "move": "21. c4",
  "error_label": "mistake",
  "root_cause": true,
  "pattern": "undefended_pawn",
  "concept": "peón avanzado indefenso: un peón importante quedó sin defensa.",
  "consequence": "La secuencia 21...Rxe5 22. ... aprovechó el error.",
  "lesson": "Antes de empujar un peón, confirma que los peones vecinos siguen defendidos.",
  "eval_shift": "La posición cedió iniciativa o material de forma clara.",
  "severity": "error claro",
  "phase": "medio juego",
  "tactical_line": "21...Rxe5",
  "consequence_moves": ["51. Rd3"],
  "context_pgn": "20...Bb7 21. c4 Rxe5 22. Nxe5 ..."
}
```

**Never send:** raw SHAP arrays, `score_cp`, `score_diff` numbers, full PGN, feature vectors.

### 7.2 Phase B — player profile (`build_coaching_context`)

Structured JSON across N complete games (patterns, games_analyzed, trends). Same forbidden fields as v1 spec.

| Phase | Scope |
|-------|--------|
| **A** | 1 complete game, all player moves, RCA brief |
| **B** | 8–50 complete games (demo); production → hundreds/thousands |
| **Later** | Modules 7–8: persistent player pattern DB + RAG |

---

## 8. Prompt engineering rules

### 8.1 Single-game (Phase A)

- Respond **always in Spanish**.
- Prioritize entries with `root_cause: true`.
- Explain **cause** (`pattern`, `concept`) and **consequence** (`consequence`, `tactical_line`).
- Do **not** repeat symptom moves listed only in `consequence_moves`.
- Use `context_pgn` / `tactical_line`; do not invent variations.
- No generic king/castling advice unless supported by the moment.
- No SHAP, ML, or engine jargon.

### 8.2 Profile (Phase B)

- Same language and honesty rules as v1.
- Natural phrasing (“a menudo”, “en varias partidas”); no percentages in player-facing text.

---

## 9. Notebook flow (`06_5_llm_coaching_recommendations.ipynb`)

1. Load env, model, validation split, `CourseFeaturesRepository`
2. **LLM — modelo y cuota** (links to AI Studio rate limits; no API call)
3. **Phase A:** one complete game → SHAP → verbal brief + `critical_moves` (RCA) → save `single_game_prompt.txt`
4. **Phase A (optional):** invoke Gemini manually (`LLM_AUTO_CALL=true` or run optional cell)
5. **Phase B:** N games → profile context → save `sample_context.json` + `sample_prompt.txt`
6. **Phase B (optional):** invoke Gemini manually
7. Pedagogy markdown: SHAP stays in Python; RCA + patterns diagnose; LLM narrates

Regenerate notebook after template changes:

```powershell
python docs/ai_chess_coach_course/_gen_llm_coaching_nb.py
```

---

## 10. Acceptance criteria

- [x] `llm/` package: ABC, Gemini, factory, settings, dry-run, quota fallback
- [x] `coaching/` package: pattern v1, instructional v2, root cause, timeline, PGN, human brief, context, prompt, pipeline
- [x] RCA groups symptoms under root causes for arbitrary games (cluster + walkback)
- [x] `critical_moves` includes `root_cause`, `pattern`, `tactical_line`, verbal `eval_shift`
- [x] Notebook builds prompts without calling Gemini by default
- [x] Gemini only in optional notebook cells / `LLM_AUTO_CALL=true`
- [x] LLM payload contains no raw SHAP, no engine cp columns
- [x] Tests pass without network / without Gemini (`tests/docs_courses/test_root_cause.py`, `test_instructional_patterns.py`, `test_human_brief.py`, `test_llm_coaching.py`, …)

---

## 11. Relationship to later modules

| Module | Builds on 6.5 by… |
|--------|-------------------|
| **07 RAG** | Adding retrieved snippets to context (not replacing RCA / pattern engine) |
| **08 LLM Explanation** | Second provider (Ollama); RAG-augmented prompts |
| **09** | Consistency / hallucination tests on 6.5+ outputs |
| **10+** | Agentic planner over the same context contract |

Module 6.5 defines the **brief / context JSON contract** later modules must extend, not replace.

---

## 12. Success criteria (coaching quality)

Final coaching should:

- Focus on **causes** rather than **symptoms**.
- Explain **why** the mistake happened using `pattern` + PGN evidence.
- Group related errors into a single lesson per incident.
- Avoid generic filler (“king safety”, “calculate more”) unless backed by a concrete `critical_moves` entry.

Reference manual critique: [gemini_2.5_flash_recommendation_analysis.md](./gemini_2.5_flash_recommendation_analysis.md).
