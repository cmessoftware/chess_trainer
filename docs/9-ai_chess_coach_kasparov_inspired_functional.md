ChessTrainer — Kasparov Decision Engine - Functional Design

## Objetivo

Implementar un módulo de análisis de partidas que capture el **proceso de toma de decisiones del jugador**, no solo el resultado de la jugada.

El módulo debe:

- detectar **momentos críticos**
- reconstruir **planes y candidatos**
- comparar con el **motor**
- clasificar **tipos de error**
- generar **features para ML**

Este módulo alimentará:

- dashboards
- generación automática de ejercicios
- datasets de entrenamiento
- recomendaciones personalizadas

---

# Arquitectura

El módulo seguirá la arquitectura existente del proyecto.


UI (React+Vite)
↓
REST API (FastAPI)
↓
Analysis Services
↓
Repositories
↓
Database


---

# Pipeline de análisis

Cada partida seguirá este flujo.


PGN
↓
feature extraction
↓
critical moment detection
↓
candidate move generation
↓
engine evaluation
↓
error classification
↓
dataset generation


---

# Paso 1 — Detección de momentos críticos

Un momento crítico es una jugada donde ocurre:

- gran cambio de evaluación
- decisión estratégica relevante
- inicio de ataque
- simplificación importante
- error grave

## Heurísticas

Detectar si:


abs(score_diff) > threshold


o


abs(depth_score_diff) > threshold


También marcar jugadas donde:

- aparece táctica
- cambio de fase
- captura de pieza mayor

## Output


critical_positions


Ejemplo


move_number
fen
score_before
score_after
phase


---

# Paso 2 — Reconstrucción del plan

Intentar inferir el plan del jugador a partir de la posición.

## Features usadas

- estructura de peones
- columnas abiertas
- seguridad del rey
- material
- actividad de piezas

## Plan types


attack_king
central_break
minority_attack
positional_pressure
endgame_transition
piece_improvement
defensive_hold


## Output


plan_type
plan_confidence


---

# Paso 3 — Generación de jugadas candidatas

Para cada posición crítica generar **máximo 3 candidatas**.

## Método

1. jugada del jugador
2. mejor jugada del engine
3. mejor alternativa estratégica

## Estructura


candidate_moves


Ejemplo


[
{"move":"Qg4", "type":"played"},
{"move":"Qd2", "type":"engine_best"},
{"move":"Rfd1", "type":"strategic"}
]


---

# Paso 4 — Evaluación con engine

Evaluar cada candidata.

Engine:


Stockfish


Datos almacenados


score_cp
mate_in
depth
principal_variation


---

# Paso 5 — Clasificación del error

Comparar la jugada del jugador con la mejor del engine.

## Categorías


brilliant
good
inaccuracy
mistake
blunder


## Clasificación adicional


calculation_error
strategy_error
prophylaxis_miss
impulsive_move
time_pressure
tactical_miss
endgame_error


---

# Paso 6 — Generación de dataset

Cada jugada produce una fila.

## Dataset schema


move_id
game_id
fen
move
evaluation_before
evaluation_after
score_diff
depth_score_diff
phase
plan_type
candidate_count
error_label
tactical_tags
material_total
num_pieces
is_center_controlled
is_pawn_endgame


---

# Paso 7 — Generación de feedback

El sistema debe generar recomendaciones.

Ejemplo


El plan correcto era presionar la columna abierta.
La jugada Qg4 ignora la mejora de piezas.
Se recomienda Qd2 seguido de doblar torres.


---

# Integración con módulos existentes

Este módulo alimenta:


tactical_recommender
training_dataset
feedback_analysis
tactics_progress_chart


---

# Servicios a implementar

## AnalysisService

Responsable del pipeline completo.

Funciones:


analyze_game(pgn)
detect_critical_positions(game)
infer_plan(position)
generate_candidates(position)
evaluate_candidates(position)
classify_error(move)
generate_dataset_rows(game)


---

## CandidateMoveService


generate_candidate_moves(position)


---

## ErrorClassificationService


classify_error(score_diff)
classify_error_type(position)


---

# Base de datos

Tablas sugeridas

## move_analysis


move_id
game_id
ply
fen
move
score_before
score_after
depth
pv
error_label
error_type
plan_type
phase


---

## candidate_moves


candidate_id
move_id
move
candidate_type
score
depth


---

# Visualización en Streamlit

La UI debe mostrar:

- tablero interactivo
- jugada del jugador
- mejor jugada del engine
- evaluación
- explicación estratégica

Ejemplo


Move 18

Played: Qg4
Best: Qd2

Evaluation change: -1.4

Plan: pressure on open file
Error: impulsive attack


---

# Posibles extensiones futuras

- SHAP analysis para modelos ML
- clustering de errores
- generación automática de ejercicios
- recomendación personalizada
- comparación con partidas elite

---

# Métricas del jugador

El sistema debe calcular:


blunder_rate
mistake_rate
tactical_accuracy
positional_accuracy
plan_consistency
calculation_depth


---

# Resultado esperado

El módulo permitirá:

- detectar patrones de error
- mejorar entrenamiento personalizado
- generar datasets para ML
- crear ejercicios automáticamente
- analizar el estilo del jugador

