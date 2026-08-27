# Module 6.5 — LLM Coaching Recommendations

> **Placement:** between Module 06 (SHAP) and Module 07 (RAG)  
> **Architecture (as-built):** [6.5_llm_integration_architecture.md](./6.5_llm_integration_architecture.md)  
> **Coaching report format (V7):** [accc_llm_coaching_recommendations_v7.md](./accc_llm_coaching_recommendations_v7.md)  
> **V2 design (root cause):** [accc_llm_coaching_recommendations_V2.md](./accc_llm_coaching_recommendations_V2.md)  
> **Extended pattern catalog (future):** [04-ai_chess_coach_course_llm_recommendationsf_from_shap_+_pattern_engine.md](./04-ai_chess_coach_course_llm_recommendationsf_from_shap_+_pattern_engine.md)  
> **Notebook:** `06_5_llm_coaching_recommendations.ipynb`  
> **Goal:** end-to-end course pipeline that turns Human Pattern + SHAP + **structured diagnosis** into **grounded coaching text** via a provider-agnostic LLM layer (**DeepSeek API default**, Gemini optional).

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
Root Cause Analysis + DiagnosisBuilder (V4–V6) + Instructional Patterns v2
    ↓
Verbal game brief + V7 lesson_clusters
    ↓
Prompt Builder (V7 four-section coaching rules, Spanish)
    ↓
LLMProvider (DeepSeek / Gemini)  (manual / optional in notebook)
    ↓
validate_coaching_response → or deterministic fallback
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
| API key (optional, live LLM) | `DEEPSEEK_API_KEY` or `GEMINI_API_KEY` in repo `.env` — see [`.env.example`](./.env.example) (never committed) |

---

## 3. Package layout (course-local, portable)

```text
docs/ai_chess_coach_course/
├── llm/
│   ├── base.py                   # LLMProvider ABC
│   ├── gemini_provider.py        # google-genai + gemini-2.5-flash
│   ├── openai_compatible_provider.py  # DeepSeek / OpenAI-compatible API
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
│   ├── diagnosis/                # V4: board detectors (python-chess)
│   ├── diagnosis_builder/        # V5–V6: tags, features, diagnosis_type, styles
│   ├── game_timeline.py          # full-game feature rows by game_id (+ tags)
│   ├── game_analysis.py          # complete-game selection, player filter
│   ├── pgn_context.py            # context_pgn windows, tactical_line
│   ├── human_brief.py            # verbal Spanish brief + critical_moves
│   ├── critical_move_contract.py # V3 LLM payload normalization
│   ├── lesson_synthesizer.py     # V7 lesson_clusters
│   ├── prompt_builder.py         # V7 coaching prompt templates
│   ├── coaching_generate.py      # validate → prompt → optional LLM → fallback
│   ├── coaching_validation.py    # post-LLM V7 validation
│   ├── coaching_debug.py         # debug artifacts
│   ├── deterministic_coaching.py # no-LLM V7-shaped report
│   ├── context_builder.py        # profile JSON (Phase B)
│   └── pipeline.py               # explain_player_games()
├── artifacts/module06_5/
│   ├── single_game_prompt.txt
│   ├── debug/phase_a/            # prompt, payload, LLM response
│   ├── sample_context.json
│   ├── sample_prompt.txt
│   └── (optional) *_recommendation.txt  # after manual LLM call
├── .env.example
├── _gen_llm_coaching_nb.py
└── 06_5_llm_coaching_recommendations.ipynb
```

Dependencies: `google-genai` (optional, Gemini only). `python-chess` for PGN and board diagnosis. DeepSeek uses stdlib HTTP (no extra package).

---

## 4. LLM provider layer

### 4.1 Interface

```python
class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str: ...
```

### 4.2 Providers (implemented)

| Provider | Env | Model example |
|----------|-----|----------------|
| **DeepSeek** (default) | `LLM_PROVIDER=deepseek`, `DEEPSEEK_API_KEY` | `deepseek-chat` |
| **Gemini** | `LLM_PROVIDER=gemini`, `GEMINI_API_KEY` | `gemini-2.5-flash` |
| **Dry run** | empty API key | CI / notebook without billing |

Config: `LLMSettings` in `llm/settings.py`; template in `.env.example`.

- DeepSeek: `openai_compatible_provider.py` → `POST https://api.deepseek.com/v1/chat/completions`
- Gemini: `google-genai`; quota retries; Spanish placeholder via `generate_coaching_text()`

### 4.3 Invocation policy

| Context | Live LLM called? |
|---------|------------------|
| `pytest` / CI | **Never** — dry-run providers and fixtures only |
| Notebook pipeline cells (Phase A/B build) | **No** — saves prompts to `artifacts/module06_5/` |
| Notebook optional cell (`INVOKE_GEMINI=True`) | **Yes** — uses `LLM_PROVIDER` from `.env` |

Vendor SDKs are isolated in `GeminiProvider` and HTTP client in `OpenAICompatibleProvider` only.

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

### 6.4 Structured diagnosis (V4–V6)

For each root-cause moment, `DiagnosisBuilder` (in `root_cause.py` flow) produces:

- `diagnosis_type`: `tactical` | `opening` | `positional` | `endgame` | …
- `issue`, `consequence`, `lesson_hint`, `theme`, `supporting_features`
- `opponent_reply` in LLM payload **only** when `diagnosis_type == "tactical"`
- Priority: SQLite `tags` → board detectors → legacy heuristics

See architecture doc §5 for details.

---

## 7. LLM input contracts

### 7.1 Phase A — single game brief (`prepare_single_game_brief_for_llm`)

Spanish structured JSON for the LLM (not shown verbatim to the player). V3 normalized fields per moment:

| Field | Role |
|-------|------|
| `move_number`, `player_move`, `phase`, `severity` | Identity |
| `issue`, `lesson_hint`, `consequence`, `context_pgn` | Evidence |
| `opponent_reply` | Tactical punishment only |
| `diagnosis_type`, `theme`, `sections` | V6 style hints |
| `root_cause` | Prioritize in prompt |

V7 additions at brief root:

| Field | Role |
|-------|------|
| `lesson_clusters` | 2–3 merged lessons (`lesson_synthesizer.py`) |
| `phase_summary` | Opening/middlegame/endgame hints for **Resumen breve** |

Example normalized moment (sent to LLM):

```json
{
  "move_number": 21,
  "player_move": "21. c4",
  "diagnosis_type": "tactical",
  "issue": "Peón avanzado sin defensa.",
  "lesson_hint": "Verifica defensas antes de empujar.",
  "opponent_reply": "21... Nxe5",
  "context_pgn": "20...Bb7 21. c4 21...Rxe5 22. ...",
  "root_cause": true,
  "severity": "error grave",
  "phase": "medio juego"
}
```

**Never send:** raw SHAP arrays, `score_cp`, numeric `score_diff`, full PGN, deprecated bare `move` field.

### 7.2 Phase B — player profile (`build_coaching_context`)

Structured JSON across N complete games (patterns, games_analyzed, trends). Same forbidden fields as v1 spec.

| Phase | Scope |
|-------|--------|
| **A** | 1 complete game, all player moves, RCA brief |
| **B** | 8–50 complete games (demo); production → hundreds/thousands |
| **Later** | Modules 7–8: persistent player pattern DB + RAG |

---

## 8. Prompt engineering rules (V7 — Phase A)

Player-facing report must have **exactly four sections** (see [accc_llm_coaching_recommendations_v7.md](./accc_llm_coaching_recommendations_v7.md)):

1. **Resumen breve** — opening / middlegame / ending; no individual moves yet  
2. **Lecciones principales** — 2–3 ideas; merge related `critical_moves` via `lesson_clusters`  
3. **Momentos clave** — one concise entry per `critical_moves` item (evidence only)  
4. **Plan de entrenamiento** — three concrete items linked to lessons  

Rules enforced in prompt and validated after LLM (`coaching_validation.py`):

- Respond **always in Spanish**; no SHAP, features, parquet, or model jargon  
- Only moves listed in `critical_moves` as key student moments  
- Lessons are main content; moments are secondary  
- No generic filler (“JCA”, “calcula más”) unless supported by payload  
- Prioritize `root_cause: true` and `lesson_clusters` when synthesizing  

On validation failure or missing API: `deterministic_coaching.render_deterministic_coaching()` returns the same four-section shape.

### 8.2 Profile (Phase B)

- Same language and honesty rules as v1.
- Natural phrasing (“a menudo”, “en varias partidas”); no percentages in player-facing text.

---

## 9. Notebook flow (`06_5_llm_coaching_recommendations.ipynb`)

1. Load env, model, validation split, `CourseFeaturesRepository`
2. **LLM — provider and quota** (DeepSeek / Gemini; no API call in setup)
3. **Phase A:** one complete game → SHAP → brief + RCA + diagnosis → `lesson_clusters` preview → save `single_game_prompt.txt`
4. **Phase A (optional):** `generate_single_game_coaching(..., invoke_llm=True)` — writes `debug/phase_a/*` and recommendation text
5. **Phase B:** N games → profile context → save `sample_context.json` + `sample_prompt.txt`
6. **Phase B (optional):** invoke LLM manually
7. Pedagogy: Python diagnoses; LLM narrates V7 structure; SHAP stays in Python

Regenerate notebook after template changes:

```powershell
python docs/ai_chess_coach_course/_gen_llm_coaching_nb.py
```

---

## 10. Acceptance criteria

- [x] `llm/` package: ABC, Gemini, DeepSeek (OpenAI-compatible), factory, settings, dry-run, quota fallback
- [x] `coaching/` package: pattern v1, instructional v2, RCA, timeline, PGN, diagnosis V4–V6, V7 lesson synthesizer
- [x] `coaching_generate.py`: validate payload → prompt → optional LLM → V7 validation → deterministic fallback
- [x] RCA groups symptoms under root causes (cluster + walkback)
- [x] `critical_moves` V3 contract + `lesson_clusters` in LLM payload
- [x] Notebook builds prompts without live LLM by default
- [x] Live LLM only in optional notebook cell (`invoke_llm=True`)
- [x] LLM payload contains no raw SHAP or engine cp columns
- [x] Tests pass without network (`test_insight_coaching_v7.py`, `test_openai_compatible_provider.py`, …)

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

Final coaching should match [V7 success criteria](./accc_llm_coaching_recommendations_v7.md):

- Teach **2–3 strategic lessons**, not a flat list of mistakes  
- Use critical moves as **evidence**, not as the report skeleton  
- Focus on **causes** (Python diagnosis) with natural Spanish prose (LLM)  
- Avoid generic filler unless backed by `issue` / `context_pgn`  
- **Known gap:** noisy SQLite tactical tags (e.g. `discovered_attack`) still flow into `issue`; fix tagging upstream for better narratives  

Reference: [gemini_2.5_flash_recommendation_analysis.md](./gemini_2.5_flash_recommendation_analysis.md).
