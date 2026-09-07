# Checklist manual — Module 07 ya implementado

Abrí Jupyter con cwd `docs/ai_chess_coach_course` (o el repo root; el bootstrap busca ambos).
`.env` con `STOCKFISH_PATH` para ítems 003+.
**Fuente humana primero:** libros (Chernev, Kasparov, *Mi sistema*) → `data/expert_gold/`. El pastor (`f07_002_white.pgn`) y `sample_game4.pgn` son humo de pipeline, no gold experto.

## A. Lab único (recorrido integrado)

Archivo: `07_0_mental_model_lab.ipynb`

1. **Paso 0.** `PGN_PATH = GAMES_DIR / 'f07_002_white.pgn'` y `PLAYER_NAME = 'cmess1315'`. Ejecutá. Confirmá que ve `.env` y Stockfish si lo usás.
2. **Paso 1 (F07-001/002).** Carga: White `cmess1315`, plies del pastor, `select_analyzed_player` deja solo blancas.
3. **Paso 2.** Listado de ply. Para el error de negras no uses este jugador: cambiá a `PLAYER_NAME` del negro o `PLAYER_COLOR='black'` y recargá Paso 1. `TARGET_SAN` vía `TARGET_MOVE_NUMBER` o ply de `Nf6`.
4. **Paso 3 (003–008, 012–016, 019, 028, 035).** Con Stockfish:
   - Eval antes/después y `eval_loss` (005).
   - `EVALUATION_DROP` en `Nf6` (006). Recordá: es *después* del error (§1 del doc 07/08).
   - MultiPV 3 y gap PV1–PV2 en cp (§2). `ONLY_MOVE` no debe disparar en `1.e4`.
   - `POSITION_TRANSFORMATION`: en el pastor casi no; cambiá PGN a `sample_game4.pgn`, jugada `f5` → `PAWN_BREAK`; `O-O-O` → `OPPOSITE_CASTLING`.
   - Ranking (013) solo si `SCORE_ALL_PLAYER_PLIES = True` (lento).
   - Comparación 019 + abstención 028 (`NONE` en Nf6).
   - Review pack JSON en `artifacts/module07/` (035); `primary_error` null.
5. **Pasos 4+.** Prototipo mental E1–E11 (HTML). No es el detector P0; no lo uses como validación de 07.1 motor.

Repetí A con `sample_game4.pgn` / `cmess1315` / `TARGET_MOVE_NUMBER = 11`.

## B. Labs parciales (un ítem por notebook)

Carpeta: `labs/`. Índice: `labs/README.md`. Regenerar: `python _gen_f07_item_labs.py`.

| Orden | Notebook | Esperado en humo | Comparar con libro |
| ----- | -------- | ---------------- | ------------------- |
| 1 | F07-001 | SAN `e4 e5 Qh5…` | Misma partida del libro, mismos lances |
| 2 | F07-002 | Color y lista de plies del jugador | Lado que analiza el autor |
| 3 | F07-003 | Eval/mate en `Qxf7#` | No sustituye el comentario humano |
| 4 | F07-004 | POV negras en `Nf6` | Signo coherente con el bando |
| 5 | F07-005 | `eval_loss` alto en `Nf6` | El autor marca el error |
| 6 | F07-006 | DROP fired | ¿El libro ya pedía calcular *antes*? |
| 7 | F07-007 | `e4` no ONLY_MOVE; FEN octava sí | Caso “única defensa” del libro |
| 8 | F07-008 | `f5` PAWN_BREAK | Ruptura o rey en Chernev/Kasparov |
| 9 | F07-012 | score/level en `Nf6` | No usar DROP como única señal de “detenerse” |
| 10 | F07-013 | `Nf6` cerca del top | Posiciones que el autor llama críticas |
| 11 | F07-014 | 3 líneas + gap cp | `expert_candidates` |
| 12 | F07-015 | Nf6 independent o rank | Jugada jugada vs las del autor |
| 13 | F07-016 | SAN=Qh5 | Notación del libro |
| 14 | F07-019 | gap vs g6/Qe7 | “Mejor era…” |
| 15 | F07-028 | NONE en Nf6 | No afirmar hipótesis cognitiva |
| 16 | F07-035 | JSON FEN+candidatas | Plantilla `expert_gold` |

En cada lab, última celda markdown: copiá FEN, `stop_reason` humano, y si SF discrepa.

## C. Primer gold (libros)

1. Elegí 1 posición táctica de Chernev o Kasparov (amenaza inmediata).
2. Completá `data/expert_gold/case_template.json` → una línea en `expert_gold.jsonl`.
3. Corré el lab F07-009 *cuando exista*; hasta entonces usá 014/008/007 según el tema.
4. No pongas eval de Stockfish como `expert_preferred`.
