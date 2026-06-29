# Cursor Prompt: Implement a Diagnosis Builder Using Tactical Tags + SHAP + Features

## Context

The current coaching pipeline is:

```text
PGN
    ↓
Stockfish Analysis
    ↓
Feature Extraction
    ↓
Tactical Tag Detection
    ↓
Parquet
    ↓
ML Error Prediction
    ↓
Gemini Coaching
```

Important:

At coaching time **Stockfish is NOT available**.

The coaching stage only has access to:

* PGN
* Feature vector (parquet)
* SHAP explanation
* Tactical tags generated previously
* Predicted error label
* Phase of game
* Move information

Therefore, the application must perform all chess diagnosis before calling Gemini.

Gemini should explain, not diagnose.

---

# Objective

Create a new module called:

```text
DiagnosisBuilder
```

Its responsibility is to convert:

```text
Features
+
Tactical Tags
+
SHAP
+
Critical Move
```

into a structured chess diagnosis.

Gemini should receive that diagnosis instead of trying to infer it.

---

# Architecture

Current:

```text
critical_moves
        ↓
Gemini
```

Target:

```text
critical_moves
        │
        ├── Tactical Interpreter
        ├── Feature Interpreter
        ├── SHAP Interpreter
        │
        ▼
Structured Diagnosis
        ▼
Gemini
```

---

# 1. Tactical Interpreter

The parquet already contains tactical tags generated from Stockfish.

Those tags should become the primary source of chess understanding.

Example tags:

```text
fork
pin
skewer
discovered_attack
discovered_check
double_attack
mate
mate_threat
back_rank
passed_pawn
promotion
hanging_piece
piece_lost
exchange_lost
queen_lost
rook_trapped
bishop_trapped
knight_trapped
remove_defender
overloaded_piece
interference
zwischenzug
perpetual_check
```

Create a TacticalInterpreter that converts tag combinations into chess concepts.

Example:

```python
fork
+
piece_lost
```

↓

```python
theme="Fork"

issue="A fork won material."

lesson="Before moving, verify whether one enemy piece can attack two targets simultaneously."
```

---

Another example:

```python
pin
+
hanging_piece
```

↓

```python
theme="Pin"

issue="The pinned piece could not defend another piece."

lesson="When a piece is pinned, re-evaluate every defender in the position."
```

---

# 2. Feature Interpreter

Interpret chess features.

Examples:

```text
center_control

self_mobility

opponent_mobility

material_total

num_pieces

king_attack_units

development

space

pawn_structure

piece_activity
```

Never expose raw feature names.

Translate them into chess language.

Example:

Instead of

```text
self_mobility = low
```

produce

```text
Your pieces had very few active squares.
```

---

Instead of

```text
opponent_mobility = high
```

produce

```text
Black's pieces became significantly more active.
```

---

# 3. SHAP Interpreter

Use SHAP only as supporting evidence.

Never explain SHAP.

Instead:

Positive SHAP

↓

"What contributed most to the mistake."

Negative SHAP

↓

"What aspects of the position remained healthy."

Example:

```text
center_control

+

high SHAP impact
```

↓

```text
The loss of central control played an important role in this mistake.
```

---

# 4. Diagnosis Object

Replace generic strings like

```json
{
    "pattern":"tactical_oversight"
}
```

with

```json
{
    "theme":"Fork",

    "issue":"A fork won material.",

    "supporting_features":[
        "opponent piece activity",
        "reduced mobility"
    ],

    "consequence":
        "Black gained material and activated the initiative.",

    "lesson":
        "Before every move, identify squares where one enemy piece attacks multiple targets."
}
```

---

# 5. Merge Tactical + Positional Concepts

If tactical tags exist:

They take priority.

Features provide context.

Example:

```text
Tags

fork

piece_lost

Features

opponent_mobility ↑
```

↓

Diagnosis

```text
The fork won material.

After gaining material, Black's pieces became much more active.
```

---

Example:

```text
Tags

pin

Features

self_mobility ↓
```

↓

Diagnosis

```text
The pin reduced the mobility of your pieces, making defense more difficult.
```

---

# 6. Lesson Generator

Remove generic lessons.

Current:

```text
Calculate checks, captures and threats.
```

Replace with pattern-specific lessons.

Examples:

Fork

↓

```text
Before moving, identify squares from which one piece attacks multiple targets.
```

Pin

↓

```text
Pinned pieces often stop defending other pieces. Verify the entire defensive chain.
```

Skewer

↓

```text
Keep high-value pieces out of the same line as lower-value pieces.
```

Hanging Piece

↓

```text
Before every move, verify that every piece remains defended.
```

Back Rank

↓

```text
Create escape squares before activating your rooks.
```

Passed Pawn

↓

```text
Passed pawns become stronger when supported by active pieces.
```

Each tactical theme should have its own teaching message.

---

# 7. Gemini Context

Gemini should receive something like:

```json
{
    "player_move":"21.c4",

    "theme":"Hanging Pawn",

    "issue":
        "The move left the advanced e5 pawn undefended.",

    "supporting_features":[
        "loss of center control",
        "opponent activity increased"
    ],

    "consequence":
        "Black won the pawn and activated the rook.",

    "lesson":
        "Before advancing another pawn, verify that advanced pawns remain defended."
}
```

Gemini should never infer the tactical theme.

It should explain it naturally.

---

# 8. Design

Create:

```text
DiagnosisBuilder
```

which internally uses:

```text
TacticalInterpreter

FeatureInterpreter

SHAPInterpreter

LessonGenerator
```

Each component should be independently testable.

---

# 9. Success Criteria

The coaching should evolve from:

> "There was a tactical oversight."

to:

> "The move allowed a fork that won material. After that sequence, Black's pieces became much more active, making the position difficult to defend. Before committing a move, identify whether a single enemy piece can attack two important targets."

The system should no longer rely on Gemini to discover chess ideas.

It should provide Gemini with structured chess knowledge generated from the tactical tags and the existing feature set stored in the parquet.
