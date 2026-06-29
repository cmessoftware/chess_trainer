# Phase 04 - Implement LLM Coaching Recommendations from SHAP + Pattern Engine

> **Module 6.5 MVP spec (Gemini 2.5 Flash):** [06_5-ai_chess_coach_course_llm_coaching_recommendations.md](./06_5-ai_chess_coach_course_llm_coaching_recommendations.md) — implements a **minimal** pattern engine and coaching pipeline.  
> **This document** retains the **full** pattern catalog and player-aggregator design for Modules 07–08.

## Context

The Human Pattern Model has been successfully trained.

The latest SHAP analysis shows:

Top global features:

- num_pieces
- material_total
- opening
- king_safety
- player_elo
- self_mobility
- move_number
- branching_factor
- has_castling_rights
- opponent_mobility

Important observations:

1. Leakage appears to be well controlled.
2. The model relies primarily on human-understandable chess features.
3. move_number may be acting as a proxy for game phase.
4. king_safety appears consistently important.
5. player_elo provides meaningful signal.
6. time_control_bucket contributes less than expected.
7. The model is suitable for coaching-oriented explanations.

The next objective is NOT improving prediction accuracy.

The next objective is generating personalized coaching recommendations using:

```text
ML Prediction
+
SHAP Explanation
+
Pattern Engine
+
Player History
+
LLM
```

---

# Goal

Implement the first version of the ChessTrainer Coaching Recommendation Pipeline.

The output should be educational recommendations such as:

```text
You frequently leave pieces undefended.

In your last 50 games, this pattern appeared 18 times.

Focus on performing a final piece safety check before every tactical sequence.
```

instead of raw ML explanations such as:

```text
king_safety = +0.42
```

---

# High-Level Architecture

Implement:

```text
XGBoost
   ↓
SHAP
   ↓
Pattern Engine
   ↓
Player Pattern Aggregator
   ↓
Recommendation Context Builder
   ↓
LLM
   ↓
Coaching Advice
```

---

# Phase 1: Pattern Engine

Create a new module:

```text
chess_trainer/patterns/pattern_engine.py
```

Purpose:

Translate features and SHAP contributions into chess concepts.

---

## Pattern Schema

Define:

```python
@dataclass
class PatternObservation:
    pattern_name: str
    confidence: float
    source_features: list[str]
    shap_impact: float
    severity: str
```

---

## Initial Pattern Catalog

Implement at least:

```text
unsafe_king
uncastled_king
high_tactical_complexity
opponent_activity
cramped_position
low_mobility
opening_risk
late_game_accuracy
```

Example:

```python
if king_safety > threshold:
    pattern = "unsafe_king"
```

Example:

```python
if has_castling_rights == 0 and move_number < 15:
    pattern = "uncastled_king"
```

Example:

```python
if branching_factor > threshold:
    pattern = "high_tactical_complexity"
```

---

# Phase 2: SHAP Mapping

Create:

```text
chess_trainer/explainability/shap_pattern_mapper.py
```

Purpose:

Convert SHAP output into PatternObservations.

Input:

```python
{
    "feature": "king_safety",
    "shap": 0.42
}
```

Output:

```python
PatternObservation(
    pattern_name="unsafe_king",
    confidence=0.88,
    shap_impact=0.42
)
```

---

# Phase 3: Player Pattern Database

Create:

```text
player_patterns
```

table.

Suggested columns:

```sql
player_name
pattern_name
occurrences
avg_shap_impact
first_seen
last_seen
```

Purpose:

Track recurring weaknesses.

---

# Phase 4: Pattern Aggregation

Create:

```text
analyze_player_patterns.py
```

Purpose:

Aggregate patterns across all analyzed games.

Output example:

```json
{
  "unsafe_king": {
    "count": 74,
    "avg_impact": 0.43
  },
  "uncastled_king": {
    "count": 31,
    "avg_impact": 0.28
  }
}
```

---

# Phase 5: Recommendation Context Builder

Create:

```text
recommendation_context_builder.py
```

Input:

```json
{
  "player": "cmess1315",
  "elo": 1450,
  "top_patterns": [
    "unsafe_king",
    "uncastled_king",
    "high_tactical_complexity"
  ]
}
```

Output:

```json
{
  "player_elo": 1450,
  "dominant_patterns": [...],
  "recent_trends": [...],
  "top_openings": [...],
  "error_distribution": {...}
}
```

Purpose:

Build a compact structured payload for the LLM.

---

# Phase 6: Recommendation Prompt Generator

Create:

```text
recommendation_prompt_builder.py
```

Generate prompts such as:

```text
You are a chess coach.

Player rating: 1450

Most frequent patterns:

1. unsafe_king (74 occurrences)
2. uncastled_king (31 occurrences)
3. high_tactical_complexity (28 occurrences)

Recent trend:
unsafe_king increasing.

Generate:

- Key weakness
- Why it matters
- What to study
- Training recommendation
- Example exercise type

Keep advice practical and educational.
```

---

# Phase 7: Recommendation Output Schema

Define:

```python
@dataclass
class CoachingRecommendation:
    title: str
    pattern_name: str
    explanation: str
    study_recommendation: str
    exercise_recommendation: str
    confidence: float
```

---

# Phase 8: Trend Analysis

Implement:

```text
pattern_trends.py
```

Detect:

```text
improving
stable
worsening
```

Example:

```text
unsafe_king:
40 → 31 → 21
```

Trend:

```text
improving
```

---

# Phase 9: Explainability Dashboard Data

Generate JSON output:

```json
{
  "top_patterns": [...],
  "recent_patterns": [...],
  "improving_patterns": [...],
  "worsening_patterns": [...],
  "recommendations": [...]
}
```

This will later feed Streamlit or React dashboards.

---

# Important Design Rules

## Rule 1

SHAP explains the model.

SHAP does NOT explain chess.

Pattern Engine translates model explanations into chess concepts.

---

## Rule 2

LLM must never receive raw feature vectors.

LLM receives:

```json
{
  "patterns": [...],
  "player_profile": {...},
  "trends": {...}
}
```

only.

---

## Rule 3

Recommendations must be based on recurring patterns.

Avoid single-game advice.

Prefer:

```text
This issue appeared 17 times.
```

instead of:

```text
Move 24 was bad.
```

---

## Rule 4

The primary objective is coaching value.

Not prediction accuracy.

---

# Deliverables

Implement:

```text
pattern_engine.py
shap_pattern_mapper.py
player_patterns table
analyze_player_patterns.py
pattern_trends.py
recommendation_context_builder.py
recommendation_prompt_builder.py
coaching_recommendation.py
```

Generate clean Python code, typed where practical, aligned with the current ChessTrainer architecture, and ready for future integration with GPT/Qwen-based coaching modules.