# Module 6.5 — LLM coaching recommendations

Canonical spec: **[06_5-ai_chess_coach_course_llm_coaching_recommendations.md](./06_5-ai_chess_coach_course_llm_coaching_recommendations.md)** (includes v2 root-cause analysis)

V2 design notes: **[accc_llm_coaching_recommendations_V2.md](./accc_llm_coaching_recommendations_V2.md)**

Architecture reference: **[6.5_llm_integration_architecture.md](./6.5_llm_integration_architecture.md)**

Quick start (after implementation):

```powershell
cd docs/ai_chess_coach_course
jupyter lab 06_5_llm_coaching_recommendations.ipynb
```

Add `GEMINI_API_KEY=...` to the repo-root `.env` file (loaded automatically). **By default the notebook does not call Gemini** — it saves prompts to `artifacts/module06_5/`. To invoke the API, run the optional cells or set `LLM_AUTO_CALL=true`.

Optional dependency for live Gemini calls:

```powershell
pip install google-genai
```

Tests (no Gemini / no network):

```powershell
pytest tests/docs_courses/test_root_cause.py tests/docs_courses/test_human_brief.py tests/docs_courses/test_llm_coaching.py -q
```

