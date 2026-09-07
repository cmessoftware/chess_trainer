# expert_gold — primer conjunto de prueba manual (Módulos 07/08 §7)

La primera fuente para las pruebas **manuales y el dataset dorado estratégico** no es Stockfish ni Lichess Evaluations. Es el **comentario humano de libros anotados**.

## Orden de fuentes (acordado)

1. **Libros anotados (esta carpeta)** — Chernev (*Logical Chess* / *The Most Instructive Games*), Kasparov (*My Great Predecessors* / partidas comentadas), Nimzowitsch (*My System*). Extraé **a mano** 30–100 posiciones. Resumí la idea con tus palabras; no copies párrafos. Guardá autor, título y página. Derechos: `private_research`.
2. Estudios Lichess curados (comentarios + variantes), solo con curación.
3. ChessBase Mega Database (escala de partidas anotadas; no redistribuir comentarios en el producto).
4. `engine_scale` (Lichess Evaluations / Puzzles, CC0) — valida el **pipeline**, no si un humano debía detenerse.

Stockfish/Lc0 se corren **después** de etiquetar el caso experto. Si el motor discrepa, se guardan las tres capas (experto / SF / Lc0); no se pisa el experto.

## Cómo cargar un caso

1. Elegí una posición del libro donde el autor dice que había que calcular, había amenaza, única defensa, sacrificio o ruptura.
2. Reconstruí el FEN (tablero del libro o PGN público de la misma partida).
3. Completá un objeto en `expert_gold.jsonl` (una línea JSON por caso).
4. Abrí el lab del ítem (`labs/07_f07_*.ipynb`) y compará la salida del código con `stop_reason` y `expert_candidates`.

Plantilla: ver `case_template.json`.
