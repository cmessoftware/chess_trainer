# Design: implement-course-modules-06_5

## Design Goals

- Deliver the **minimum viable coaching pipeline** for the first course version (Modules 01–06.5).
- Keep LLM **provider-agnostic**; Gemini 2.5 Flash is the only v1 implementation.
- Never expose raw SHAP arrays or engine features to the LLM.
- Reuse Module 05/06 artifacts without retraining.

## Canonical Artifacts

| Artifact | Path |
|----------|------|
| Spec | `06_5-ai_chess_coach_course_llm_coaching_recommendations.md` |
| Notebook | `06_5_llm_coaching_recommendations.ipynb` |
| Architecture reference | `6.5_llm_integration_architecture.md` |

## Module Objective

Turn explainability evidence into **human-readable coaching recommendations** via structured context + Gemini 2.5 Flash.

## Pipeline

```text
artifacts/module05/best_human_run.json
artifacts/module06/* (SHAP)
        ↓
coaching/pattern_engine.py
        ↓
coaching/context_builder.py  → sample_context.json
        ↓
coaching/prompt_builder.py
        ↓
llm/provider_factory.py → GeminiProvider
        ↓
sample_recommendation.txt
```

## LLM Configuration

```python
@dataclass
class LLMSettings:
    provider: str   # "gemini"
    model: str      # "gemini-2.5-flash"
    api_key: str    # os.getenv("GEMINI_API_KEY")
```

## Dependencies

- Module 05: `best_human_run.json`
- Module 06: SHAP outputs + Human Pattern model artifacts
- Module 02: encoded dataset for sample rows
- Python package: `google-genai`

## Non-Goals (deferred)

- ChromaDB / LangChain RAG → Module 07
- Multi-game player profile aggregator (50+ games) → simplified sample window in 6.5
- DeepSeek / OpenAI / LocalProvider → future; factory stub only

## Testing Strategy

- Unit: `create_provider`, context JSON schema, prompt includes context block
- Mock: `LLMProvider.generate` in tests (no live API in CI)
- Optional manual: notebook with real `GEMINI_API_KEY`
