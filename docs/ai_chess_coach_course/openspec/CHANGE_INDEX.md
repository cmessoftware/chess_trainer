# OpenSpec Change Index - AI Chess Coach Course

This index maps each course module to one dedicated OpenSpec change.

## How to Use

Run commands from `docs/ai_chess_coach_course`:

```powershell
openspec list
openspec validate <change-name>
openspec show <change-name> --type change --no-interactive
```

## Phase 1 - Notebooks and Helper Scripts (No UI, No Agentic Orchestration)

- Module 03 -> `implement-course-modules-03`
  - Focus: feature analysis baseline notebook
- Module 04 -> `implement-course-modules-04`
  - Focus: ML baseline training
- Module 05 -> `implement-course-modules-05`
  - Focus: MLflow experiment tracking
- Module 06 -> `implement-course-modules-06`
  - Focus: SHAP explainability
- Module 07 -> `implement-course-modules-07`
  - Focus: RAG foundation
- Module 08 -> `implement-course-modules-08`
  - Focus: LLM explanations
- Module 09 -> `implement-course-modules-09`
  - Focus: consistency and hallucination tests

## Phase 2 - Agentic Architecture

- Module 10 -> `implement-course-modules-10`
  - Focus: planner-executor-critic-memory orchestration
- Module 11 -> `implement-course-modules-11`
  - Focus: capstone backend integration

## Phase 3 - MVP and Production Bridge

- Module 12 -> `implement-course-modules-12`
  - Focus: MVP UI + FastAPI demo
- Module 13 -> `implement-course-modules-13`
  - Focus: React + Vite production bridge

## Suggested Execution Order

1. `implement-course-modules-04`
2. `implement-course-modules-05`
3. `implement-course-modules-06`
4. `implement-course-modules-07`
5. `implement-course-modules-08`
6. `implement-course-modules-09`
7. `implement-course-modules-10`
8. `implement-course-modules-11`
9. `implement-course-modules-12`
10. `implement-course-modules-13`

Module 03 is already implemented and validated as the starting point.
