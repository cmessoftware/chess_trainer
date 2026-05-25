# Analysis Pipeline V7 - Validated Explanation System

## Overview

**Paradigm shift**: The LLM must NOT analyze chess. It must ONLY verbalize a structured JSON we build.

This architecture prevents hallucinations by:
1. Using only Stockfish ground truth (not buggy `material_balance` field)
2. Cross-validating ML predictions against Stockfish
3. Detecting patterns conservatively (no over-tagging)
4. Building complete, self-contained JSON packs
5. Enforcing strict LLM safety rules (verbalize only what's in JSON)
6. Post-validating LLM output

## Architecture

```
DB (Stockfish + ML predictions + temporal)
  ↓
Validator (cross-check ML vs Stockfish)
  ↓
PatternEngine (geometry + PV hints)
  ↓
ExplanationPack (JSON with ALL data)
  ↓
LLMExplainer (verbalize ONLY what's in JSON)
  ↓
Validated Feedback
```

## Modules

### 1. validator.py
**Purpose**: ML vs Stockfish cross-validation

**Key components**:
- `classify_cp_loss(cp_loss: int) -> Label`: Maps cp_loss to label
  - ≤40: good
  - ≤90: inaccuracy
  - ≤200: mistake
  - >200: blunder
- `validate_prediction(predicted_label, cp_loss, *, final_label_policy) -> ValidationResult`: Cross-validates ML vs Stockfish

**Design**: Pure functions, deterministic

### 2. pattern_engine.py
**Purpose**: Conservative tactical/positional pattern detection

**Detectable patterns**:
- Tactical: hanging_piece, fork, pin, discovered_attack
- Positional: exposed_king, weak_back_rank, open_file_attack, overloaded_defender

**Design**: Uses geometry + PV hints (NOT full tactical analysis). Stub implementation for MVP (TODO: integrate python-chess).

**Principle**: "Only tag when evidence is strong from geometry/PV. Avoid over-tagging."

### 3. explanation_pack.py
**Purpose**: JSON structure builder for LLM consumption

**Structure**:
```python
ExplanationPack:
  - game_id: str
  - ply: int
  - phase: str  # opening/middlegame/endgame
  - played_move: str
  - final_label: Label
  - validator: dict  # ML vs Stockfish results
  - stockfish: dict  # Ground truth analysis
  - patterns: dict   # Detected patterns
  - temporal_context: dict  # Streaks, cascades
```

**Design**: Complete self-contained JSON with ALL info LLM needs.

### 4. llm_explainer.py
**Purpose**: LLM verbalizer (NOT analyzer)

**CRITICAL SAFETY RULES** (enforced in system prompt):
1. Only use info present in JSON
2. Never analyze chess positions
3. Never invent moves (only mention best_moves/multipv)
4. Never claim tactics unless in patterns.*_tags
5. If data missing, say so (never guess)

**Output format**: 3 lines in Spanish
- Diagnosis: [One sentence using validator.final_label and stockfish.cp_loss]
- Better move: [Mention best move from stockfish.best_moves + idea]
- Training rule: [Short heuristic grounded in patterns.tactical_tags or phase]

**Design**: Wrapper around LLM client, strict input/output validation.

### 5. pipeline.py
**Purpose**: Main orchestrator

**Entry point**: `generate_validated_feedback(game_id, *, repos, llm_client, cp_loss_threshold, max_items) -> dict`

**Flow**:
1. Load game data
2. Load Stockfish analysis per ply
3. Load ML predictions per ply
4. Load temporal context per ply
5. Select critical moves (cp_loss ≥ threshold OR label ∈ {mistake, blunder} OR streak ≥ 3)
6. For each critical move:
   - Validate (ML vs Stockfish)
   - Detect patterns
   - Build explanation pack
   - Generate LLM explanation
7. Return structured feedback

**Returns**:
```json
{
  "game_id": "...",
  "stats": {
    "num_moves_analyzed": 50,
    "num_critical": 8,
    "num_disagreements": 2
  },
  "critical_feedback": [
    {
      "ply": 23,
      "final_label": "mistake",
      "model_disagreement": false,
      "explanation": {
        "diagnosis": "...",
        "better_move": "...",
        "training_rule": "..."
      },
      "pack": {...}
    },
    ...
  ]
}
```

### 6. repository_adapters.py
**Purpose**: Maps existing DB schema to pipeline interface

**Current DB schema**:
- `games`: game_id, pgn, white_player, black_player, result
- `features`: game_id, move_number, fen, move_san, move_uci, material_balance, score_diff, error_label, phase

**Pipeline expected interface**:
- `repos.get_game(game_id) -> dict`
- `repos.get_stockfish_rows(game_id) -> list[dict]`
- `repos.get_predictions(game_id) -> dict[ply -> {predicted_label, ...}]`
- `repos.get_temporal_context(game_id) -> dict[ply -> {streaks, cascade, ...}]`

**Important**: Material balance field in Features is corrupt/duplicate. We ignore it and use only `score_diff` to derive `cp_loss`.

## Usage

### 1. Basic usage

```python
from api.services.analysis_pipeline import generate_validated_feedback, create_v7_repos

# Create repository adapter
repos = create_v7_repos(db_session, models)

# Wrap LLM client
llm_client = LLMClientWrapper(openai_client)

# Generate feedback
result = generate_validated_feedback(
    game_id="aec7f86c...",
    repos=repos,
    llm_client=llm_client,
    cp_loss_threshold=90,
    max_items=10,
)
```

### 2. API endpoint

```python
from fastapi import APIRouter, Depends
from .services.analysis_pipeline import generate_validated_feedback, create_v7_repos

@router.post("/analysis/v7-feedback")
async def generate_v7_feedback(
    request: GenerateFeedbackRequest,
    db: Session = Depends(get_db),
):
    repos = create_v7_repos(db, models)
    llm_client = LLMClientWrapper(openai_client)
    
    result = generate_validated_feedback(
        request.game_id,
        repos=repos,
        llm_client=llm_client,
        cp_loss_threshold=request.cp_loss_threshold,
        max_items=request.max_items,
    )
    
    return {"status": "success", "data": result}
```

### 3. A/B testing (V6 vs V7)

See [integration_example.py](integration_example.py) for `compare_v6_vs_v7()` helper.

## V7 vs V6 Comparison

| Dimension              | V6 (Current)                                     | V7 (New)                                  |
| ---------------------- | ------------------------------------------------ | ----------------------------------------- |
| **LLM Role**           | Analyze game + generate text                     | Only verbalize pre-built JSON             |
| **Material Detection** | Calculate from Features.material_balance (buggy) | Use Stockfish cp_loss only (ground truth) |
| **Pattern Detection**  | LLM invents tactics                              | Conservative geometry + PV hints          |
| **Validation**         | Post-generation regex checks                     | Pre-generation + post-validation          |
| **Hallucination Risk** | HIGH (LLM can invent facts)                      | LOW (LLM only repeats JSON)               |
| **Architecture**       | Single service file (2200+ lines)                | Modular pipeline (5 files, ~800 lines)    |
| **Testability**        | Hard (async, DB dependencies)                    | Easy (pure functions, mocked)             |

## Material Detection Fix (Root Cause Resolution)

**Problem** (V6):
- Used `Features.material_balance` field (has duplicate/incorrect data)
- Example: Move 11-12 are balanced exchanges but DB shows +1.0, +3.0

**Solution** (V7):
- **Ignore `material_balance` completely**
- Use `stockfish.cp_loss` as single source of truth
- If cp_loss >= threshold → material advantage changed
- No need to detect specific piece captures (Stockfish already evaluated it)

## Testing

### Unit tests

```python
# test_validator.py
def test_classify_cp_loss():
    assert classify_cp_loss(30) == "good"
    assert classify_cp_loss(60) == "inaccuracy"
    assert classify_cp_loss(150) == "mistake"
    assert classify_cp_loss(250) == "blunder"

# test_pattern_engine.py
def test_pattern_engine_stub():
    engine = PatternEngine()
    result = engine.detect(fen_before="...", played_move_uci="e2e4", ...)
    assert isinstance(result, PatternResult)

# test_explanation_pack.py
def test_build_explanation_pack():
    pack = build_explanation_pack(...)
    assert pack.game_id == "..."
    assert pack.final_label in ["good", "inaccuracy", "mistake", "blunder"]
```

### Integration tests

```python
# test_pipeline.py
def test_generate_validated_feedback(mock_repos, mock_llm):
    result = generate_validated_feedback(
        "test_game_id",
        repos=mock_repos,
        llm_client=mock_llm,
    )
    assert "game_id" in result
    assert "stats" in result
    assert "critical_feedback" in result
```

## TODO

### High priority
- [ ] Implement pattern_engine actual detection (python-chess integration)
- [ ] Implement llm_explainer post-validation
- [ ] Add API endpoint for V7 pipeline
- [ ] Test with real game data (aec7f86c...)
- [ ] Compare V7 vs V6 outputs

### Medium priority
- [ ] Add temporal data computation (or dedicated table)
- [ ] Add cascade detection logic
- [ ] Add unit tests for all modules
- [ ] Add integration tests

### Low priority
- [ ] Add "cita obligatoria" mode (force LLM to reference JSON fields)
- [ ] Add metrics/monitoring (disagreement rate, hallucination rate)
- [ ] Add caching for expensive operations

## References

- V7 Requirements: `ChessTrainer — Prompt de Implementación (LLM grounded + MCP) + Roadmap_v7.md`
- V6 Service: `src/api/services/llm_analysis_service.py`
- DB Models: `src/api/models/`

---
_Last updated: 2026-02-14_
