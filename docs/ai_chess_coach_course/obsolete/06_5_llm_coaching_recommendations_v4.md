# Cursor Prompt: Refactor Critical Move Generation into a Real Pattern Engine

## Context

The current coaching pipeline is working correctly:

```text
PGN
→ Stockfish
→ SHAP
→ Critical Move Detection
→ Gemini 2.5 Flash
```

The prompt is no longer the bottleneck.

Gemini follows the requested format correctly.

The weak point is the quality of the `critical_moves` payload.

Currently every critical move looks like:

```json
{
  "pattern": "tactical_oversight",
  "issue": "ceguera táctica",
  "lesson_hint": "Calcula jaques, capturas y amenazas."
}
```

This gives Gemini almost no information.

The result is repetitive coaching.

The objective is to move the diagnosis logic out of Gemini and into the application.

Gemini should become only a natural-language explainer.

---

# New Architecture

Current:

```text
Stockfish
        ↓
Critical Moves
        ↓
Gemini diagnoses
        ↓
Coaching
```

Target:

```text
Stockfish
        ↓
Critical Moves
        ↓
Pattern Engine
        ↓
Structured Diagnosis
        ↓
Gemini explains
```

---

# Goal

Implement a Pattern Engine capable of generating structured chess explanations before calling Gemini.

Gemini should never have to infer the tactical or strategic pattern.

It should only explain an already identified pattern.

---

# Step 1 — Expand CriticalMove

Replace the current model with:

```python
@dataclass
class CriticalMove:

    move_number: int

    player_move: str

    opponent_reply: str | None

    phase: str

    severity: str

    root_cause: bool

    pattern: str

    issue: str

    consequence: str

    lesson_hint: str

    best_move: str | None

    why_best_move: str | None

    tactical_motif: str | None

    strategic_theme: str | None

    material_change: str | None

    affected_piece: str | None

    opened_file: str | None

    opened_diagonal: str | None

    weak_square: str | None

    context_pgn: str
```

---

# Step 2 — Replace Generic Pattern Detection

Current:

```python
pattern = "tactical_oversight"
```

Replace with specialized detectors.

Possible patterns:

```python
UNDEFENDED_PIECE

UNDEFENDED_PAWN

LOOSE_PIECE_AFTER_PAWN_PUSH

OVERLOADED_DEFENDER

DEFLECTION

PIN

SKEWER

FORK

DISCOVERED_ATTACK

DISCOVERED_CHECK

OPEN_FILE

OPEN_DIAGONAL

WEAK_BACK_RANK

BACKWARD_PAWN

WEAK_SQUARE

BAD_BISHOP

PASSIVE_ROOK

ACTIVE_ROOK

KING_ACTIVITY

KING_OPPOSITION

PAWN_STRUCTURE

ISOLATED_PAWN

DOUBLE_PAWN

PASSED_PAWN

SPACE_GAIN

PIECE_ACTIVITY

PIECE_COORDINATION

SIMPLIFICATION_ERROR

ENDGAME_TECHNIQUE
```

One move may have multiple patterns.

---

# Step 3 — Detect Concrete Consequences

Instead of

```text
Tactical oversight
```

generate explanations like

```text
The pawn push left the e5 pawn undefended.
```

or

```text
The move opened the long diagonal for Black's bishop.
```

or

```text
The rook became passive defending the second rank.
```

The explanation should describe:

* what changed
* why it matters
* what Black exploited

---

# Step 4 — Detect Material Consequences

Populate automatically.

Example:

```json
{
    "material_change":"lost pawn"
}
```

or

```json
{
    "material_change":"lost exchange"
}
```

or

```json
{
    "material_change":"lost knight"
}
```

If no material was lost:

```json
{
    "material_change":"none"
}
```

---

# Step 5 — Detect Better Move

Whenever Stockfish provides a principal variation,

store

```json
{
    "best_move":"Re1",

    "why_best_move":
        "kept the e5 pawn defended while preserving central control"
}
```

This is much more instructive than saying

"calculate more carefully."

---

# Step 6 — Improve Lesson Generation

Never generate generic lessons.

Bad:

```text
Calculate checks, captures and threats.
```

Good:

```text
Before advancing a central pawn, verify which pieces stop being defended.
```

Bad:

```text
Improve tactical vision.
```

Good:

```text
When exchanging pieces, calculate the entire sequence until material becomes stable.
```

Bad:

```text
King safety.
```

Good:

```text
Do not activate your king before checking all forcing checks available to your opponent.
```

Lessons must be pattern-specific.

---

# Step 7 — Improve JSON Sent to Gemini

Instead of

```json
{
    "pattern":"tactical_oversight"
}
```

send

```json
{
    "player_move":"21.c4",

    "opponent_reply":"21...Rxe5",

    "pattern":"UNDEFENDED_PAWN",

    "issue":
        "The pawn advance left the advanced e5 pawn undefended.",

    "consequence":
        "Black won the pawn and activated the rook.",

    "material_change":
        "lost pawn",

    "lesson_hint":
        "Before advancing another pawn, verify that advanced pawns remain defended.",

    "best_move":
        "21.Re1",

    "why_best_move":
        "It preserved the pawn while maintaining pressure."
}
```

Gemini should explain this.

Not discover it.

---

# Step 8 — Separate Diagnosis from Explanation

Create two independent modules.

```text
DiagnosisEngine

↓

StructuredDiagnosis

↓

CoachingGenerator
```

Responsibilities:

DiagnosisEngine

* analyze position
* detect motifs
* classify mistakes
* detect root causes
* compute lessons

Gemini

* rewrite naturally
* connect ideas
* adapt tone
* avoid repetition

Diagnosis must never depend on the LLM.

---

# Step 9 — Design for Extensibility

Pattern detectors should implement a common interface.

Example:

```python
class PatternDetector(ABC):

    def detect(
        self,
        before_position,
        after_position,
        stockfish_analysis
    ) -> PatternMatch | None:
        ...
```

Examples:

```text
LoosePieceDetector

OpenFileDetector

WeakSquareDetector

ForkDetector

PinnedPieceDetector

KingActivityDetector

PawnStructureDetector

PieceActivityDetector

EndgameDetector
```

The Pattern Engine simply executes all detectors and aggregates the matches.

---

# Success Criteria

A critical move should no longer produce:

```json
{
    "pattern":"tactical_oversight",
    "issue":"ceguera táctica"
}
```

Instead it should generate something like:

```json
{
    "player_move":"14.e5",

    "pattern":"LOOSE_PIECE_AFTER_PAWN_PUSH",

    "issue":
        "The central pawn advance removed a defender from the knight on d5.",

    "consequence":
        "A forcing exchange sequence allowed Black to win a full piece.",

    "material_change":"lost knight",

    "best_move":"14.Re1",

    "why_best_move":
        "Maintained support of the knight while keeping central pressure.",

    "lesson_hint":
        "Before pushing a central pawn, identify which pieces stop being defended."
}
```

The application should become responsible for chess understanding.

Gemini should only transform structured chess knowledge into fluent coaching for the player.
