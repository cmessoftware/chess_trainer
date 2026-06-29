# Tasks: implement-course-modules-06_5

## 1. Specification & docs

- [x] Canonical spec: `06_5-ai_chess_coach_course_llm_coaching_recommendations.md`
- [x] Short pointer: `ai_chess_coach_course_llm_coaching_recommendations.md` → link to canonical spec
- [x] Update roadmap Module 6.5 entry in `00-ai_enginner_course_roadmap.md`

## 2. LLM provider layer (`llm/`)

- [x] `llm/base.py` — `LLMProvider` ABC
- [x] `llm/settings.py` — `LLMSettings` from `GEMINI_API_KEY`
- [x] `llm/gemini_provider.py` — `google-genai`, model `gemini-2.5-flash`
- [x] `llm/provider_factory.py` — `create_provider(settings)`
- [x] `llm/__init__.py` exports

## 3. Coaching pipeline (`coaching/`)

- [x] `coaching/pattern_engine.py` — v1 rule catalog (≥5 patterns)
- [x] `coaching/context_builder.py` — JSON context (no raw SHAP)
- [x] `coaching/prompt_builder.py` — coaching prompt template
- [x] `coaching/__init__.py` exports

## 4. Notebook & artifacts

- [x] Create `06_5_llm_coaching_recommendations.ipynb`
- [x] Wire Module 05/06 artifact paths
- [x] Dry-run path when `GEMINI_API_KEY` missing
- [x] Write `artifacts/module06_5/sample_context.json`
- [x] Write `artifacts/module06_5/sample_recommendation.txt`

## 5. Validation

- [x] `tests/docs_courses/test_llm_coaching.py` — factory, context, prompt (mocked LLM)
- [x] Document `google-genai` install in notebook / course README
- [ ] Verify top-to-bottom notebook run with API key (manual)
