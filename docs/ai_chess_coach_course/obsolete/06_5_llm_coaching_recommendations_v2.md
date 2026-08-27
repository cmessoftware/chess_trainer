# Cursor Prompt: Fix Critical Move Extraction (Root Cause vs Punishment)

## Context

The current coaching pipeline is:

```
PGN
→ Stockfish Analysis
→ SHAP Explanation
→ Pattern Detection
→ Critical Move Selection
→ Gemini 2.5 Flash Coaching
```

The coaching quality is limited because `critical_moves` currently contains the opponent's punishment move instead of the player's mistake.

Example:

Current output:

```json
{
  "move_number": 21,
  "move": "21...Rxe5",
  "severity": "blunder"
}
```

Gemini correctly assumes that `21...Rxe5` is the move to explain, even though it is Black's move.

The real instructional move is:

```
21.c4?
```

which allowed

```
21...Rxe5
```

Therefore the LLM is explaining the punishment instead of the mistake.

---

# Goal

Redesign the critical move extraction stage so every critical move represents **the player's move that caused the problem**, not the opponent's tactical punishment.

The punishment should still be stored as supporting context.

---

# Required Changes

## 1. Detect Whose Move Triggered the Evaluation Drop

When Stockfish reports a mistake/blunder:

Determine whether the evaluation change happened:

* immediately after the player's move
* immediately after the opponent's reply

If the critical swing is detected after the opponent's move:

```
player_move
↓
opponent tactical punishment
↓
evaluation collapse
```

then:

store

```
player_move
```

as the critical move.

---

## 2. Replace Current Structure

Current:

```json
{
    "move": "21...Rxe5"
}
```

New:

```json
{
    "move_number": 21,

    "player_move": "21.c4",

    "opponent_reply": "21...Rxe5",

    "critical_side": "player",

    "severity": "mistake"
}
```

---

## 3. Root Cause Backtracking

After finding a critical move, walk backwards several plies.

Goal:

Find whether the evaluation collapse actually originated earlier.

Example:

```
14.e5
...
15...Nxd5
16.Bxd5
17...Bxd5
```

Although material is lost on move 17, the instructional mistake started on move 14.

Algorithm:

```
for each critical move:

    inspect previous 2–5 plies

    locate the first move where

        evaluation begins to deteriorate

    if found:

        replace critical move

        mark original move as consequence
```

---

## 4. Store Both Cause and Punishment

Each critical move should contain:

```json
{
    "player_move": "14.e5",

    "opponent_reply": "14...dxe5",

    "root_cause": true,

    "consequence_sequence": [
        "15...Nxd5",
        "16.Bxd5",
        "16...Qxd5",
        "17.Qxd5",
        "17...Bxd5"
    ]
}
```

---

## 5. Add Instructional Pattern

Instead of generic concepts such as

```
king safety
```

infer concrete instructional patterns.

Examples:

```
loose_piece_after_pawn_push

undefended_advanced_pawn

hanging_piece

overloaded_defender

tactical_overload

passive_rooks

rook_invasion

bishop_diagonal

weak_back_rank
```

Store:

```json
{
    "pattern":

    "loose_piece_after_pawn_push"
}
```

---

## 6. Generate Better Context for Gemini

Instead of:

```json
{
    "move":"21...Rxe5"
}
```

send

```json
{
    "player_move":"21.c4",

    "opponent_reply":"21...Rxe5",

    "pattern":"undefended_advanced_pawn",

    "issue":
    "The pawn advance left the e5 pawn undefended.",

    "consequence":
    "Black won the pawn and activated the rook.",

    "lesson":
    "Before advancing a pawn, verify which pieces or pawns stop being defended."
}
```

---

## 7. Update the Prompt Sent to Gemini

Modify the coaching prompt.

Replace the current behavior with:

```
Each entry in critical_moves always represents the student's move.

If opponent_reply exists:

Explain it only as the tactical punishment.

Never describe opponent_reply as if it were the student's mistake.

Focus on the player's decision and why it enabled the opponent's response.

If root_cause is true:

Prioritize explaining that move instead of later consequences.
```

---

# Success Criteria

After this refactor the coaching should naturally evolve from:

> "After 21...Rxe5 your king became exposed..."

to

> "The key mistake was 21.c4. This pawn advance left your advanced e5 pawn undefended, allowing 21...Rxe5. The real lesson is to verify which pieces and pawns lose protection before advancing another pawn."

The objective is to transform the coaching from describing tactical punishments into explaining the underlying decision that created the tactical opportunity.

# REGLA DE CONTROL:

Debes mencionar exclusivamente las jugadas presentes en critical_moves.
Está prohibido agregar momentos clave que no estén en critical_moves.
Si critical_moves contiene seis entradas, la sección "Momentos clave" debe contener exactamente esas seis entradas y ninguna otra.
Si una jugada no aparece en critical_moves, no la menciones como momento clave.

