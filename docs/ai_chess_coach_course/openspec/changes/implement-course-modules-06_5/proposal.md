# Change Proposal: implement-course-modules-06_5

## Why

The course needs a **first complete coaching arc** after SHAP (Module 06) without waiting for RAG (07) or local LLM stacks (08). Module 6.5 closes the loop:

**Human Pattern model → SHAP → Pattern Engine → Gemini 2.5 Flash coaching text**

using the provider-agnostic design in `6.5_llm_integration_architecture.md`.

## What Changes

- Add canonical spec: `06_5-ai_chess_coach_course_llm_coaching_recommendations.md`
- Implement course-local packages: `llm/` (provider abstraction + Gemini) and `coaching/` (pattern → context → prompt)
- Deliver notebook: `06_5_llm_coaching_recommendations.ipynb`
- Persist sample artifacts under `artifacts/module06_5/`
- Add tests for factory, context schema, and prompt guardrails

## Out of Scope

- Vector DB / RAG (Module 07)
- Ollama / local models (Module 08)
- Full pattern catalog from `04-ai_chess_coach_course_llm_recommendationsf_from_shap_+_pattern_engine.md` (defer expansions to 07–08)
- Production API / UI (Modules 12–13)
- Committing API keys or calling LLM in CI without mocks

## Success Criteria

- Student can run notebook with `GEMINI_API_KEY` and receive grounded coaching text from structured context
- Without API key, notebook still demonstrates pipeline through prompt + dry-run
- No vendor SDK imports outside `llm/gemini_provider.py`
