 ChessTrainer — Kasparov Decision Engine
## Copilot Input / Functional + Technical Design

## Objetivo general

Diseñar un módulo llamado **Kasparov Decision Engine (KDE)** dentro de `chess_trainer` para transformar el análisis de partidas en un sistema de **coach automático estilo gran maestro**.

El motor no debe limitarse a responder:

- cuál fue la mejor jugada del engine

Sino también:

- qué plan tenía sentido en la posición
- cuáles eran las jugadas candidatas razonables
- qué patrón de error cometió el jugador
- qué recomendación concreta se le debe dar
- cómo convertir esa información en features útiles para ML

El módulo debe servir simultáneamente para:

1. coaching automático
2. generación de datasets enriquecidos
3. recomendación de ejercicios
4. explicación estratégica en lenguaje natural
5. análisis de patrones del jugador a mediano y largo plazo

---

# Principio conceptual

El enfoque inspirado en Kasparov no analiza solo la jugada final, sino el **proceso de decisión**.

La cadena conceptual a modelar es:

```text
posición
→ evaluación estratégica
→ plan
→ objetivos intermedios
→ candidatas
→ cálculo
→ decisión jugada
→ resultado
→ clasificación del error o acierto
→ feedback

Esto permite que ChessTrainer evolucione desde un simple analizador con engine a un sistema explicativo y pedagógico.

Objetivos funcionales del Kasparov Decision Engine

El KDE debe:

detectar momentos críticos
inferir el plan más razonable
generar jugadas candidatas
contrastar la jugada real con el engine y con el plan
clasificar la calidad de la decisión
generar feedback natural accionable
guardar features intermedias para datasets de ML
producir métricas agregadas por jugador
integrarse con el recomendador de entrenamiento

Ubicación en la arquitectura

El módulo debe encajar en la arquitectura desacoplada del proyecto:

```mermaid
UI (React+Vite)
    ↓
REST API (FastAPI)
    ↓
Application Services
    ↓
Kasparov Decision Engine
    ↓
Repositories
    ↓
Database / Feature Store
Pipeline general del Kasparov Decision Engine
PGN / Game
    ↓
Move Extraction
    ↓
Position Feature Extraction
    ↓
Critical Moment Detection
    ↓
Strategic Interpretation
    ↓
Candidate Move Generation
    ↓
Engine Evaluation
    ↓
Decision Classification
    ↓
Feedback Generation
    ↓
Persistence
    ↓
ML Dataset Export
```

Bloques principales del motor
1. Position Interpreter

Responsabilidad:

Interpretar la posición en términos estratégicos y posicionales.

Debe responder:

quién tiene ventaja y por qué
qué zonas del tablero son relevantes
qué debilidades existen
qué piezas están activas o mal ubicadas
si la posición favorece ataque, maniobra, simplificación, defensa o ruptura

Inputs

FEN

side to move

metadata de la partida

features estáticas y dinámicas existentes

Outputs
position_summary
strategic_balance
king_safety_state
center_control_state
open_files_state
pawn_structure_state
piece_activity_state
phase
Función objetivo

Construir una representación semántica de la posición para que los módulos posteriores no dependan únicamente del score del engine.

2. Critical Moment Detector

Responsabilidad:

Detectar jugadas o posiciones donde el proceso de decisión era importante.

Reglas mínimas

Marcar como momento crítico si ocurre alguno de estos eventos:

abs(score_diff) >= threshold
abs(depth_score_diff) >= threshold
cambio de fase
sacrificio material
aparición o desaparición de amenaza táctica
transición a final
cambio brusco en seguridad del rey
aparición de una ruptura temática
oportunidad táctica fuerte no aprovechada

Output
is_critical
critical_reason
critical_score
Ejemplos de critical_reason
eval_swing
missed_tactic
plan_transition
king_attack_window
endgame_transition
defensive_decision
exchange_decision
central_break_moment
3. Strategic Plan Inference Engine

Responsabilidad:

Inferir el plan más coherente con la posición.

No debe depender solo del engine top-1, sino de patrones estratégicos.

Plan types sugeridos
attack_king
improve_worst_piece
central_break
minority_attack
pressure_open_file
convert_material_advantage
defend_and_hold
simplify_to_endgame
create_passed_pawn
prophylaxis
space_gain
piece_redeployment
counterplay_generation
Subobjetivos

Cada plan debe poder descomponerse en objetivos intermedios.

Ejemplo:

plan_type = attack_king

subgoals:
- open_h_file
- remove_f6_defender
- bring_queen_to_h6
- rook_lift
Output

```json
{
  "plan_type": "attack_king",
  "plan_confidence": 0.82,
  "subgoals": [
    "open_h_file",
    "remove_key_defender",
    "improve_attacking_piece"
  ]
}
```
Reglas de inferencia inicial

Primera versión heurística:

si rey rival inseguro + piezas cerca + columnas semiabiertas → attack_king
si ventaja material y simplificación favorable → simplify_to_endgame
si pieza propia mal ubicada y no hay táctica inmediata → improve_worst_piece
si centro bloqueado y flanco dama expandible → minority_attack
si rival amenaza y posición delicada → prophylaxis o defend_and_hold

Versión futura:

clasificador supervisado o ranking model de plan_type

4. Candidate Move Generator

Responsabilidad:

Generar 2 a 5 jugadas candidatas razonables en menos de una expansión exhaustiva de engine.

Este módulo es central para emular el proceso humano tipo GM.
Algoritmo mental simplificado a modelar
La jugada candidata debe surgir de esta secuencia:

1. detectar amenazas del rival
2. detectar desequilibrios
3. inferir plan
4. seleccionar jugadas que:
   - cumplan el plan
   - sean tácticamente sanas
   - mejoren la posición
5. priorizar máximo 3-5 candidatas
Tipos de candidatas
forced
strategic
prophylactic
tactical
improving_move
defensive_resource
conversion_move
Política mínima de generación

Siempre intentar incluir:

jugada jugada por el usuario
mejor jugada del engine
mejor jugada alineada con el plan
mejor jugada profiláctica si existe
mejor recurso defensivo si la posición lo exige

Output sugerido
```json
[
  {
    "move": "Qd2",
    "candidate_type": "strategic",
    "supports_plan": true,
    "plan_alignment_score": 0.91
  },
  {
    "move": "Rfd1",
    "candidate_type": "improving_move",
    "supports_plan": true,
    "plan_alignment_score": 0.84
  },
  {
    "move": "h4",
    "candidate_type": "tactical",
    "supports_plan": false,
    "plan_alignment_score": 0.42
  }
]
```

5. Candidate Ranking Engine

Responsabilidad:

Rankear candidatas no solo por score del engine, sino por valor pedagógico y estratégico.

Fórmula conceptual
candidate_final_score =
    engine_eval_weight
  + plan_alignment_weight
  + tactical_soundness_weight
  + prophylaxis_weight
  + explainability_weight

Variables

engine_score
plan_alignment_score
tactical_risk_score
defensive_value_score
initiative_score
explainability_score

Objetivo

No elegir solamente la mejor por centipawns, sino también la más útil para construir feedback humano comprensible.

6. Decision Classification Engine

Responsabilidad:

Clasificar la jugada del jugador tanto por calidad objetiva como por tipo de error.

Etiquetas de calidad
brilliant
excellent
good
interesting
inaccuracy
mistake
blunder
Etiquetas de error conceptual
calculation_error
strategy_error
prophylaxis_miss
impulsive_attack
passive_defense
missed_tactic
endgame_misjudgment
time_pressure_like_move
unnecessary_complication
wrong_trade_decision
king_safety_neglect
piece_improvement_miss
conversion_failure
Clasificación compuesta

Ejemplo:

```json
{
  "quality_label": "mistake",
  "error_label": "prophylaxis_miss",
  "error_severity": 0.71,
  "reason": "ignored opponent counterplay on c-file"
}
```

Regla importante

Separar:

error objetivo por engine

error humano/estratégico

Porque una jugada puede ser apenas una inaccuracy según engine pero ser didácticamente una gran falla de plan.

7. Natural Language Coach

Responsabilidad:

Generar explicaciones estilo coach humano.
Debe producir texto breve, concreto y accionable.

Salidas esperadas

explicación de la jugada
explicación del plan correcto
error conceptual
recomendación concreta
patrón recurrente si aplica

Plantilla recomendada
En esta posición el plan más coherente era {plan_type}.
La jugada {played_move} pierde fuerza porque {reason}.
La alternativa {best_candidate} era mejor ya que {benefit}.
Tu error principal aquí fue {error_label}.
Recomendación: {actionable_tip}.
Ejemplo
En esta posición el plan correcto era presionar la columna d y mejorar la torre menos activa.
La jugada Qg4 es demasiado directa y no resuelve la coordinación de piezas.
Qd2 era mejor porque conecta torres y prepara doblarse en la columna abierta.
El patrón de error aquí es impulsive_attack.
Recomendación: antes de atacar, mejora la peor pieza y verifica el contrajuego rival.
8. Pattern Memory Engine

Responsabilidad:

Detectar patrones recurrentes del jugador a través de muchas partidas.

Objetivo

Construir el equivalente a un perfil de toma de decisiones.

Patrones posibles
frequent_impulsive_attacks
late_prophylaxis
weak_endgame_conversion
missed_center_breaks
overvalued_tactics
exchange_misjudgment
poor_worst_piece_improvement
recurrent_king_exposure
Outputs agregados
player_pattern_summary
pattern_frequency
pattern_trend
pattern_severity
Uso

feedback longitudinal

sugerencias de entrenamiento

features de ML por jugador

dashboards de evolución

Diseño de datos
Entidad principal: move_decision_analysis
move_decision_analysis
- id
- game_id
- player_id
- ply
- fen
- side_to_move
- move_played
- move_san
- phase
- is_critical
- critical_reason
- critical_score
- eval_before_cp
- eval_after_cp
- score_diff_cp
- depth_score_diff
- plan_type
- plan_confidence
- subgoals_json
- quality_label
- error_label
- error_severity
- explanation_text
- actionable_tip
- created_at
Entidad: move_candidates
move_candidates
- id
- move_analysis_id
- move_uci
- move_san
- candidate_rank
- candidate_type
- engine_score_cp
- mate_in
- depth
- plan_alignment_score
- tactical_soundness_score
- prophylaxis_score
- explainability_score
- final_candidate_score
- is_engine_best
- is_played_move
- is_selected_best_human_candidate
Entidad: player_decision_pattern
player_decision_pattern
- id
- player_id
- pattern_name
- phase
- opening_family
- frequency
- severity_avg
- last_seen_at
- trend_direction
- example_game_id
- example_ply
Entidad: training_recommendation
training_recommendation
- id
- player_id
- source_pattern
- recommendation_type
- recommendation_text
- exercise_theme
- priority
- created_at
- status
Features para ML
Nivel jugada
eval_before_cp
eval_after_cp
score_diff_cp
depth_score_diff
phase
material_balance
material_total
num_pieces
king_safety_self
king_safety_opp
center_control_self
center_control_opp
open_files_count
semi_open_files_count
passed_pawns_self
passed_pawns_opp
piece_activity_score
worst_piece_score
plan_type
plan_confidence
candidate_count
best_candidate_gap_cp
played_vs_best_rank
error_label
quality_label
is_critical
critical_reason
tactical_tags
Nivel partida
blunder_rate
mistake_rate
inaccuracy_rate
critical_moment_accuracy
plan_consistency_score
prophylaxis_score
conversion_score
attack_success_score
endgame_decision_score
Nivel jugador
dominant_error_pattern
opening_risk_profile
strategic_style_vector
tactical_style_vector
decision_stability_score
improvement_trend
Servicios a implementar
KasparovDecisionEngineService

Servicio orquestador.

Métodos sugeridos

```python
class KasparovDecisionEngineService:
    def analyze_game(self, game_id: int) -> GameDecisionAnalysisResult: ...
    def analyze_move(self, fen: str, move: str, context: dict) -> MoveDecisionAnalysisResult: ...
    def detect_critical_moments(self, game_id: int) -> list[CriticalMoment]: ...
    def infer_plan(self, fen: str, context: dict) -> PlanInferenceResult: ...
    def generate_candidates(self, fen: str, context: dict) -> list[CandidateMove]: ...
    def evaluate_candidates(self, fen: str, candidates: list[str]) -> list[EvaluatedCandidate]: ...
    def classify_decision(self, move_analysis_input: dict) -> DecisionClassificationResult: ...
    def generate_feedback(self, move_analysis_input: dict) -> CoachFeedbackResult: ...
    def update_player_patterns(self, player_id: int) -> None: ...
PositionInterpreterService
class PositionInterpreterService:
    def summarize_position(self, fen: str) -> PositionSummary: ...
    def detect_imbalances(self, fen: str) -> PositionImbalances: ...
    def detect_phase(self, fen: str) -> str: ...
PlanInferenceService
class PlanInferenceService:
    def infer_plan(self, fen: str, position_summary: PositionSummary) -> PlanInferenceResult: ...
    def infer_subgoals(self, fen: str, plan_type: str) -> list[str]: ...
CandidateGenerationService
class CandidateGenerationService:
    def generate(self, fen: str, plan: PlanInferenceResult, context: dict) -> list[CandidateMove]: ...
    def add_played_move(self, move: str, candidates: list[CandidateMove]) -> list[CandidateMove]: ...
    def add_engine_best(self, fen: str, candidates: list[CandidateMove]) -> list[CandidateMove]: ...
CandidateRankingService
class CandidateRankingService:
    def rank(self, evaluated_candidates: list[EvaluatedCandidate], plan: PlanInferenceResult) -> list[EvaluatedCandidate]: ...
DecisionClassificationService
class DecisionClassificationService:
    def classify_quality(self, score_diff_cp: int) -> str: ...
    def classify_error_type(self, move_context: dict) -> str: ...
    def build_decision_result(self, analysis_input: dict) -> DecisionClassificationResult: ...
CoachNarrativeService
class CoachNarrativeService:
    def generate_feedback(self, analysis_result: MoveDecisionAnalysisResult) -> CoachFeedbackResult: ...
    def generate_short_tip(self, analysis_result: MoveDecisionAnalysisResult) -> str: ...
    def generate_training_focus(self, player_patterns: list[PlayerPattern]) -> list[str]: ...
PlayerPatternService
class PlayerPatternService:
    def aggregate_patterns(self, player_id: int) -> list[PlayerPattern]: ...
    def detect_trends(self, player_id: int) -> PlayerPatternTrendResult: ...
    def build_player_profile(self, player_id: int) -> PlayerDecisionProfile: ...
DTOs sugeridos
PlanInferenceResult
@dataclass
class PlanInferenceResult:
    plan_type: str
    confidence: float
    subgoals: list[str]
    explanation: str | None = None
CandidateMove
@dataclass
class CandidateMove:
    move_uci: str
    move_san: str | None
    candidate_type: str
    supports_plan: bool
    plan_alignment_score: float
    source: str
EvaluatedCandidate
@dataclass
class EvaluatedCandidate:
    move_uci: str
    move_san: str | None
    candidate_type: str
    engine_score_cp: int | None
    mate_in: int | None
    depth: int | None
    plan_alignment_score: float
    tactical_soundness_score: float
    prophylaxis_score: float
    explainability_score: float
    final_candidate_score: float
    rank: int | None = None
MoveDecisionAnalysisResult
@dataclass
class MoveDecisionAnalysisResult:
    game_id: int
    ply: int
    fen: str
    move_played: str
    phase: str
    is_critical: bool
    critical_reason: str | None
    plan: PlanInferenceResult
    candidates: list[EvaluatedCandidate]
    quality_label: str
    error_label: str | None
    explanation_text: str
    actionable_tip: str
```

Endpoints sugeridos
Analizar partida completa
POST /api/kde/games/{game_id}/analyze

Respuesta:

```json
{
  "game_id": 123,
  "critical_positions_found": 8,
  "analyses_created": 42,
  "player_patterns_updated": true
}
```

Analizar jugada puntual
POST /api/kde/move/analyze

Body:

```json
{
  "fen": "r1bq1rk1/pp1n1ppp/2pbpn2/3p4/3P4/2N1PN2/PPQ1BPPP/R1B2RK1 w - - 0 10",
  "move": "e4",
  "context": {
    "game_id": 123,
    "ply": 20,
    "player_id": 77
  }
}
```
Obtener patrones del jugador
GET /api/kde/players/{player_id}/patterns
Obtener recomendaciones de entrenamiento
GET /api/kde/players/{player_id}/recommendations
Integración con módulos existentes
analyze_feedback.py

Usar el output del KDE para enriquecer error_label, plan_type, critical_reason.

training_recommender.py
Usar player_decision_pattern para sugerir ejercicios por patrón dominante.
tactical_recommender.py
Cruzar missed_tactic, impulsive_attack, prophylaxis_miss con tactical_tags.
feedback_analysis.ipynb

Agregar análisis por:

plan_type
quality_label
critical_reason
candidate_rank_of_played_move

React+Vite UI

Agregar panel “Decision Coach” con:

plan inferido
top candidatas
error conceptual
tip concreto
patrón recurrente relacionado

Roadmap de implementación
Fase 1 — MVP heurístico

Objetivo: tener un coach funcional aunque todavía simple.

Implementar:

detector de momentos críticos
inferencia heurística de plan
generación básica de candidatas

clasificación por score_diff

feedback en lenguaje natural
persistencia en move_decision_analysis

Fase 2 — Enriquecimiento estratégico

Implementar:

subgoals
ranking de candidatas
etiquetado de errores conceptuales
player patterns
recomendaciones automáticas

Fase 3 — ML assisted engine

Implementar:

modelo de predicción de plan_type
ranking model de candidatas
clasificador de error conceptual
embeddings de posiciones / decisiones

Fase 4 — Coach adaptativo

Implementar:

feedback personalizado por perfil del jugador
rutas de entrenamiento adaptadas
detección de mejora real por patrón

Reglas de diseño importantes
1. Separar engine score de explicación humana

El coach no debe limitarse a decir que una jugada vale menos centipawns.
Debe explicar el porqué en términos humanos.

2. Guardar toda la traza intermedia

No guardar solo el resultado final.
Persistir plan, candidatas, razones, scores, patrones.

3. No depender exclusivamente del top-1 del engine

El top-1 del engine no siempre coincide con la mejor explicación pedagógica.

4. Priorizar explicaciones accionables

Cada análisis debe terminar con una recomendación concreta que el jugador pueda entrenar.

5. Diseñar para dataset first

Todo output del KDE debe poder convertirse fácilmente en fila de dataset.

Ejemplo de salida ideal
```json
{
  "game_id": 1452,
  "ply": 23,
  "phase": "middlegame",
  "is_critical": true,
  "critical_reason": "king_attack_window",
  "plan": {
    "plan_type": "improve_worst_piece",
    "confidence": 0.78,
    "subgoals": [
      "activate_rook_on_d_file",
      "stabilize_center",
      "limit_counterplay"
    ]
  },
  "played_move": "Qg4",
  "quality_label": "mistake",
  "error_label": "impulsive_attack",
  "candidates": [
    {
      "move": "Qd2",
      "candidate_type": "strategic",
      "rank": 1
    },
    {
      "move": "Rfd1",
      "candidate_type": "improving_move",
      "rank": 2
    },
    {
      "move": "h4",
      "candidate_type": "tactical",
      "rank": 3
    }
  ],
  "feedback": {
    "explanation_text": "El plan correcto era mejorar la coordinación y presionar la columna abierta antes de atacar.",
    "actionable_tip": "Antes de lanzar un ataque, preguntate cuál es tu peor pieza y si el rival tiene contrajuego inmediato."
  }
}
```
Resultado esperado

Con este módulo, ChessTrainer debe pasar de:

motor de evaluación de jugadas

a:

coach estratégico automático + generador de datasets de decisión

Esto permitirá:

feedback mucho más humano
mejor entrenamiento personalizado
mejores features para ML
mayor trazabilidad del proceso de pensamiento
futura evolución hacia un AI chess coach realmente útil