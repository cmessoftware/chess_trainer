# Cursor Prompt: Debug and Harden Gemini Coaching Prompt

## Context

The current pipeline sends chess game context to Gemini 2.5 Flash to generate coaching feedback.

Problem observed:

The prompt shown to the user contains `critical_moves` with moves:

```text
20, 21, 29, 46, 55, 56
```

but Gemini generated feedback for different moves:

```text
6.N1c3
34.b4
57.Kb8
```

This means one of these bugs exists:

* the final prompt sent to Gemini is not the same as the prompt displayed/logged
* the `critical_moves` payload is being overwritten
* Gemini is receiving conversational history or stale context
* the model is ignoring `critical_moves`
* the parser is mixing critical moves from another source

Goal:

Fix the pipeline so Gemini only explains the moves explicitly present in `critical_moves`.

---

## Required Tasks

### 1. Add strict logging

Before calling Gemini, save these files:

```text
debug/prompt_final_sent_to_gemini.txt
debug/critical_moves_payload.json
debug/full_llm_payload.json
```

The logged prompt must be exactly the same string sent to Gemini.

Do not log an intermediate prompt.

Do not log a reconstructed prompt.

Log the final value immediately before the API call.

---

### 2. Validate `critical_moves` before calling Gemini

Add validation rules:

```python
assert critical_moves is not None
assert len(critical_moves) > 0
```

Each critical move must contain:

```python
required_fields = [
    "move_number",
    "player_move",
    "phase",
    "severity",
    "issue",
    "lesson_hint",
    "context_pgn"
]
```

Optional but preferred:

```python
optional_fields = [
    "opponent_reply",
    "pattern",
    "consequence"
]
```

Reject or warn if the old ambiguous field exists:

```python
"move"
```

because it creates confusion between player move and opponent punishment.

---

### 3. Enforce player move vs opponent reply

Replace old structure:

```json
{
  "move": "21...Rxe5"
}
```

with:

```json
{
  "player_move": "21.c4",
  "opponent_reply": "21...Rxe5"
}
```

Rules:

* `player_move` is always the student's mistake.
* `opponent_reply` is always the rival's punishment.
* Gemini must never treat `opponent_reply` as the student's move.
* If the evaluation swing occurs after the opponent reply, map the critical move back to the previous move made by the student.

---

### 4. Add root-cause backtracking

When a blunder/mistake is detected after a forcing sequence, walk backwards several plies to identify the first bad player move.

Example:

```text
13.Kh1 Rc8
14.e5? dxe5
15.fxe5 Nxd5
16.Bxd5 Qxd5
17.Qxd5 Bxd5
```

The root cause is:

```text
14.e5?
```

not the final material-loss move.

Store:

```json
{
  "player_move": "14.e5",
  "opponent_reply": "14...dxe5",
  "root_cause": true,
  "pattern": "loose_piece_after_pawn_push",
  "issue": "The e5 pawn advance initiated a forcing exchange sequence where the knight on d5 became tactically vulnerable.",
  "consequence": "After simplification, Black won a full piece.",
  "lesson_hint": "Before pushing a central pawn, check which pieces stop being defended.",
  "context_pgn": "13.Kh1 Rc8 14.e5 dxe5 15.fxe5 Nxd5 16.Bxd5 Qxd5 17.Qxd5 Bxd5"
}
```

---

### 5. Harden the Gemini prompt

Add this control block at the top of the prompt:

```text
CONTROL RULES:
- You must mention only moves listed in critical_moves.
- Do not add extra critical moments.
- The "Momentos clave" section must contain exactly one entry for each item in critical_moves.
- Each critical_moves item represents the student's move in player_move.
- opponent_reply is only the opponent's tactical punishment.
- Never describe opponent_reply as if it were the student's mistake.
- If a move is not present in critical_moves, do not mention it as a key moment.
- Do not use generic filler phrases such as "jaques, capturas y amenazas", "JCA", "revisa tácticas", "rey expuesto", or "seguridad del rey" unless directly supported by issue, consequence, or context_pgn.
```

---

### 6. Force output format

Ask Gemini to use this exact structure for every critical move:

```text
### Momentos clave

- Jugada del alumno: {player_move}
  Castigo del rival: {opponent_reply}
  Causa: {issue}
  Consecuencia: {consequence}
  Lección: {lesson_hint}
```

If `opponent_reply` is missing, omit only that line.

Do not allow Gemini to invent extra move numbers.

---

### 7. Add post-generation validation

After Gemini returns the response, validate:

* Every mentioned move number exists in `critical_moves`.
* No move number outside `critical_moves` appears in the response.
* The number of "Momentos clave" entries equals `len(critical_moves)`.
* The response does not contain banned generic phrases unless explicitly allowed.

Example banned phrases:

```python
banned_phrases = [
    "jaques, capturas y amenazas",
    "JCA",
    "revisa tácticas",
    "seguridad del rey",
    "rey expuesto",
    "enroque tardío",
    "rey en el centro"
]
```

If validation fails:

* regenerate once with a stricter repair prompt
* if it fails again, return a fallback deterministic coaching summary generated from the structured JSON

---

### 8. Deterministic fallback

Implement a fallback renderer that does not call Gemini.

Example:

```python
def render_deterministic_coaching(game, critical_moves):
    lines = []

    lines.append(f"Revisión de tu partida contra {game['opponent']}.")
    lines.append(f"Resultado: {game['result_description']}.")

    lines.append("### Momentos clave")

    for cm in critical_moves:
        lines.append(f"- Jugada del alumno: {cm['player_move']}")

        if cm.get("opponent_reply"):
            lines.append(f"  Castigo del rival: {cm['opponent_reply']}")

        lines.append(f"  Causa: {cm['issue']}")

        if cm.get("consequence"):
            lines.append(f"  Consecuencia: {cm['consequence']}")

        lines.append(f"  Lección: {cm['lesson_hint']}")

    return "\n".join(lines)
```

---

## Success Criteria

The final output must not invent moves.

If `critical_moves` contains only:

```text
14.e5
21.c4
51.Rd3
```

then Gemini may only explain:

```text
14.e5
21.c4
51.Rd3
```

It must not introduce:

```text
6.N1c3
34.b4
57.Kb8
```

The coaching must explain the student's decision, the opponent's punishment, and the concrete lesson.
