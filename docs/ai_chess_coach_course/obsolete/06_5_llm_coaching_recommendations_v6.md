# Cursor Prompt: Refactor DiagnosisBuilder to Support Multiple Coaching Styles

## Context

The current coaching pipeline is producing technically correct but overly uniform feedback.

Current flow:

```text
Parquet
    ↓
Critical Move Detection
    ↓
DiagnosisBuilder
    ↓
Gemini
```

The prompt is no longer the bottleneck.

Gemini faithfully rewrites the structured data it receives.

The problem is that DiagnosisBuilder currently reduces almost every mistake to:

```text
Player move
↓

Opponent found a forcing reply

↓

"Tactical oversight"

↓

"Calculate forcing lines."
```

This works for tactical mistakes but produces poor coaching for:

* opening mistakes
* positional mistakes
* strategic mistakes
* endgame mistakes
* simplification mistakes

The DiagnosisBuilder must classify the nature of the mistake before generating the explanation.

---

# Goal

Replace the current "one size fits all" diagnosis with multiple diagnosis styles.

The application—not Gemini—must determine how each mistake should be explained.

---

# Step 1 — Add diagnosis_type

Extend CriticalMove:

```python
diagnosis_type: Literal[
    "tactical",
    "positional",
    "opening",
    "endgame",
    "simplification",
    "strategic"
]
```

DiagnosisBuilder is responsible for assigning this field.

Gemini should never infer it.

---

# Step 2 — Different Templates Per Diagnosis Type

## Tactical

Use only when tactical tags indicate:

* fork
* pin
* skewer
* discovered attack
* hanging piece
* remove defender
* overloaded piece
* etc.

Template:

```text
Player decision

↓

Opponent tactical punishment

↓

Material or positional consequence

↓

Concrete tactical lesson
```

Example:

```text
21.c4

↓

21...Rxe5

↓

Lost pawn

↓

Before advancing a pawn, verify that advanced pawns remain defended.
```

---

## Positional

Do NOT emphasize forcing replies.

Instead explain:

* what changed in the position
* which piece improved
* which piece became worse
* how the plan changed

Template:

```text
Decision

↓

Positional change

↓

Long-term consequence

↓

Strategic lesson
```

Example:

```text
34.b4

↓

Allowed the bishop to become much more active.

↓

White's pieces became passive.

↓

Before advancing a wing pawn, verify whether it improves an enemy piece.
```

---

## Opening

Focus on:

* development
* center
* initiative
* coordination

Never describe it as merely a tactical oversight.

Example:

```text
6.N1c3

↓

Allowed ...Nd4 under favorable conditions.

↓

Black equalized comfortably and obtained an active center.

↓

In the opening, prioritize harmonious development over short-term activity.
```

---

## Endgame

Focus on:

* king activity
* pawn races
* opposition
* rook activity
* conversion

Do not force tactical explanations.

Example:

```text
57.Kb8

↓

The king entered a restricted zone.

↓

Black coordinated king and rook more easily.

↓

In rook endings, preserve king mobility before seeking activity.
```

---

## Simplification

Focus on exchanges.

Template:

```text
Exchange decision

↓

Resulting endgame

↓

Why the ending favored the opponent

↓

Lesson
```

---

# Step 3 — Improve Tactical Tag Interpretation

Current:

```python
pattern = tactical_oversight
```

This is too generic.

Interpret combinations.

Examples:

```text
fork
+
piece_lost
```

↓

```python
theme="Fork winning material"
```

---

```text
pin
+
low_self_mobility
```

↓

```python
theme="Pinned defender"
```

---

```text
remove_defender
+
bishop_attack
```

↓

```python
theme="Deflection"
```

Avoid using:

```text
tactical_oversight
```

unless no better explanation exists.

---

# Step 4 — Use Supporting Features Correctly

Current payload already contains:

```python
supporting_features
```

Example:

```text
Black pieces became active

Reduced center control

Reduced mobility
```

Do not merely append these.

Instead integrate them naturally.

Example:

Bad:

```text
Supporting feature:
Black pieces became active.
```

Good:

```text
After this decision, Black's bishop became much more active,
which restricted the movement of your rooks.
```

---

# Step 5 — Better Lesson Generation

LessonGenerator should depend on diagnosis_type.

Example:

Tactical:

```text
Before moving, identify forcing tactical replies.
```

Opening:

```text
Do not allow the opponent to gain central activity while completing development.
```

Positional:

```text
Before advancing a pawn, ask which enemy piece becomes stronger.
```

Endgame:

```text
King activity is often more important than gaining a single pawn.
```

Simplification:

```text
Before exchanging pieces, evaluate whether the resulting ending favors your opponent.
```

No generic lessons.

---

# Step 6 — Allow Variable Coaching Structure

Current prompt forces:

```text
Player move

Opponent reply

Cause

Consequence

Lesson
```

Instead DiagnosisBuilder should emit:

```python
sections = [
    decision,
    positional_change,
    tactical_punishment (optional),
    consequence,
    lesson
]
```

`tactical_punishment` should only exist for tactical mistakes.

This allows richer coaching.

---

# Step 7 — Do Not Overuse opponent_reply

Current implementation assumes every mistake has:

```text
Opponent punishment
```

That is incorrect.

For positional mistakes:

Explain the positional deterioration.

For opening mistakes:

Explain development and initiative.

For endgames:

Explain coordination and king activity.

Only tactical mistakes require a forcing reply.

---

# Step 8 — Success Criteria

Current coaching:

> You missed a tactical response.

Target coaching:

Opening

> Your development allowed Black to activate the knight with ...Nd4 while obtaining a healthy central structure.

Positional

> The pawn advance improved the opponent's bishop more than your own position, leaving your pieces increasingly passive.

Endgame

> The king's route reduced your available squares and allowed Black to coordinate the king and rook into a winning position.

Tactical

> The move left a pawn undefended, allowing an immediate tactical win.

The coaching should resemble the explanations of a human coach rather than a list of tactical punishments.

DiagnosisBuilder should decide **what kind of chess mistake occurred**.

Gemini should only transform that structured diagnosis into fluent, personalized coaching.
