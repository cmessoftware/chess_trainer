# Design: implement-course-modules-06_5

## Design Goals

- Deliver the **minimum viable coaching pipeline** for the first course version (Modules 01–06.5).
- Keep LLM **provider-agnostic**; **DeepSeek API** and **Gemini** implemented; dry-run for CI.
- Never expose raw SHAP arrays or engine features to the LLM.
- Reuse Module 05/06 artifacts without retraining.
- **V7:** lesson-first player report; Python clusters moments before LLM narration.

## Canonical Artifacts

| Artifact | Path |
|----------|------|
| Spec | `06_5-ai_chess_coach_course_llm_coaching_recommendations.md` |
| V7 output format | `accc_llm_coaching_recommendations_v7.md` |
| Notebook | `06_5_llm_coaching_recommendations.ipynb` |
| Architecture (as-built) | `6.5_llm_integration_architecture.md` |
| Env template | `.env.example` |

## Module Objective

Turn explainability evidence into **human-readable coaching recommendations** via structured diagnosis + optional LLM (DeepSeek default).

## Pipeline (Phase A)

```text
SHAP + Pattern Engine
        ↓
root_cause.py + DiagnosisBuilder (V4–V6)
        ↓
lesson_synthesizer.py (V7)
        ↓
prompt_builder.py
        ↓
coaching_generate.py → LLMProvider | deterministic fallback
        ↓
coaching_validation.py (V7)
```

Phase B profile flow still uses `context_builder.py` (pre-V7 prompt shape).

## LLM Configuration

```python
@dataclass
class LLMSettings:
    provider: str   # "deepseek" | "gemini" | "openai_compatible"
    model: str      # e.g. "deepseek-chat"
    api_key: str    # DEEPSEEK_API_KEY / GEMINI_API_KEY / LLM_API_KEY
    base_url: str   # https://api.deepseek.com for DeepSeek
    temperature: float
```

## Dependencies

- Module 05/06: Human Pattern model + SHAP
- Module 02: encoded dataset + splits
- Optional: `google-genai` (Gemini only)
- `python-chess` (PGN + board diagnosis)

## Non-Goals (deferred)

- ChromaDB / RAG → Module 07
- V7 four-section format for **profile** Phase B
- Ollama provider in course package (architecture allows via OpenAI-compatible URL)
- Fixing upstream SQLite tactical tag quality (documented caveat)

## Testing Strategy

- Unit: providers, V7 payload, validation, diagnosis, RCA
- No live API in CI (`DryRunProvider`, HTTP mocks for DeepSeek)
- Manual: notebook + `.env` with real API key
