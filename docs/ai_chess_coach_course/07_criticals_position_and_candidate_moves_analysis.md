# ChessInsight — Functional Specification

## Critical Position Detection, Candidate Move Analysis, and Suboptimal Move Sequences

## 1. Purpose

Extend ChessInsight so that it does not merely classify moves as `good`, `inaccuracy`, `mistake`, or `blunder`, but can also:

* detect critical positions;
* explain why a position is critical;
* distinguish static and dynamic factors;
* identify candidate moves;
* explain the tactical and strategic ideas behind each candidate;
* detect sequences of suboptimal moves;
* locate the conceptual origin of an error;
* reconstruct a useful thinking process for the player;
* personalize explanations according to Elo level and time control.

The system should primarily answer this question:

> How should the player have thought about this position?

It should not be limited to answering:

> What was the engine’s best move?

---

# 2. Functional Scope

The system will receive the following inputs:

* a chess game in PGN format;
* optionally, a position in FEN format;
* both players’ Elo ratings;
* time control;
* remaining clock times, when available;
* identifier of the player being analyzed;
* previously generated Stockfish analysis;
* features already extracted by ChessInsight;
* prediction from the current move-quality classification model.

The system will generate:

1. detected critical positions;
2. criticality level;
3. criticality reasons;
4. static evaluation;
5. dynamic evaluation;
6. candidate moves;
7. conceptual classification of candidate moves;
8. comparison with the move played;
9. suboptimal move sequences;
10. decision-process diagnosis;
11. pedagogical explanation adapted to the player;
12. positions recommended for training.

---

# 3. Design Principles

## 3.1 Separation Between Facts and Interpretations

The system must explicitly distinguish between:

### Verifiable facts

* material balance;
* engine evaluation;
* variations;
* threats;
* captures;
* checks;
* mobility;
* piece activity;
* pawn structure;
* king safety;
* weak squares;
* passed pawns;
* evaluation changes;
* calculation depth.

### Interpretations

* initiative;
* compensation;
* need for dynamic play;
* static advantage;
* incorrect plan;
* passive move;
* loss of coordination;
* favorable simplification;
* thematic pawn break.

Every interpretation must be supported by one or more pieces of evidence.

---

## 3.2 The LLM Must Not Determine Chess Truth

The LLM must be used only to:

* write explanations;
* summarize evidence;
* adapt language to the player’s level;
* reconstruct the thinking process;
* transform structured results into understandable commentary.

The LLM must not:

* choose the best move independently;
* invent variations;
* calculate evaluations;
* decide whether a position is critical without supporting evidence;
* generate candidate moves without Stockfish or rule-engine support.

---

## 3.3 Preserve the Existing Prediction Model

The current move-type prediction model must remain part of the system.

Its role will be to:

* estimate probabilities for `good`, `inaccuracy`, `mistake`, and `blunder`;
* estimate expected severity;
* provide a human-difficulty signal;
* contribute to critical-position detection;
* prioritize positions for training;
* identify deterioration sequences;
* detect recurring patterns by Elo band.

---

# 4. Functional Architecture

```text
PGN / FEN
   ↓
Position Extractor
   ↓
Feature Engine
   ├── Tactical Features
   ├── Static Features
   ├── Dynamic Features
   ├── Context Features
   └── Player Features
   ↓
Stockfish MultiPV
   ↓
Move Quality Prediction Model
   ↓
Critical Position Detector
   ↓
Suboptimal Sequence Detector
   ↓
Static Evaluation Engine
   ↓
Dynamic Evaluation Engine
   ↓
Candidate Move Classifier
   ↓
Decision Failure Diagnosis
   ↓
Training Position Selector
   ↓
Explanation Planner
   ↓
LLM Verbalizer
   ↓
Critic / Validation Layer
```

---

# 5. Functional Modules

## 5.1 Position Extractor

Responsibilities:

* iterate through the game;
* reconstruct every position;
* generate the FEN for each ply;
* identify the side to move;
* register the move played;
* store temporal and game context.

### Input

* PGN.

### Output

```json
{
  "gameId": 1001,
  "ply": 35,
  "fen": "...",
  "sideToMove": "white",
  "playedMoveUci": "f3g5",
  "playedMoveSan": "Ng5",
  "phase": "middlegame",
  "whiteElo": 1600,
  "blackElo": 1580,
  "timeControl": "600",
  "whiteTimeRemainingSeconds": 183,
  "blackTimeRemainingSeconds": 204
}
```

---

## 5.2 Feature Engine

The engine must produce features grouped by dimension.

### Tactical features

* available checks;
* available captures;
* direct threats;
* hanging pieces;
* overloaded pieces;
* pins;
* skewers;
* discovered attacks;
* double attacks;
* tactical alignments;
* forcing sequences;
* required tactical depth.

### Static features

* material balance;
* pawn structure;
* isolated pawns;
* doubled pawns;
* backward pawns;
* passed pawns;
* pawn majorities;
* weak squares;
* open files;
* diagonals;
* bishop pair;
* piece quality;
* space advantage;
* color-complex weaknesses;
* favorable endgame after a queen exchange.

### Dynamic features

* initiative;
* development advantage;
* mobility;
* coordination;
* pressure against the king;
* piece activity;
* number of forcing moves;
* attacking potential;
* available pawn break;
* tempo advantage;
* initiative stability.

### Contextual features

* game phase;
* Elo;
* time control;
* remaining time;
* complexity;
* number of reasonable candidate moves;
* difference between the best candidate moves;
* previous move;
* changes caused by the previous move.

---

## 5.3 Stockfish MultiPV Analyzer

Suggested initial configuration:

```text
Engine: Stockfish 17.1
MultiPV: 5
Minimum depth: 15
Configurable depth
```

For each candidate, it must return:

* rank;
* UCI move;
* SAN move;
* evaluation;
* search depth;
* principal variation;
* centipawn loss relative to the top move;
* mate score, when applicable;
* evaluation stability across different depths.

Example:

```json
{
  "move": "d4d5",
  "san": "d5",
  "rank": 1,
  "evaluation": 0.42,
  "depth": 18,
  "principalVariation": ["d5", "exd5", "Nxd5"],
  "centipawnLossFromBest": 0
}
```

---

# 6. Integration of the Existing Prediction Model

## 6.1 Expected Output

```json
{
  "goodProbability": 0.14,
  "inaccuracyProbability": 0.21,
  "mistakeProbability": 0.49,
  "blunderProbability": 0.16,
  "predictedLabel": "mistake",
  "expectedSeverity": 1.67,
  "modelVersion": "xgb_v3"
}
```

## 6.2 Expected Severity

```text
expectedSeverity =
    0 × P(good)
  + 1 × P(inaccuracy)
  + 2 × P(mistake)
  + 3 × P(blunder)
```

## 6.3 Functional Uses

The model must be used as:

* a human-error-risk signal;
* an indicator of difficulty for the Elo band;
* an input feature for criticality detection;
* a trigger for deeper analysis;
* a signal for detecting suboptimal sequences;
* a criterion for training-position prioritization.

The model must not determine by itself that a position is critical.

---

# 7. Critical Position Detector

## 7.1 Functional Definition

A position is critical when a decision may materially change:

* the evaluation;
* king safety;
* pawn structure;
* material balance;
* initiative;
* strategic plan;
* the character of the position;
* simplification possibilities;
* calculation requirements.

## 7.2 Criticality Reasons

```text
TacticalThreat
OnlyMove
ForcedSequence
KingSafetyChange
PawnBreakAvailable
MaterialTransformation
QueenExchangeDecision
StructuralTransformation
InitiativeTransfer
PlanTransition
EvaluationInstability
IrreversiblePawnMove
CandidateDivergence
HumanErrorRisk
```

## 7.3 Initial Scoring Formula

```text
criticalityScore =
    tacticalThreatScore
  + onlyMoveScore
  + forcingSequenceScore
  + kingSafetyScore
  + structuralTransformationScore
  + candidateDivergenceScore
  + evaluationInstabilityScore
  + initiativeTransferScore
  + humanErrorRiskScore
```

## 7.4 Classification

```text
0.0 – 2.9  Routine
3.0 – 5.9  Relevant
6.0 – 8.4  Critical
8.5 – 10.0 HighlyCritical
```

## 7.5 Example Output

```json
{
  "critical": true,
  "score": 7.8,
  "level": "Critical",
  "reasons": [
    {
      "type": "PawnBreakAvailable",
      "weight": 1.8,
      "description": "The central break ...d5 can open the position."
    },
    {
      "type": "KingSafetyChange",
      "weight": 2.1,
      "description": "The white king remains in the center."
    },
    {
      "type": "CandidateDivergence",
      "weight": 1.4,
      "description": "The main candidate moves represent different plans."
    }
  ]
}
```

---

# 8. Static Evaluation

## 8.1 Objective

Answer:

> If the position stabilized and immediate tactics disappeared, which side would have better long-term prospects?

## 8.2 Factors

```text
Material
KingSafety
PawnStructure
PieceQuality
Space
WeakSquares
OpenFiles
BishopPair
PassedPawns
EndgameProspects
QueenExchangeEffect
```

## 8.3 Output

```json
{
  "favoredSide": "white",
  "score": 0.8,
  "confidence": 0.74,
  "factors": [
    {
      "type": "PawnStructure",
      "favoredSide": "white",
      "score": 0.6,
      "evidence": [
        "Black has an isolated pawn on d5.",
        "The d4 square may become an outpost."
      ]
    }
  ]
}
```

---

# 9. Dynamic Evaluation

## 9.1 Objective

Answer:

> Which temporary factors may alter the static evaluation?

## 9.2 Factors

```text
Initiative
Development
Tempo
Coordination
TacticalPressure
AttackPotential
ForcingMoves
KingExposure
DynamicCompensation
```

## 9.3 Output

```json
{
  "favoredSide": "black",
  "score": 1.1,
  "confidence": 0.71,
  "factors": [
    {
      "type": "Initiative",
      "favoredSide": "black",
      "score": 0.7,
      "evidence": [
        "Black has two forcing moves available.",
        "Three black pieces participate in the pressure against the king."
      ]
    }
  ]
}
```

---

# 10. Conceptual Integration of Dorfman

Implement an evaluation inspired by Dorfman’s hierarchy:

1. king safety;
2. material balance;
3. effect of a queen exchange;
4. pawn structure.

Output:

```json
{
  "staticAdvantage": "white",
  "requiresDynamicAction": true,
  "sideThatRequiresDynamicAction": "black",
  "reason": "Black is statically worse but has initiative and a development advantage."
}
```

Initial rule:

```text
If one side is statically worse:
    favor dynamic and transformative candidate moves.

If one side is statically better:
    favor consolidation, simplification, or gradual improvement,
    unless a concrete tactic exists.
```

This rule must be treated as a heuristic, not as an absolute principle.

---

# 11. Conceptual Integration of Alvira

The system must reconstruct the player’s thinking process:

```text
1. What changed after the previous move?
2. What is the opponent threatening?
3. Are there checks, captures, or threats?
4. Is the position critical?
5. What are the candidate moves?
6. Which plan does each candidate represent?
7. Which variations require calculation?
8. Which move best addresses the demands of the position?
```

Output:

```json
{
  "lastMoveImpact": "The previous move weakened e5 and left the king uncastled.",
  "opponentThreat": "Black threatens to open the center with ...d5.",
  "forcingMoves": ["Bxf7+", "d4"],
  "decisionQuestion": "Should White close the center, simplify, or complete development?"
}
```

---

# 12. Conceptual Integration of Beim

The system must detect dynamic imbalances:

```text
Material
Development
Initiative
KingSafety
Space
PawnStructure
PieceCoordination
WeakSquares
OpenFiles
PassedPawn
```

It must also identify compensation.

Example:

```json
{
  "materialBalance": -1.0,
  "dynamicCompensation": {
    "initiative": 0.4,
    "development": 0.3,
    "kingExposure": 0.4
  },
  "summary": "Black sacrificed a pawn but obtained sufficient dynamic compensation."
}
```

These values are descriptive and must not be presented as exact mathematical equivalents.

---

# 13. Candidate Generation and Classification

## 13.1 Candidate Sources

Use:

* Stockfish MultiPV;
* checks;
* captures;
* threats;
* defensive moves;
* pawn breaks;
* piece-improvement moves;
* simplifications;
* prophylaxis;
* consolidation.

## 13.2 Candidate Types

```text
Forcing
Defensive
Tactical
Positional
Dynamic
Simplifying
Prophylactic
Structural
Improving
Consolidating
```

## 13.3 Structure

```json
{
  "move": "d5",
  "uci": "d6d5",
  "rank": 1,
  "candidateType": ["Dynamic", "Structural"],
  "engineEvaluation": 0.42,
  "strategicIdea": "Open the center before the opponent completes development.",
  "tacticalIdea": "The white queen becomes exposed after the center opens.",
  "argumentsFor": [
    "Activates the bishop on c8.",
    "Uses the development advantage."
  ],
  "argumentsAgainst": [
    "Weakens the e5 square.",
    "Requires concrete calculation."
  ],
  "risk": "Medium",
  "calculationRequirement": "High"
}
```

---

# 14. Comparison With the Move Played

For every critical position, compare:

```text
Best candidate
Alternative candidates
Played move
Conceptual difference
Tactical difference
Strategic difference
Practical difficulty
```

Example structured explanation:

```json
{
  "playedMove": "Nf1",
  "playedMoveEvaluation": -0.7,
  "bestMove": "d4",
  "bestMoveEvaluation": 0.3,
  "difference": {
    "tactical": "Nf1 does not address the pressure on e4.",
    "strategic": "The move concedes the center and the initiative.",
    "dynamic": "It allows the opponent to play ...d5 with tempo."
  }
}
```

---

# 15. Suboptimal Sequence Detector

## 15.1 Objective

Detect groups of moves that, when considered together, represent strategic or tactical deterioration.

## 15.2 Initial Patterns

```text
RepeatedPassiveMoves
IgnoredThreat
FailedDevelopment
PrematureAttack
StructuralDeterioration
LossOfInitiative
WrongPieceExchanges
PlanInconsistency
TacticalDrift
TimeWasting
FailureToExploitAdvantage
ProgressiveKingExposure
```

## 15.3 Initial Rules

A sequence may be detected when:

* two or more suboptimal moves occur within a window of 3 to 8 moves;
* the evaluation worsens cumulatively;
* the same pattern repeats;
* initiative is progressively lost;
* a previously created weakness produces a later tactical problem;
* the final move reveals a problem that started earlier.

## 15.4 Output

```json
{
  "startPly": 31,
  "endPly": 39,
  "pattern": "RepeatedPassiveMoves",
  "moves": ["h3", "Bh2", "Re1", "Nf1"],
  "accumulatedLoss": 1.4,
  "originPositionPly": 31,
  "manifestationPly": 39,
  "summary": "The deterioration began with a passive sequence that allowed the opponent to accumulate initiative."
}
```

---

# 16. Origin, Decision, and Manifestation of the Error

The system must distinguish between:

```text
Origin Position:
the moment when the conceptual problem begins.

Decision Position:
the moment when a critical choice was available.

Manifestation Position:
the moment when the tactical loss or major evaluation drop appears.
```

Example:

```json
{
  "originPly": 26,
  "decisionPly": 30,
  "manifestationPly": 34,
  "diagnosis": "The tactical error on move 34 was a consequence of allowing the central break on move 26."
}
```

---

# 17. Decision-Failure Diagnosis

Initial taxonomy:

```text
TacticalOversight
IncorrectEvaluation
MissedCandidate
WrongPlan
FailureToDetectCriticalPosition
MisjudgedExchange
IgnoredDynamicFactor
OverestimatedAttack
UnderestimatedThreat
PrematureSimplification
FailureToConsolidate
PassiveDefense
PoorPieceCoordination
StructuralMisjudgment
```

Example:

```json
{
  "severity": "mistake",
  "primaryCause": "FailureToDetectCriticalPosition",
  "secondaryCause": "IgnoredDynamicFactor",
  "explanation": "The player treated the position as routine and failed to consider the immediate central break."
}
```

---

# 18. Training Prioritization

Calculate:

```text
trainingPriority =
    criticalityScore
  × predictedErrorProbability
  × recurrenceFactor
  × instructionalValue
```

Prioritize positions where:

* the position was critical;
* the player made a suboptimal move;
* the pattern is recurrent;
* conceptually different candidate moves existed;
* the explanation is transferable;
* the position requires a decision appropriate to the player’s level.

Output:

```json
{
  "trainingPriority": 8.7,
  "recommended": true,
  "trainingTheme": "Central pawn break with a development advantage",
  "recurrenceCount": 6
}
```

---

# 19. Personalization

The system must adapt:

* explanation depth;
* number of variations;
* terminology;
* difficulty;
* number of candidate moves shown;
* tactical or strategic emphasis.

## Suggested Profile

```json
{
  "playerId": "cmess1315",
  "eloBand": "1600-1799",
  "preferredTimeControl": "rapid",
  "explanationLevel": "intermediate",
  "maxCandidates": 3,
  "maxVariationDepth": 6
}
```

---

# 20. Minimum Data Model

## Table `positions`

```sql
id
game_id
ply
fen
side_to_move
played_move_uci
played_move_san
engine_eval_before
engine_eval_after
phase
criticality_score
criticality_level
created_at
```

## Table `position_features`

```sql
id
position_id
feature_group
feature_name
feature_value
favored_side
confidence
source
```

## Table `move_quality_predictions`

```sql
id
position_id
good_probability
inaccuracy_probability
mistake_probability
blunder_probability
predicted_label
expected_severity
model_version
```

## Table `criticality_reasons`

```sql
id
position_id
reason_type
weight
description
confidence
```

## Table `candidate_moves`

```sql
id
position_id
move_uci
move_san
multipv_rank
engine_eval
centipawn_loss
candidate_type
risk_score
calculation_requirement
```

## Table `candidate_arguments`

```sql
id
candidate_id
argument_type
dimension
description
confidence
evidence_source
```

## Table `suboptimal_sequences`

```sql
id
game_id
start_ply
end_ply
origin_ply
decision_ply
manifestation_ply
pattern
accumulated_loss
confidence
summary
```

## Table `decision_diagnoses`

```sql
id
position_id
primary_cause
secondary_cause
severity
description
confidence
```

## Table `training_positions`

```sql
id
position_id
player_id
priority_score
training_theme
recurrence_count
recommended
```

---

# 21. Suggested Services

```csharp
public interface IPositionExtractor
{
    Task<IReadOnlyList<PositionContext>> ExtractAsync(string pgn);
}

public interface IFeatureExtractor
{
    Task<PositionFeatures> ExtractAsync(PositionContext position);
}

public interface IEngineAnalyzer
{
    Task<MultiPvAnalysis> AnalyzeAsync(
        PositionContext position,
        int multiPv,
        int depth);
}

public interface IMoveQualityPredictor
{
    Task<MoveQualityPrediction> PredictAsync(PositionFeatures features);
}

public interface ICriticalPositionDetector
{
    Task<CriticalityAssessment> EvaluateAsync(
        PositionContext position,
        PositionFeatures features,
        MultiPvAnalysis engineAnalysis,
        MoveQualityPrediction prediction);
}

public interface IStaticEvaluationService
{
    Task<StaticEvaluation> EvaluateAsync(
        PositionContext position,
        PositionFeatures features);
}

public interface IDynamicEvaluationService
{
    Task<DynamicEvaluation> EvaluateAsync(
        PositionContext position,
        PositionFeatures features,
        MultiPvAnalysis engineAnalysis);
}

public interface ICandidateClassifier
{
    Task<IReadOnlyList<CandidateMoveAnalysis>> ClassifyAsync(
        PositionContext position,
        MultiPvAnalysis analysis,
        PositionFeatures features);
}

public interface ISuboptimalSequenceDetector
{
    Task<IReadOnlyList<SuboptimalSequence>> DetectAsync(
        IReadOnlyList<AnalyzedDecision> decisions);
}

public interface IDecisionDiagnosisService
{
    Task<DecisionDiagnosis> DiagnoseAsync(
        AnalyzedDecision decision);
}

public interface ITrainingPositionSelector
{
    Task<TrainingPositionAssessment> EvaluateAsync(
        AnalyzedDecision decision,
        PlayerProfile profile);
}

public interface IExplanationPlanner
{
    Task<ExplanationPlan> BuildAsync(
        AnalyzedDecision decision,
        PlayerProfile profile);
}

public interface IExplanationGenerator
{
    Task<string> GenerateAsync(ExplanationPlan plan);
}

public interface IExplanationValidator
{
    Task<ValidationResult> ValidateAsync(
        ExplanationPlan plan,
        string generatedText);
}
```

---

# 22. Suggested Functional API

## Analyze Game

```http
POST /api/analysis/games
```

### Request

```json
{
  "pgn": "...",
  "playerToAnalyze": "white",
  "playerProfile": {
    "eloBand": "1600-1799",
    "timeControl": "rapid",
    "explanationLevel": "intermediate"
  },
  "options": {
    "multiPv": 5,
    "depth": 18,
    "detectCriticalPositions": true,
    "detectSuboptimalSequences": true,
    "generateExplanations": true
  }
}
```

### Response

```json
{
  "gameId": 1001,
  "summary": {
    "criticalPositions": 4,
    "suboptimalSequences": 2,
    "mistakes": 3,
    "blunders": 1
  },
  "positions": [],
  "sequences": [],
  "trainingRecommendations": []
}
```

---

# 23. MVP

## Phase 1

Implement:

* position extraction;
* Stockfish MultiPV;
* integration of the existing prediction model;
* rule-based criticality detection;
* simple candidate classification;
* comparison between the played move and candidate moves;
* structured explanation without an LLM.

## Initial Detectors

```text
TacticalThreat
OnlyMove
PawnBreakAvailable
QueenExchangeDecision
StructuralTransformation
KingSafetyChange
EvaluationInstability
CandidateDivergence
HumanErrorRisk
```

## Phase 2

Add:

* static evaluation;
* dynamic evaluation;
* sequence detector;
* origin, decision, and manifestation analysis;
* cause diagnosis.

## Phase 3

Add:

* Elo-based personalization;
* training-position selection;
* recurring-pattern detection;
* LLM verbalizer;
* critical validation layer.

---

# 24. Acceptance Criteria

## AC-01

Given a valid PGN, the system must reconstruct every position.

## AC-02

For every position, the system must obtain at least three candidate moves through MultiPV.

## AC-03

The system must integrate the existing prediction model without replacing Stockfish evaluation.

## AC-04

The system must assign a criticality level and at least one verifiable criticality reason.

## AC-05

The system must distinguish between static and dynamic evaluation.

## AC-06

The system must explain the difference between the played move and the primary candidate.

## AC-07

The system must detect sequences of at least two related suboptimal moves.

## AC-08

The system must distinguish origin, decision, and manifestation when applicable.

## AC-09

Every conceptual statement must be supported by evidence.

## AC-10

The LLM must not introduce variations that are absent from the structured analysis.

---

# 25. Minimum Test Cases

## Case 1 — Critical Position With the Best Move Found

Expected result:

* position classified as critical;
* move classified as `good`;
* explanation recognizes the correct decision;
* no error diagnosis generated.

## Case 2 — Immediate Tactical Error

Expected result:

* high criticality;
* tactical threat detected;
* defensive candidate identified;
* cause classified as `TacticalOversight`.

## Case 3 — Passive Sequence

Expected result:

* several inaccuracies;
* pattern classified as `RepeatedPassiveMoves`;
* progressive loss of initiative;
* origin identified before the final blunder.

## Case 4 — Static Advantage Versus Dynamic Compensation

Expected result:

* static advantage for one side;
* dynamic initiative for the other;
* candidate moves differentiated between consolidation and dynamic action.

## Case 5 — Simple Position With a Suboptimal Move

Expected result:

* low or medium criticality;
* move classified as `mistake`;
* no confusion between move quality and position criticality.

---

# 26. Constraints

* Do not use the LLM as a chess engine.
* Do not infer concepts without evidence.
* Do not assume the engine’s first move is always the only valid explanation.
* Do not treat every inaccuracy as an independent event.
* Do not confuse an evaluation drop with the origin of the problem.
* Do not present conceptual scores as exact mathematical equivalences.
* Maintain full traceability between explanations, features, and evidence sources.

---

# 27. Final Product Definition

ChessInsight must detect positions in which a decision materially changes the evaluation or the nature of the game.

For every critical position, it must:

* identify the causes;
* separate static and dynamic factors;
* generate and classify candidate moves;
* explain tactical and strategic arguments;
* compare the played move with the alternatives;
* detect suboptimal move sequences;
* locate the conceptual origin of the error;
* reconstruct a thinking process appropriate to the player’s level;
* select positions that are useful for training.

The central functional sequence is:

```text
Detect
→ Evaluate
→ Compare
→ Diagnose
→ Explain
→ Train
```
