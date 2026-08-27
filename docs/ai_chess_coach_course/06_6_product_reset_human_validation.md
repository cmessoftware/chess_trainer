# Module 6.6 — Product Reset & Human Validation

> **Objective:** Understand why an LLM-based system can generate technically plausible yet pedagogically incorrect recommendations, and how to redefine the product by introducing human validation before moving on to RAG and agentic architectures.

---

# Introduction

Up to Module 6.5, we built a complete end-to-end pipeline capable of:

- extracting features from PGN files
- training machine learning models
- explaining predictions using SHAP
- detecting recurring patterns
- building structured diagnoses
- generating coaching reports with LLMs

From a technological perspective, the system worked correctly.

However, during testing an unexpected limitation emerged.

The problem was no longer generating explanations.

The real problem became determining whether those explanations actually helped a player improve.

This discovery fundamentally changes the direction of the project.

---

# What Has Been Built So Far

Current pipeline:

```text
PGN
    ↓
Feature Extraction
    ↓
Machine Learning
    ↓
SHAP
    ↓
Pattern Engine
    ↓
Diagnosis Builder
    ↓
LLM
    ↓
Coaching Report
```

All of these components remain valid.

None of them are discarded.

---

# The Bottleneck

Stockfish answers:

> What is the best move?

The ML model answers:

> What type of mistake did the player make?

SHAP answers:

> Which features contributed to this prediction?

The Pattern Engine answers:

> Which recurring patterns can be detected?

The LLM answers:

> How should the explanation be written?

However, none of these components answer the most important question.

> What is the most useful training recommendation for this player?

---

# Paradigm Shift

The original goal was to build a system capable of explaining games.

The new goal is to build a system capable of diagnosing players.

The focus shifts away from an individual position.

The new focus becomes the player's entire game history.

Previous approach:

```text
Position
      ↓
Chess Engine
      ↓
LLM
      ↓
Explanation
```

New approach:

```text
Thousands of Games
         ↓
Pattern Extraction
         ↓
Player Diagnosis
         ↓
Personalized Training Plan
```

---

# What Is Missing?

The missing component is not more AI.

The missing component is domain expertise.

The system must learn how an experienced chess coach reasons.

For example, a coach may identify:

- poor advantage conversion
- overestimating attacking chances
- exchanging pieces at the wrong moment
- avoiding endgames
- playing too quickly in critical positions

These conclusions do not come directly from the chess engine.

They come from years of coaching experience.

---

# Human in the Loop

Starting with this module, a new stage is introduced.

```text
Diagnosis Builder
        ↓
Structured Diagnosis
        ↓
Human Coach
        ↓
Corrections
        ↓
Validated Dataset
```

The objective is no longer to generate recommendations automatically.

The objective is to build a dataset of recommendations validated by human experts.

---

# Validation Dataset

Every diagnosis can be manually reviewed.

Example:

Automatic diagnosis:

```json
{
  "theme": "isolated pawn",
  "priority": "medium",
  "recommendation": "Study IQP positions"
}
```

Human validation:

```json
{
  "correct": true,
  "priority_correct": false,
  "better_priority": "high",
  "coach_comment": "The real issue is poor piece coordination."
}
```

This validated dataset becomes the new ground truth.

---

# New Architecture

Previous architecture:

```text
Machine Learning
       ↓
Diagnosis
       ↓
LLM
       ↓
Final Recommendation
```

New architecture:

```text
Machine Learning
       ↓
Diagnosis
       ↓
Human Validation Dataset
       ↓
Recommendation Engine
       ↓
LLM
       ↓
Natural Language Report
```

The LLM no longer makes decisions.

The LLM's role is limited to communicating validated recommendations in natural language.

---

# Learning Objectives

By the end of this module, students will be able to:

- recognize when a problem is no longer technological but domain-related
- understand the limitations of LLM-generated recommendations
- separate evidence from interpretation
- integrate human experts into an AI pipeline
- build datasets through expert validation
- redesign an AI product using evidence gathered during development

---

# Proposed MVP

New MVP

Input:

- player's game history

Output:

Player diagnostic report

Example:

Strengths

- tactical calculation
- initiative

Weaknesses

- endgames
- isolated pawn positions
- unnecessary simplifications

Priority study topics

- open files
- rook endgames
- converting winning positions

The goal of the MVP is no longer to explain individual moves.

Its purpose is to generate a useful player diagnosis.

---

# Future Evolution

Once the diagnostic process has been validated, the project can safely evolve by incorporating:

- Retrieval-Augmented Generation (RAG)
- annotated chess books
- annotated master games
- autonomous agents
- long-term memory
- automated planning

However, these technologies should only be introduced after demonstrating that the diagnosis itself is reliable.

---

# Case Study

This module represents a real-world AI Engineering case study.

During development it became clear that:

- the data pipeline worked
- the ML models worked
- SHAP explanations worked
- the LLM produced convincing explanations

Nevertheless,

there was still insufficient evidence to conclude that those recommendations actually improved a player's training process.

This realization led to a change in the product strategy.

Rather than representing a failure, it illustrates how AI products evolve when the primary challenge shifts from technology to domain expertise.

---

# Coherence with Modules 0–6.5

This module **does not replace** the 6.5 pipeline; it **audits and gates** it.

| Topic | Module 6.5 (implemented) | Module 6.6 (this doc) | Relationship |
|-------|--------------------------|------------------------|--------------|
| **Evidence layer** | Features, SHAP, Pattern Engine, RCA, `DiagnosisBuilder` | Same stack; **candidate evidence** | Reused |
| **LLM role (V7)** | Narrates V7 report from `lesson_clusters` + `critical_moves` | LLM = **language**; priorities from rules + human gold | Product shift: audit whether synthesis is **pedagogically true** |
| **Scope** | Phase A: one game; Phase B: small profile sample | Longitudinal MVP (many games) + human case review | Extends 6.5 Phase B |
| **Known failure** | Noisy tags → convincing wrong text (e.g. false tactical themes) | `coach_review` + grounding metrics | Explains 6.5 “works” technically but fails coaching |
| **Validation** | `coaching_validation.py` (sections, moves) | Coach correctness, relevance, priority | **Syntactic** vs **domain** validation |
| **Modules 7–10** | Deferred | **Gate:** no RAG/agents until validation criteria met | Roadmap exit criterion |

**How to reconcile V7 with Human-in-the-Loop:** In 6.5 the LLM still **drafts** the report for learning and demos. In 6.6 those drafts become **review candidates**; validated labels become ground truth for a future recommendation engine. The LLM does not need to be removed from 6.5 — it must be **measured and corrected**.

Extended checklist (hypotheses, metrics, abstention, MVP A/B): [00-ai_enginner_course_roadmap.md](./00-ai_enginner_course_roadmap.md) § Module 6.6.

---

# Course notebook (Module 6.6)

| Item | Path |
|------|------|
| Notebook | `06_6_product_reset_human_validation.ipynb` |
| Generator | `_gen_human_validation_nb.py` |

```powershell
python docs/ai_chess_coach_course/_gen_human_validation_nb.py
```

### Prerequisites

- Module **6.5** Phase A executed once, or existing `artifacts/module06_5/debug/phase_a/full_llm_payload.json`.
- Optional: LLM report in debug folder for experiment **C**.
- Human reviewer for cells marked **Human in the loop**.

### Notebook sections

1. **Setup** — course paths; `artifacts/module06_6/`.
2. **Load review case** — from 6.5 debug artifacts **or** rebuild with `generate_single_game_coaching(..., invoke_llm=False)`.
3. **Evidence panel** — show `critical_moves`, `lesson_clusters`, `context_pgn` (no new LLM call).
4. **Automatic pre-checks** — `validate_critical_moves`, format validation on any saved LLM text, flag generic phrases.
5. **Human in the loop** — reviewer completes `coach_review` per moment/lesson (schema aligned with roadmap §6.6.3).
6. **Persist** — append to `validated_cases.jsonl`; export `review_pack_{game_id}.json` for external coaches.
7. **Reliability snapshot** — simple aggregates (agreement, harmful count, abstention candidates).
8. **Product reset memo** — draft `product_reset_decision.md` (continue / limit / drop recommendation types).
9. **Gate to Module 7** — checklist vs exit criteria below.

### Experiments A–D (same cases)

| Variant | Source |
|---------|--------|
| A | Engine line + eval (manual / future Stockfish hook) |
| B | `render_deterministic_coaching()` |
| C | 6.5 LLM output |
| D | C + human `coach_review` as gold |

### Artifacts

```text
artifacts/module06_6/
├── review_pack_{game_id}.json
├── validated_cases.jsonl
├── reliability_summary.json
└── product_reset_decision.md
```

---

# Expected Outcome

After completing this module, students should understand that:

- building a good model does not necessarily mean building a good product;
- a technically correct explanation is not necessarily a useful recommendation;
- human validation may become the most valuable component of an AI system;
- AI Engineering involves iterating on product hypotheses, not only on machine learning models.

At this point, the project is ready to continue with RAG, agentic architectures, and production-oriented modules, but now on top of a foundation validated by domain experts.