# ChessInsight — Complementary Functional Specification

## Decision-Process Diagnosis, Static-Dynamic Evaluation, and Personalized Training

---

## 1. Purpose

Extend the system defined in:

> **ChessInsight — Functional Specification: Critical Position Detection, Candidate Move Analysis, and Suboptimal Sequence Detection**

This specification adds a chess, cognitive, and pedagogical diagnosis layer on top of the results produced by the engine and the existing detection components.

The system must not be limited to determining whether a move was:

* good;
* inaccurate;
* a mistake;
* a blunder.

It must also attempt to answer:

1. What did the position require?
2. What type of decision did the player need to make?
3. Which positional factors had priority?
4. What was the purpose of each candidate move?
5. Which aspect of the position appears to have been overlooked?
6. Was the error tactical, strategic, prophylactic, technical, or practical?
7. Was it an isolated move or part of a sequence consistent with an incorrect plan?
8. Is it a recurring pattern in the player’s history?
9. Which exercise would specifically train that weakness?

---

## 2. Functional Objective

ChessInsight must transform engine analysis into an explainable diagnosis of the decision-making process.

The conceptual flow will be:

```text
PGN
  ↓
Engine analysis
  ↓
Critical position detection
  ↓
Candidate generation and comparison
  ↓
Suboptimal sequence detection
  ↓
Structured position evaluation
  ↓
Required decision-type classification
  ↓
Chess error diagnosis
  ↓
Controlled inference of process errors
  ↓
Longitudinal pattern detection
  ↓
Explanation and exercise generation
```

---

## 3. Scope

### 3.1 Included

The system must:

* evaluate structured positional factors;
* classify the static or dynamic character of a position;
* identify the required decision type;
* describe the purpose of candidate moves;
* detect overlooked positional factors;
* classify chess errors;
* generate hypotheses about decision-process failures;
* assign confidence levels to inferences;
* connect individual errors to suboptimal sequences;
* detect recurring patterns across multiple games;
* generate training recommendations;
* generate pedagogical questions;
* maintain traceability between evidence, inference, and explanation.

### 3.2 Excluded from the First Version

The first version must not:

* state with certainty what the player was thinking;
* diagnose psychological states;
* infer emotions from a PGN;
* replace validation by a human coach;
* generate explanations without structured evidence;
* depend exclusively on an LLM for error detection;
* initially train an end-to-end cognitive model;
* analyze body language, voice, or video;
* automatically modify the player’s opening repertoire.

---

## 4. Design Principles

### 4.1 Separation Between Fact and Inference

Every conclusion must be classified into one of the following categories:

```text
FACT
STRONG_INFERENCE
WEAK_INFERENCE
PLAYER_CONFIRMED
```

Example:

```json
{
  "statement": "The move does not address the threat against f2.",
  "evidence_type": "FACT",
  "confidence": 1.0
}
```

```json
{
  "statement": "The player probably failed to evaluate the threat against f2 correctly.",
  "evidence_type": "STRONG_INFERENCE",
  "confidence": 0.82
}
```

```json
{
  "statement": "The move may have been played automatically.",
  "evidence_type": "WEAK_INFERENCE",
  "confidence": 0.43
}
```

### 4.2 The Engine Validates, but Does Not Explain by Itself

Stockfish or any other chess engine must be used to:

* evaluate positions;
* calculate variations;
* obtain MultiPV lines;
* determine critical responses;
* measure evaluation loss;
* verify tactics;
* validate candidate moves.

The engine must not be the only source used to:

* determine the purpose of a move;
* classify a cognitive error;
* establish a human plan;
* generate a pedagogical explanation;
* conclude which factor was overlooked.

### 4.3 Mandatory Explainability

Every classification must include:

* evidence;
* the rule or criterion applied;
* confidence level;
* input data used;
* relationship to the position;
* limitations of the conclusion.

### 4.4 Conservative Inference

When the evidence is insufficient, the system must return:

```text
Cannot be determined with sufficient confidence.
```

It must not fill gaps with plausible but unverifiable explanations.

---

## 5. Terminology

### 5.1 Objective Move Quality

Classification derived from evaluation loss and context:

```text
BEST
EXCELLENT
GOOD
INACCURACY
MISTAKE
BLUNDER
FORCED
```

### 5.2 Decision Type

Primary category of the decision required by the position:

```text
TACTICAL
STRATEGIC
PROPHYLACTIC
DYNAMIC
STATIC
DEFENSIVE
TECHNICAL
PRACTICAL
OPENING
ENDGAME
```

A position may require more than one decision type.

### 5.3 Position Character

Describes the general priority of action:

```text
TACTICAL_RESOLUTION
DYNAMIC_ACTION_REQUIRED
STATIC_IMPROVEMENT
DEFENSIVE_URGENCY
PROPHYLACTIC_DECISION
TECHNICAL_CONVERSION
TRANSITION_DECISION
BALANCED_FLEXIBLE
```

### 5.4 Positional Factor

Dimension used to evaluate the position:

```text
MATERIAL
KING_SAFETY
DEVELOPMENT
SPACE
CENTER_CONTROL
PAWN_STRUCTURE
PIECE_ACTIVITY
PIECE_COORDINATION
MOBILITY
INITIATIVE
TEMPO
WEAK_SQUARES
OPEN_FILES
DIAGONALS
OUTPOSTS
PASSED_PAWNS
WORST_PIECE
BEST_PIECE
EXCHANGE_QUALITY
ENDGAME_POTENTIAL
```

### 5.5 Process Error

Hypothesis about a decision-making weakness compatible with the observed move:

```text
MISSED_THREAT
SINGLE_CANDIDATE
POOR_CANDIDATE_GENERATION
PREMATURE_CALCULATION_STOP
VISUALIZATION_ERROR
FINAL_POSITION_EVALUATION_ERROR
STRATEGIC_MISDIAGNOSIS
AUTOMATIC_MOVE
HOPE_CHESS
TACTICAL_OVERREACH
PASSIVE_DEFENSE
IGNORED_WORST_PIECE
WRONG_EXCHANGE
IGNORED_OPPONENT_PLAN
FAILURE_TO_REASSESS
PLAN_PERSISTENCE
TIME_MANAGEMENT_ERROR
UNJUSTIFIED_SACRIFICE
MISPLACED_PRIORITY
```

---

## 6. Functional Architecture

The extension must incorporate the following modules:

```text
Position Assessment Engine
Decision Requirement Classifier
Candidate Purpose Analyzer
Static-Dynamic Evaluator
Chess Error Diagnosis Engine
Cognitive Hypothesis Engine
Sequence Interpretation Engine
Player Pattern Engine
Pedagogical Recommendation Engine
Explanation Composer
```

---

# 7. Position Assessment Engine

## 7.1 Responsibility

Evaluate the position using a structured set of human-understandable and computable factors.

## 7.2 Input

```json
{
  "fen": "string",
  "side_to_move": "white",
  "engine_evaluation": 0.42,
  "principal_variations": [],
  "board_features": {},
  "previous_position_features": {},
  "game_phase": "middlegame"
}
```

## 7.3 Output

```json
{
  "material": {
    "score": 0.0,
    "advantage": "balanced"
  },
  "king_safety": {
    "white": 0.62,
    "black": 0.41,
    "advantage": "white"
  },
  "development": {
    "white": 0.75,
    "black": 0.63
  },
  "space": {
    "white": 0.58,
    "black": 0.42
  },
  "pawn_structure": {
    "white": 0.55,
    "black": 0.48
  },
  "piece_activity": {
    "white": 0.49,
    "black": 0.57
  },
  "initiative": {
    "side": "white",
    "strength": 0.61
  },
  "worst_piece": {
    "side": "white",
    "piece": "Bc1",
    "reason": "low mobility and blocks rook connection"
  },
  "opponent_plan": [
    "prepare_f5_break",
    "increase_kingside_pressure"
  ],
  "recommended_priorities": [
    "complete_development",
    "neutralize_kingside_expansion"
  ]
}
```

## 7.4 Minimum Rules

The module must calculate or estimate:

* material balance;
* both kings’ safety;
* developed pieces;
* central control;
* space;
* mobility;
* pawn structure;
* piece activity;
* coordination;
* initiative;
* pieces without a useful function;
* weak squares;
* relevant files and diagonals;
* passed pawns;
* quality of potential exchanges;
* endgame potential;
* the opponent’s likely plan.

## 7.5 Traceability Requirement

Each factor must indicate how it was calculated:

```json
{
  "factor": "king_safety",
  "score": 0.41,
  "evidence": [
    "two open files near king",
    "three attacking pieces",
    "one pawn missing from king shelter"
  ]
}
```

---

# 8. Static-Dynamic Evaluator

## 8.1 Responsibility

Determine whether the position allows gradual improvement or requires immediate action.

## 8.2 Conceptual Model

The evaluation must consider:

1. king safety;
2. material;
3. pawn structure;
4. piece quality and activity;
5. initiative;
6. possibility of irreversible transformations;
7. long-term positional outlook.

## 8.3 Expected Output

```json
{
  "position_character": "DYNAMIC_ACTION_REQUIRED",
  "static_outlook": "worse",
  "dynamic_resources": "available",
  "urgency": 0.78,
  "reasons": [
    "inferior_endgame_structure",
    "temporary_piece_activity",
    "pawn_break_available_now",
    "opponent_can_consolidate"
  ]
}
```

## 8.4 Example Rules

```text
IF static_outlook = WORSE
AND dynamic_resources = AVAILABLE
AND resources_are_temporary = TRUE
THEN position_character = DYNAMIC_ACTION_REQUIRED
```

```text
IF no_immediate_tactics = TRUE
AND no_urgent_threat = TRUE
AND worst_piece_can_be_improved = TRUE
THEN position_character = STATIC_IMPROVEMENT
```

```text
IF opponent_threat_severity >= HIGH
AND defensive_responses_are_limited = TRUE
THEN position_character = DEFENSIVE_URGENCY
```

---

# 9. Decision Requirement Classifier

## 9.1 Responsibility

Determine which type of decision the player should have prioritized.

## 9.2 Input

* positional assessment;
* threats;
* engine variations;
* position criticality;
* changes relative to the previous position;
* game phase;
* available time, when known.

## 9.3 Output

```json
{
  "primary_decision_type": "PROPHYLACTIC",
  "secondary_decision_types": [
    "DEFENSIVE",
    "STRATEGIC"
  ],
  "required_questions": [
    "What changed after the opponent's last move?",
    "What is the opponent threatening?",
    "Can the threat be neutralized while improving a piece?"
  ],
  "confidence": 0.86
}
```

## 9.4 Classification Cases

### Tactical

Must be assigned when:

* forcing moves exist;
* there are critical captures, checks, or direct threats;
* the difference between candidates depends on concrete calculation;
* a tactic significantly changes the evaluation.

### Strategic

Must be assigned when:

* there are no immediate tactics;
* the decision affects structure, activity, or planning;
* improving pieces is a priority;
* there is a choice between different plans.

### Prophylactic

Must be assigned when:

* the opponent’s last move creates or prepares a threat;
* the opponent’s plan must be neutralized;
* an apparently useful move fails because it ignores the opponent’s intention.

### Dynamic

Must be assigned when:

* the position requires action before the opponent consolidates;
* temporary compensation exists;
* there is a critical pawn break;
* time is more valuable than material.

### Static

Must be assigned when:

* there is no urgency;
* the worst piece can be improved;
* the position allows gradual accumulation;
* the advantage depends on structure or piece quality.

### Technical

Must be assigned when:

* a stable advantage exists;
* the goal is to simplify or convert;
* unnecessary tactical resources should be avoided;
* precision matters more than creativity.

### Practical

Must be assigned when:

* remaining time affects the choice;
* several moves have similar evaluations;
* one move is easier for a human to execute;
* the objectively best move differs from the best practical decision.

---

# 10. Candidate Purpose Analyzer

## 10.1 Responsibility

Determine the chess purpose of each candidate move.

## 10.2 Input

* position;
* MultiPV results;
* features before and after each candidate;
* threats created or neutralized;
* structural changes;
* worst-piece evaluation;
* possible plans.

## 10.3 Output

```json
{
  "move": "Rad1",
  "rank": 1,
  "evaluation": 0.46,
  "purposes": [
    "ACTIVATE_WORST_PIECE",
    "CONTEST_OPEN_FILE",
    "COMPLETE_DEVELOPMENT"
  ],
  "decision_type": "STRATEGIC",
  "risk": "LOW",
  "irreversibility": "LOW",
  "opponent_best_response": "Qe7",
  "human_explanation": "Centralizes the rook and improves coordination without weakening the position."
}
```

## 10.4 Initial Purpose Catalog

```text
CREATE_THREAT
ANSWER_THREAT
IMPROVE_WORST_PIECE
COMPLETE_DEVELOPMENT
GAIN_SPACE
OPEN_FILE
CONTROL_FILE
OPEN_DIAGONAL
CONTROL_DIAGONAL
CREATE_OUTPOST
OCCUPY_OUTPOST
PREPARE_PAWN_BREAK
EXECUTE_PAWN_BREAK
CHANGE_PAWN_STRUCTURE
SIMPLIFY
AVOID_EXCHANGE
ACTIVATE_KING
IMPROVE_KING_SAFETY
REDUCE_OPPONENT_ACTIVITY
MAINTAIN_INITIATIVE
CREATE_COUNTERPLAY
WIN_MATERIAL
SACRIFICE_FOR_ACTIVITY
TRANSITION_TO_ENDGAME
PREVENT_OPPONENT_PLAN
CREATE_SECOND_WEAKNESS
FIX_WEAKNESS
ATTACK_WEAKNESS
IMPROVE_COORDINATION
```

## 10.5 Candidate Comparison

The system must explain qualitative differences:

```json
{
  "comparison": {
    "move_a": "Rad1",
    "move_b": "Ng5",
    "main_difference": "Rad1 addresses the central coordination problem; Ng5 starts a flank operation without sufficient support.",
    "preferred_move": "Rad1"
  }
}
```

---

# 11. Chess Error Diagnosis Engine

## 11.1 Responsibility

Classify the chess error beyond centipawn loss.

## 11.2 Main Categories

```text
TACTICAL_ERROR
STRATEGIC_ERROR
PROPHYLACTIC_ERROR
DYNAMIC_ERROR
STATIC_ERROR
DEFENSIVE_ERROR
TECHNICAL_ERROR
PRACTICAL_ERROR
OPENING_ERROR
ENDGAME_ERROR
```

## 11.3 Initial Subcategories

### Tactical Errors

```text
MISSED_TACTIC
UNSOUND_COMBINATION
MISSED_DEFENSIVE_RESOURCE
CALCULATION_HORIZON_ERROR
MOVE_ORDER_ERROR
OVERLOADED_DEFENDER_IGNORED
PIN_IGNORED
FORK_IGNORED
DISCOVERED_ATTACK_IGNORED
BACK_RANK_ISSUE
```

### Strategic Errors

```text
WRONG_PLAN
WORST_PIECE_NOT_IMPROVED
UNJUSTIFIED_PAWN_MOVE
BAD_PIECE_EXCHANGE
PREMATURE_ATTACK
SPACE_DISADVANTAGE_IGNORED
CENTER_ABANDONED
STRUCTURAL_WEAKNESS_CREATED
WRONG_SIDE_OF_BOARD
```

### Prophylactic Errors

```text
OPPONENT_THREAT_IGNORED
OPPONENT_BREAK_IGNORED
OPPONENT_PLAN_MISREAD
PREVENTABLE_COUNTERPLAY_ALLOWED
```

### Dynamic Errors

```text
FAILED_TO_ACT
INITIATIVE_RELEASED
PREMATURE_SIMPLIFICATION
TEMPORARY_RESOURCE_NOT_USED
MATERIAL_PRIORITIZED_OVER_TIME
```

### Static Errors

```text
UNNECESSARY_COMPLICATION
WEAKNESS_CREATED_WITHOUT_COMPENSATION
INFERIOR_ENDGAME_ACCEPTED
LONG_TERM_FACTOR_MISJUDGED
```

### Technical Errors

```text
ADVANTAGE_NOT_CONVERTED
WRONG_SIMPLIFICATION
COUNTERPLAY_ALLOWED
SECOND_WEAKNESS_NOT_CREATED
KING_NOT_ACTIVATED
PASSED_PAWN_MISHANDLED
```

## 11.4 Output

```json
{
  "primary_error": "PROPHYLACTIC_ERROR",
  "subtype": "OPPONENT_THREAT_IGNORED",
  "severity": "HIGH",
  "evidence": [
    "opponent threatened Qh2+",
    "played move does not create a stronger threat",
    "all safe candidates address the threat"
  ],
  "confidence": 0.91
}
```

---

# 12. Cognitive Hypothesis Engine

## 12.1 Responsibility

Generate limited and explainable hypotheses about decision-process failures.

## 12.2 Main Restriction

The module must not state:

```text
The player thought X.
```

It must state:

```text
The move is compatible with X.
```

or:

```text
The evidence suggests that X may have occurred.
```

## 12.3 Output

```json
{
  "hypotheses": [
    {
      "type": "MISSED_THREAT",
      "confidence": 0.88,
      "evidence_type": "STRONG_INFERENCE",
      "evidence": [
        "played move ignores direct threat",
        "threat was created by previous move",
        "defensive candidates were available"
      ]
    },
    {
      "type": "SINGLE_CANDIDATE",
      "confidence": 0.56,
      "evidence_type": "WEAK_INFERENCE",
      "evidence": [
        "played move follows own plan",
        "alternative defensive candidates were natural"
      ]
    }
  ]
}
```

## 12.4 Initial Heuristic Rules

### Missed Threat

```text
IF opponent_has_direct_threat = TRUE
AND played_move_does_not_answer_threat = TRUE
AND played_move_does_not_create_stronger_threat = TRUE
THEN hypothesis = MISSED_THREAT
```

### Single Candidate

```text
IF played_move_has_clear_single_purpose = TRUE
AND several_natural_candidates_exist = TRUE
AND played_move_fails_to_address_primary_requirement = TRUE
THEN hypothesis = SINGLE_CANDIDATE
```

### Premature Calculation Stop

```text
IF played_line_is_sound_for_n_plies
AND fails_after_forcing_response_at_n_plus_1
AND tactical_motif_is_linear
THEN hypothesis = PREMATURE_CALCULATION_STOP
```

### Final Position Evaluation Error

```text
IF tactical_sequence_was_calculated_plausibly
AND final_material_balance_is_known
AND resulting_position_is_strategically_bad
THEN hypothesis = FINAL_POSITION_EVALUATION_ERROR
```

### Plan Persistence

```text
IF sequence_continues_same_plan
AND position_requirements_changed
AND no_reassessment_move_detected
THEN hypothesis = PLAN_PERSISTENCE
```

### Unjustified Sacrifice

```text
IF material_is_sacrificed
AND no_forced_gain_exists
AND attack_piece_count_is_insufficient
AND engine_compensation_is_low
THEN hypothesis = UNJUSTIFIED_SACRIFICE
```

---

# 13. Sequence Interpretation Engine

## 13.1 Responsibility

Interpret a suboptimal sequence as a single decision-making unit.

## 13.2 Objective

Avoid attributing the deterioration to one isolated move when the actual problem was:

* choosing an incorrect plan;
* persisting with that plan;
* failing to reassess;
* playing a sequence of natural but incoherent moves;
* accumulating concessions.

## 13.3 Output

```json
{
  "sequence_start_ply": 23,
  "sequence_end_ply": 31,
  "sequence_pattern": "PLAN_PERSISTENCE",
  "initial_position_requirement": "central_consolidation",
  "played_plan": "queenside_expansion",
  "required_plan": "neutralize_kingside_pressure",
  "triggering_event": {
    "ply": 22,
    "move": "f5",
    "change": "opponent initiated kingside expansion"
  },
  "cumulative_eval_loss": 1.74,
  "turning_point_ply": 25,
  "explanation": "The player continued the queenside plan after the position's priority shifted to king safety."
}
```

## 13.4 Sequence Types

```text
PLAN_PERSISTENCE
FAILURE_TO_REASSESS
GRADUAL_PASSIVITY
REPEATED_TEMPO_LOSS
WRONG_EXCHANGE_SEQUENCE
KING_SAFETY_NEGLECT
PREMATURE_ATTACK_BUILDUP
STRUCTURAL_DETERIORATION
INACCURATE_SIMPLIFICATION
MISPLACED_PIECE_MANEUVER
FAILED_CONVERSION
```

## 13.5 Detecting a Change in Position Requirements

The system must compare each position with the previous one and identify:

* new threats;
* structural changes;
* opening of lines;
* changes in king safety;
* appearance of a pawn break;
* phase transition;
* disappearance of a dynamic advantage;
* change in the worst piece;
* significant variation among candidate moves.

---

# 14. Player Pattern Engine

## 14.1 Responsibility

Detect recurring patterns across multiple games.

## 14.2 Unit of Analysis

The system must group diagnoses by:

* player;
* error type;
* game phase;
* opening;
* pawn structure;
* time control;
* remaining time;
* color;
* prior evaluation;
* winning or losing position;
* position type;
* recent frequency.

## 14.3 Output

```json
{
  "player_id": 42,
  "pattern": "FAILURE_TO_REASSESS_AFTER_PAWN_BREAK",
  "occurrences": 8,
  "games_analyzed": 24,
  "average_severity": 0.71,
  "average_eval_loss": 1.28,
  "most_common_phase": "MIDDLEGAME",
  "most_common_structure": "CLOSED_CENTER",
  "most_common_time_control": "RAPID",
  "trend": "INCREASING",
  "representative_positions": [
    {
      "game_id": 101,
      "ply": 34
    },
    {
      "game_id": 118,
      "ply": 29
    }
  ]
}
```

## 14.4 Minimum Condition for Declaring a Pattern

A pattern must not be declared from a single observation.

Initial configuration:

```text
minimum_occurrences = 3
minimum_games = 3
minimum_confidence = 0.65
```

## 14.5 Frequency Versus Severity

The system must distinguish between:

```text
Frequent but mild
Infrequent but severe
Frequent and severe
Isolated
```

---

# 15. Pedagogical Recommendation Engine

## 15.1 Responsibility

Convert a diagnosis into a training intervention.

## 15.2 Exercise Types

```text
FIND_BEST_MOVE
IDENTIFY_OPPONENT_THREAT
GENERATE_CANDIDATES
IDENTIFY_WORST_PIECE
CHOOSE_PLAN
STATIC_OR_DYNAMIC
EVALUATE_EXCHANGE
CALCULATE_FORCING_LINE
EVALUATE_FINAL_POSITION
FIND_DEFENSIVE_RESOURCE
REASSESS_AFTER_LAST_MOVE
IDENTIFY_CRITICAL_POSITION
COMPARE_CANDIDATES
PROPHYLACTIC_MOVE
CONVERT_ADVANTAGE
```

## 15.3 Example

```json
{
  "exercise_type": "IDENTIFY_OPPONENT_THREAT",
  "source_game_id": 118,
  "source_ply": 29,
  "prompt": "What threat did Black's last move create?",
  "expected_concepts": [
    "open diagonal",
    "attack on f2",
    "queen entry"
  ],
  "difficulty": "INTERMEDIATE",
  "related_pattern": "MISSED_THREAT"
}
```

## 15.4 Recommendations by Error Type

| Detected error                    | Recommended exercise                               |
| --------------------------------- | -------------------------------------------------- |
| `MISSED_THREAT`                   | Identify the opponent’s threat                     |
| `SINGLE_CANDIDATE`                | Generate three candidates                          |
| `PREMATURE_CALCULATION_STOP`      | Extend the variation by one more move              |
| `FINAL_POSITION_EVALUATION_ERROR` | Evaluate the resulting position                    |
| `WRONG_EXCHANGE`                  | Compare the position before and after the exchange |
| `FAILURE_TO_REASSESS`             | Explain what changed after the last move           |
| `IGNORED_WORST_PIECE`             | Identify and improve the worst piece               |
| `TACTICAL_OVERREACH`              | Count attackers and defenders                      |
| `PASSIVE_DEFENSE`                 | Find an active defensive move                      |
| `PLAN_PERSISTENCE`                | Choose a new plan after a transformation           |

## 15.5 Prioritization

Recommendations must be ordered by:

```text
priority =
frequency_weight
× severity_weight
× recency_weight
× confidence_weight
× trainability_weight
```

---

# 16. Explanation Composer

## 16.1 Responsibility

Generate the final explanation using structured evidence only.

## 16.2 Input

```json
{
  "move_quality": {},
  "critical_position": {},
  "position_assessment": {},
  "decision_requirement": {},
  "candidate_analysis": [],
  "chess_error": {},
  "cognitive_hypotheses": [],
  "sequence_analysis": {},
  "player_patterns": [],
  "training_recommendation": {}
}
```

## 16.3 Expected Output

```text
17.Bxh6?? — Tactical and dynamic error.

The position did not justify an immediate sacrifice. Your development was
incomplete, and Black still had enough defenders around the king.

The move appears to be based on the line gxh6–Qxh6, but Black's best defensive
response interrupts the attack and leaves White a piece down.

The position required completing development and improving coordination. Rad1
was a natural candidate because it activated the rook, reinforced the center,
and maintained pressure without taking irreversible risks.

Main error:
Unjustified sacrifice.

Process hypothesis:
The sequence is compatible with insufficient candidate generation and a
premature stop in calculation. This inference has medium confidence.

Training question:
Before sacrificing on h6, how many attackers, defenders, and potential
reinforcements are actually involved around the king?
```

## 16.4 Required Structure

The explanation must be able to include:

1. objective move quality;
2. what the position required;
3. what changed after the previous move;
4. apparent purpose of the played move;
5. concrete problem;
6. recommended candidate;
7. conceptual difference between the moves;
8. chess error;
9. process hypothesis;
10. confidence level;
11. historical pattern;
12. question or exercise.

## 16.5 LLM Restrictions

The LLM prompt must include:

```text
- Do not invent variations.
- Do not invent threats.
- Do not attribute thoughts with certainty.
- Do not modify engine evaluations.
- Do not add factors that are absent from the structured data.
- Distinguish facts from inferences.
- Express uncertainty when appropriate.
- Prefer pedagogical language over engine terminology.
- Explain concepts rather than only listing moves.
```

---

# 17. Data Model

## 17.1 Table `position_assessments`

```sql
CREATE TABLE position_assessments (
    id                     BIGSERIAL PRIMARY KEY,
    game_id                BIGINT NOT NULL,
    ply                    INTEGER NOT NULL,
    fen                    TEXT NOT NULL,
    side_to_move           VARCHAR(10) NOT NULL,
    game_phase             VARCHAR(20),

    material_score         NUMERIC,
    king_safety_white      NUMERIC,
    king_safety_black      NUMERIC,
    development_white      NUMERIC,
    development_black      NUMERIC,
    space_white            NUMERIC,
    space_black            NUMERIC,
    activity_white         NUMERIC,
    activity_black         NUMERIC,
    initiative_side        VARCHAR(10),
    initiative_strength    NUMERIC,

    worst_piece_white      VARCHAR(10),
    worst_piece_black      VARCHAR(10),

    factors                JSONB,
    opponent_plan          JSONB,
    recommended_priorities JSONB,

    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, ply)
);
```

## 17.2 Table `decision_diagnoses`

```sql
CREATE TABLE decision_diagnoses (
    id                       BIGSERIAL PRIMARY KEY,
    game_id                  BIGINT NOT NULL,
    ply                      INTEGER NOT NULL,

    played_move              VARCHAR(10),
    best_move                VARCHAR(10),
    move_quality             VARCHAR(20),
    centipawn_loss           INTEGER,

    critical_position        BOOLEAN,
    critical_type            VARCHAR(50),

    position_character       VARCHAR(50),
    primary_decision_type    VARCHAR(50),
    secondary_decision_types JSONB,

    primary_error            VARCHAR(50),
    error_subtype            VARCHAR(80),
    severity                 VARCHAR(20),

    evidence                 JSONB,
    confidence               NUMERIC(5,4),

    created_at               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(game_id, ply)
);
```

## 17.3 Table `candidate_diagnoses`

```sql
CREATE TABLE candidate_diagnoses (
    id                    BIGSERIAL PRIMARY KEY,
    decision_diagnosis_id BIGINT NOT NULL,
    move                  VARCHAR(10) NOT NULL,
    engine_rank           INTEGER,
    evaluation            NUMERIC,
    purposes              JSONB,
    decision_type         VARCHAR(50),
    risk_level            VARCHAR(20),
    irreversibility       VARCHAR(20),
    best_response         VARCHAR(10),
    explanation           TEXT
);
```

## 17.4 Table `cognitive_hypotheses`

```sql
CREATE TABLE cognitive_hypotheses (
    id                    BIGSERIAL PRIMARY KEY,
    decision_diagnosis_id BIGINT NOT NULL,
    hypothesis_type       VARCHAR(80) NOT NULL,
    evidence_type         VARCHAR(30) NOT NULL,
    confidence            NUMERIC(5,4) NOT NULL,
    evidence              JSONB,
    player_confirmed      BOOLEAN DEFAULT FALSE,
    player_comment        TEXT
);
```

## 17.5 Table `sequence_diagnoses`

```sql
CREATE TABLE sequence_diagnoses (
    id                   BIGSERIAL PRIMARY KEY,
    game_id              BIGINT NOT NULL,
    start_ply            INTEGER NOT NULL,
    end_ply              INTEGER NOT NULL,
    turning_point_ply    INTEGER,
    sequence_pattern     VARCHAR(80),
    initial_requirement  VARCHAR(80),
    played_plan          VARCHAR(120),
    required_plan        VARCHAR(120),
    triggering_event     JSONB,
    cumulative_eval_loss NUMERIC,
    evidence             JSONB,
    explanation          TEXT,
    confidence           NUMERIC(5,4)
);
```

## 17.6 Table `player_thinking_patterns`

```sql
CREATE TABLE player_thinking_patterns (
    id                        BIGSERIAL PRIMARY KEY,
    player_id                 BIGINT NOT NULL,
    pattern_code              VARCHAR(80) NOT NULL,
    occurrences               INTEGER NOT NULL,
    games_analyzed            INTEGER NOT NULL,
    average_severity          NUMERIC,
    average_eval_loss         NUMERIC,
    most_common_phase         VARCHAR(30),
    most_common_structure     VARCHAR(80),
    most_common_time_control  VARCHAR(30),
    trend                     VARCHAR(20),
    representative_positions JSONB,
    updated_at                TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(player_id, pattern_code)
);
```

## 17.7 Table `training_recommendations`

```sql
CREATE TABLE training_recommendations (
    id                BIGSERIAL PRIMARY KEY,
    player_id         BIGINT NOT NULL,
    source_game_id    BIGINT,
    source_ply        INTEGER,
    related_pattern   VARCHAR(80),
    exercise_type     VARCHAR(80),
    priority          NUMERIC,
    prompt            TEXT,
    expected_concepts JSONB,
    difficulty        VARCHAR(30),
    status            VARCHAR(20) DEFAULT 'PENDING',
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

# 18. Service Contracts

## 18.1 Position Assessment

```python
class PositionAssessmentService:
    def assess(
        self,
        fen: str,
        engine_analysis: EngineAnalysis,
        previous_assessment: PositionAssessment | None
    ) -> PositionAssessment:
        ...
```

## 18.2 Decision Classification

```python
class DecisionRequirementService:
    def classify(
        self,
        assessment: PositionAssessment,
        critical_position: CriticalPosition,
        candidates: list[CandidateAnalysis],
        game_context: GameContext
    ) -> DecisionRequirement:
        ...
```

## 18.3 Error Diagnosis

```python
class ChessErrorDiagnosisService:
    def diagnose(
        self,
        played_move: str,
        assessment: PositionAssessment,
        requirement: DecisionRequirement,
        candidates: list[CandidateAnalysis],
        engine_analysis: EngineAnalysis
    ) -> ChessErrorDiagnosis:
        ...
```

## 18.4 Cognitive Hypotheses

```python
class CognitiveHypothesisService:
    def infer(
        self,
        diagnosis: ChessErrorDiagnosis,
        sequence_context: SequenceContext,
        player_context: PlayerContext | None
    ) -> list[CognitiveHypothesis]:
        ...
```

## 18.5 Pedagogical Recommendations

```python
class TrainingRecommendationService:
    def generate(
        self,
        diagnosis: ChessErrorDiagnosis,
        hypotheses: list[CognitiveHypothesis],
        patterns: list[PlayerPattern]
    ) -> list[TrainingRecommendation]:
        ...
```

---

# 19. Main DTOs

```python
from dataclasses import dataclass
from enum import Enum


class EvidenceType(str, Enum):
    FACT = "FACT"
    STRONG_INFERENCE = "STRONG_INFERENCE"
    WEAK_INFERENCE = "WEAK_INFERENCE"
    PLAYER_CONFIRMED = "PLAYER_CONFIRMED"


class PositionCharacter(str, Enum):
    TACTICAL_RESOLUTION = "TACTICAL_RESOLUTION"
    DYNAMIC_ACTION_REQUIRED = "DYNAMIC_ACTION_REQUIRED"
    STATIC_IMPROVEMENT = "STATIC_IMPROVEMENT"
    DEFENSIVE_URGENCY = "DEFENSIVE_URGENCY"
    PROPHYLACTIC_DECISION = "PROPHYLACTIC_DECISION"
    TECHNICAL_CONVERSION = "TECHNICAL_CONVERSION"
    TRANSITION_DECISION = "TRANSITION_DECISION"
    BALANCED_FLEXIBLE = "BALANCED_FLEXIBLE"


@dataclass
class Evidence:
    description: str
    evidence_type: EvidenceType
    source: str
    confidence: float


@dataclass
class PositionalFactor:
    name: str
    white_score: float | None
    black_score: float | None
    evidence: list[Evidence]


@dataclass
class PositionAssessment:
    game_id: int
    ply: int
    fen: str
    factors: list[PositionalFactor]
    worst_piece_white: str | None
    worst_piece_black: str | None
    opponent_plan: list[str]
    recommended_priorities: list[str]


@dataclass
class CandidateDiagnosis:
    move: str
    engine_rank: int
    evaluation: float
    purposes: list[str]
    decision_type: str
    risk_level: str
    irreversibility: str
    explanation: str


@dataclass
class CognitiveHypothesis:
    hypothesis_type: str
    evidence_type: EvidenceType
    confidence: float
    evidence: list[Evidence]
```

---

# 20. Execution Pipeline

## 20.1 Per Critical Position

```text
1. Retrieve the position and context.
2. Obtain MultiPV analysis.
3. Calculate positional features.
4. Compare features with the previous position.
5. Evaluate static-dynamic character.
6. Classify the required decision type.
7. Analyze the purpose of candidate moves.
8. Diagnose the played move.
9. Generate process hypotheses.
10. Associate the position with a suboptimal sequence.
11. Update player patterns.
12. Generate a pedagogical recommendation.
13. Compose the final explanation.
```

## 20.2 Per Game

```text
1. Analyze all positions.
2. Detect critical positions.
3. Detect suboptimal sequences.
4. Diagnose individual decisions.
5. Interpret complete sequences.
6. Select pedagogically relevant errors.
7. Update longitudinal patterns.
8. Generate a learning summary.
```

---

# 21. Pedagogical Game Summary

The system must generate a summary such as:

```json
{
  "game_id": 118,
  "main_turning_point": {
    "ply": 29,
    "move": "Ng5",
    "error": "OPPONENT_THREAT_IGNORED"
  },
  "main_sequence_problem": {
    "start_ply": 25,
    "end_ply": 31,
    "pattern": "PLAN_PERSISTENCE"
  },
  "strengths": [
    "good opening development",
    "correct identification of queenside space advantage"
  ],
  "improvement_areas": [
    "reassess after opponent pawn breaks",
    "identify opponent threats before continuing own plan"
  ],
  "recommended_exercises": [
    "IDENTIFY_OPPONENT_THREAT",
    "REASSESS_AFTER_LAST_MOVE"
  ]
}
```

---

# 22. User Interface

## 22.1 Critical Position View

Must display:

* board;
* played move;
* candidate moves;
* evaluation;
* reason for criticality;
* decision type;
* positional factors;
* opponent threat;
* worst piece;
* purpose of each candidate;
* main error;
* process hypothesis;
* confidence;
* pedagogical question.

## 22.2 Sequence View

Must display:

* sequence start and end;
* cumulative evaluation loss;
* plan followed;
* required plan;
* event that changed the position;
* point at which reassessment was required;
* global explanation;
* alternative moves.

## 22.3 Pattern View

| Pattern                | Frequency | Severity | Trend      | Exercise          |
| ---------------------- | --------: | -------: | ---------- | ----------------- |
| Ignoring threats       |         7 |     High | Increasing | Identify threat   |
| Persisting with a plan |         5 |   Medium | Stable     | Reassess position |
| Unjustified sacrifices |         3 |     High | Decreasing | Count attackers   |

## 22.4 Player Confirmation

The user must be able to answer:

```text
- I did not see the threat.
- I saw the threat, but evaluated it incorrectly.
- I calculated the line, but missed the final response.
- I played too quickly.
- I continued with my original plan.
- Other.
```

The answer must be stored as:

```text
PLAYER_CONFIRMED
```

This will allow the system to validate or correct generated hypotheses.

---

# 23. Confidence Rules

## 23.1 Scale

```text
0.00–0.39 = low
0.40–0.64 = medium
0.65–0.84 = high
0.85–1.00 = very high
```

## 23.2 Restrictions

* Hypotheses with confidence below `0.40` must not be shown by default.
* Hypotheses between `0.40` and `0.64` must be expressed as possibilities.
* Hypotheses above `0.65` may be expressed as probable conclusions.
* Only player confirmation may be labeled as subjective certainty.

---

# 24. Implementation Strategy

## Phase 1 — Explainable Rules

Implement without complex machine learning:

* basic positional evaluation;
* worst-piece identification;
* opponent-threat detection;
* tactical, strategic, and prophylactic classification;
* static-dynamic character;
* candidate-purpose analysis;
* error taxonomy;
* rule-based hypotheses;
* structured explanations.

## Phase 2 — Sequences and Patterns

Add:

* sequence interpretation;
* plan-change detection;
* plan persistence;
* reassessment detection;
* player-level aggregation;
* personalized exercises.

## Phase 3 — User and Coach Validation

Add:

* player confirmation;
* manual review;
* label correction;
* comparison between hypotheses and player responses;
* validated dataset.

## Phase 4 — Supervised Machine Learning

Train models for:

* decision type;
* strategic error;
* cognitive hypothesis;
* sequence pattern;
* pedagogical recommendation.

Models must be trained only on reviewed or confirmed labels.

## Phase 5 — Personalization

Add:

* player profile;
* estimated skill level;
* dominant errors;
* adaptive difficulty;
* explanation selection;
* improvement tracking.

---

# 25. Recommended MVP

The MVP must implement:

1. structured evaluation of ten factors;
2. worst-piece identification;
3. opponent-threat detection;
4. decision-type classification;
5. static or dynamic evaluation;
6. purpose analysis for three MultiPV candidates;
7. chess-error classification;
8. five initial cognitive hypotheses;
9. structured explanation;
10. generation of one exercise.

## Hypotheses Included in the MVP

```text
MISSED_THREAT
SINGLE_CANDIDATE
PREMATURE_CALCULATION_STOP
FAILURE_TO_REASSESS
UNJUSTIFIED_SACRIFICE
```

## Factors Included in the MVP

```text
MATERIAL
KING_SAFETY
DEVELOPMENT
SPACE
CENTER_CONTROL
PAWN_STRUCTURE
PIECE_ACTIVITY
PIECE_COORDINATION
INITIATIVE
WORST_PIECE
```

---

# 26. Acceptance Criteria

## 26.1 Diagnosis

Given a critical position, the system must:

* identify at least one decision type;
* describe at least two relevant factors;
* analyze three candidate moves when available;
* assign a purpose to each candidate;
* classify the main error;
* present evidence;
* assign confidence;
* distinguish fact from inference.

## 26.2 Sequences

Given a suboptimal sequence, the system must:

* identify its start and end;
* detect the event that changed the position;
* describe the plan followed;
* describe the required plan;
* measure cumulative evaluation loss;
* detect persistence or failure to reassess.

## 26.3 Explanation

The explanation must:

* be consistent with engine evaluation;
* contain no invented variations;
* avoid presenting mental states as facts;
* explain why one candidate is better;
* include a question or exercise;
* use language understandable to an intermediate player.

## 26.4 Patterns

A pattern must only be shown when:

* it appears in at least three games;
* it exceeds the confidence threshold;
* it includes representative positions;
* it has a trainable recommendation.

---

# 27. Testing

## 27.1 Unit Tests

Create tests for:

* static-dynamic classification;
* worst-piece identification;
* threat detection;
* candidate-purpose analysis;
* error taxonomy;
* confidence calculation;
* pattern grouping;
* exercise selection.

## 27.2 Integration Tests

Minimum cases:

```text
1. Direct threat ignored.
2. Incorrect sacrifice.
3. Unfavorable piece exchange.
4. Statically worse position with a dynamic resource.
5. Quiet position where the worst piece must be improved.
6. Incorrect-plan sequence.
7. Failure to reassess after a pawn break.
8. Advantage not converted.
9. Passive defense when active defense was available.
10. Error confirmed by the player.
```

## 27.3 Golden Tests

Create known positions with expected outputs:

```text
tests/golden/
    missed_threat.json
    dynamic_action_required.json
    improve_worst_piece.json
    unjustified_sacrifice.json
    plan_persistence.json
    wrong_exchange.json
```

Each file must contain:

```json
{
  "fen": "...",
  "played_move": "...",
  "expected_decision_type": "...",
  "expected_error": "...",
  "expected_evidence": [],
  "minimum_confidence": 0.70
}
```

---

# 28. Metrics

## 28.1 Technical Metrics

```text
Decision Type Accuracy
Chess Error Macro F1
Cognitive Hypothesis Precision
Sequence Pattern Macro F1
Confidence Calibration Error
Unsupported Explanation Rate
```

## 28.2 Pedagogical Metrics

```text
Coach Agreement Rate
Player Confirmation Rate
Exercise Relevance Rate
Repeated Error Reduction
Critical Position Recognition Improvement
Candidate Generation Improvement
```

## 28.3 Critical Metric

The primary metric must not be accuracy alone.

The following must also be measured:

```text
Unsupported Explanation Rate
```

Definition:

```text
Percentage of generated statements that cannot be linked to structured
evidence, engine analysis, or player confirmation.
```

Initial target:

```text
Unsupported Explanation Rate < 5%
```

---

# 29. Configuration

```yaml
decision_diagnosis:
  enabled: true

  multipv:
    candidates: 3

  confidence:
    minimum_visible: 0.40
    high_threshold: 0.65
    very_high_threshold: 0.85

  patterns:
    minimum_occurrences: 3
    minimum_games: 3

  llm:
    require_structured_evidence: true
    allow_unverified_inference: false

  training:
    generate_exercise: true
    max_recommendations_per_game: 3
```

---

# 30. Expected Result

ChessInsight must evolve from an analyzer centered on the question:

```text
Was the move good or bad?
```

into a system capable of answering:

```text
What did the position require?

What changed after the last move?

Which candidate moves were reasonable?

What was the purpose of each candidate?

Why did the selected move fail to meet the position’s requirements?

Was the error tactical, strategic, prophylactic, dynamic, or technical?

Which decision-process weakness is compatible with the evidence?

Is this a recurring pattern?

What should the player train?
```

The final product must prioritize explainable diagnosis and player learning over the simple reproduction of engine evaluations.
