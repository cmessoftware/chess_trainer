# Cursor Prompt V7 — Insight-based Coaching

> **Status: implemented (Module 6.5, V7-lite)**  
> **Architecture:** [6.5_llm_integration_architecture.md](./6.5_llm_integration_architecture.md) §6  
> **Canonical spec:** [06_5-ai_chess_coach_course_llm_coaching_recommendations.md](./06_5-ai_chess_coach_course_llm_coaching_recommendations.md) §8  
>
> | V7 requirement | Implementation |
> |----------------|----------------|
> | Four report sections | `prompt_builder.py`, `deterministic_coaching.py` |
> | 2–3 main lessons | `lesson_synthesizer.py` → `lesson_clusters` |
> | Concise critical moments | Prompt + `coaching_validation.py` (entry count) |
> | Training plan (3 items) | Prompt rules + deterministic fallback |
> | Merge related moves into one lesson | `synthesize_lessons()` clustering by theme / `diagnosis_type` |
> | LLM synthesizes, does not invent diagnosis | Payload from `DiagnosisBuilder` + RCA |

## Context

The current pipeline already produces high-quality structured data.

Gemini is no longer responsible for discovering mistakes.

Instead, the configured **LLM provider** (DeepSeek or Gemini) should transform structured chess diagnosis into coaching that resembles a human chess coach.

The current move-by-move coaching is technically correct but too mechanical.

The objective is to explain the game, not the JSON.

---

# Philosophy

The report should teach ideas.

Not list mistakes.

Critical moves are evidence.

They are NOT the report structure.

A human coach usually says:

"I noticed three recurring problems."

and then cites moves as examples.

The report should follow that philosophy.

---

# Required Output

The report must have exactly four sections.

## 1. Short Summary

Two or three short paragraphs.

Describe:

- opening
- middlegame
- ending

without discussing individual moves yet.

---

## 2. Main Lessons

Identify the two or three most important lessons from the game.

Each lesson should:

- explain one recurring idea
- cite one or more critical moves as evidence
- explain why the mistake happened
- explain how to avoid it

Example:

### Lesson: Improving the opponent's pieces

Instead of:

Move 34.b4

write

During the middlegame you improved Black's bishop activity more than your own position.

Move 34.b4 illustrates this clearly.

The pawn advance looked active, but it gave Black better coordination.

Before advancing a wing pawn, always ask which enemy piece becomes stronger.

---

## 3. Critical Moments

Only now list the critical moves.

Keep this section concise.

For every move include only:

Player move

Opponent reply (if tactical)

One sentence explaining why the move matters.

No long paragraphs.

This section exists only as supporting evidence.

---

## 4. Training Plan

Produce three practical recommendations.

Each recommendation must correspond to one lesson from section 2.

Avoid generic advice.

Never write:

- calculate more
- improve tactics
- check checks captures threats

Instead produce concrete advice linked to the lesson.

---

# Important Rules

Critical moves are evidence.

Lessons are the main content.

Do not dedicate equal space to every critical move.

If several critical moves belong to the same underlying idea:

Merge them into a single lesson.

Examples:

6.N1c3

21.c4

↓

Lesson:

Allowing the opponent active counterplay.

-----------------------------------

34.b4

↓

Lesson:

Improving enemy pieces.

-----------------------------------

57.Kb8

↓

Lesson:

King activity in rook endings.

---

# Writing Style

The report must read like a coach talking after the game.

Not like an engine annotation.

Do not expose the internal structure.

Do not mention:

- SHAP
- features
- parquet
- model
- probability

Use natural Spanish.

Do not overuse chess jargon.

Do not explain every move.

Explain ideas.

---

# Data Usage

DiagnosisBuilder already provides:

- diagnosis_type
- theme
- issue
- consequence
- lesson
- supporting_features
- player_move
- opponent_reply

Use them as supporting evidence.

Do not simply rewrite them.

Synthesize them into broader lessons.

---

# Success Criteria

The final coaching should feel similar to what a strong chess coach would say after a training session.

The reader should finish remembering two or three strategic lessons from the game rather than six isolated mistakes.

The report should prioritize understanding over completeness.