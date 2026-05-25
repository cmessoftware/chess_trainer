# ChessTrainer AI Coach – Player Style Classification & ML-Based Coaching

**Last Updated:** March 18, 2026

## Objective

Extend the AI coaching system to incorporate **player style classification** using ML model predictions.

Instead of generic coaching advice, the system will:
- Classify player style using ML cluster models (XGBoost/RandomForest/Neural Networks)
- Generate personalized feedback based on detected playing style
- Cross-reference ML predictions with Stockfish analysis for validated insights

This document defines how to integrate ML-based style classification into the existing LLM coaching pipeline.

---

## System Context

**Technology Stack:**
- Backend: Python (FastAPI)
- LLM: Ollama (llama3.1:8b)
- ML Models: XGBoost, RandomForest, Neural Networks
- Engine: Stockfish
- Database: PostgreSQL

**Available Inputs:**
- `pgn`: Standard game notation
- `stockfish_metadata`: 
  - Move-by-move evaluation (centipawns)
  - Best move vs actual move
  - Average centipawn loss (ACPL)
  - Clock times
- `ml_features`: 
  - Extracted game features
  - Model predictions with confidence scores
  - **Player style clusters** (e.g., "aggressive", "speculator", "solid", "positional")

**Goal:** Use Ollama to orchestrate these data sources and generate a **narrative pedagogical report** that humans can understand, avoiding redundant tactical calculations already performed by Stockfish.

---

## Implementation Strategy

### Phase 1: ML Style Classification (PLANNED)

**Objective:** Train ML models to classify players into style clusters based on game features.

**Player Style Taxonomy:**
1. **Aggressive** - High risk, tactical play, frequent attacks
2. **Positional** - Strategic, long-term planning, solid structure
3. **Solid** - Defensive, low error rate, patient play
4. **Tactical** - Combination-focused, sharp positions
5. **Speculator** - High variance, risky moves, unbalanced positions

**Data Source:**
- Historical games with extracted features
- Stockfish evaluations
- Player ELO ratings

**Model Output:**
```json
{
  "style_cluster": "aggressive",
  "confidence": 0.87,
  "style_scores": {
    "aggressive": 0.87,
    "tactical": 0.62,
    "positional": 0.31,
    "solid": 0.18,
    "speculator": 0.45
  }
}
```

---

### Phase 2: LLM Integration with Style Context

**Endpoint:** `/api/analysis/pedagogical-report` (EXISTING)

**Service:** `LLMAnalysisService.generate_pedagogical_report()` (IMPLEMENTED)

**Enhancement Required:** Inject ML style classification into the prompt context.

---

## Prompt Engineering Strategy

### Current Architecture (Implemented)

The system uses a **double-pass architecture**:

1. **Pass 1 - Structured Analysis (JSON)**
   - Input: Game data, Stockfish metadata, SHAP values
   - Output: Validated JSON with structured insights
   - Purpose: Verifiable, hallucination-free analysis

2. **Pass 2 - Narrative Report**
   - Input: Structured JSON + style classification
   - Output: Natural language coaching report
   - Purpose: Human-readable pedagogical feedback

### Enhanced Prompt Template with Style Classification

**System Role:**
```
You are an elite chess coach and sports psychologist.

Your function is NOT to calculate moves (Stockfish does that), but to:
- Interpret statistical data and convert it into pedagogical advice
- Adapt feedback to the player's playing style and skill level
- Provide actionable training recommendations

You analyze:
1. Stockfish evaluations (objective tactical assessment)
2. ML model predictions (pattern recognition)
3. Player style classification (behavioral tendencies)
```

**Enhanced User Prompt:**
```
Game Analysis Context:

STOCKFISH DATA:
- Average centipawn loss: {acpl}
- Blunders: {blunders}
- Mistakes: {mistakes}
- Critical moments: {critical_moves}

ML MODEL PREDICTIONS:
- Player style: {style_cluster} (confidence: {confidence}%)
- Style breakdown:
  * Aggressive: {aggressive_score}%
  * Tactical: {tactical_score}%
  * Positional: {positional_score}%
  * Solid: {solid_score}%

GAME METADATA:
- Opening: {opening_name}
- Phase breakdown: {phase_stats}
- Clock usage: {time_analysis}

TASK:
Based on the player's "{style_cluster}" playing style, explain:

1. Why did performance drop at move {critical_move}?
   - Was it time pressure (check clock data)?
   - Was it a tactical oversight (check Stockfish)?
   - Was it a style-driven impulse (check ML cluster)?

2. What recurring patterns match this player's style?
   - Strengths to leverage
   - Weaknesses to address
   - Style-appropriate training exercises

OUTPUT FORMAT (strict JSON):
{
  "style_analysis": "Interpretation of player style in this game",
  "coaching_summary": "Personalized coaching based on style",
  "strengths": ["List of style-aligned strengths"],
  "weaknesses": ["List of style-driven weaknesses"],
  "panic_detection": "Was there evidence of time pressure or panic?",
  "training_recommendations": ["Style-specific exercises"]
}
```

---

## Implementation Requirements

### 1. ML Model Integration

**File:** `src/ai_coach/style_classifier.py` (TO CREATE)

```python
class PlayerStyleClassifier:
    """
    Classifies player style using trained ML models.
    
    Uses feature data to predict playing style cluster.
    """
    
    def __init__(self, model_path: str):
        """Load trained style classification model."""
        pass
    
    def classify_style(self, features: Dict) -> Dict:
        """
        Predict player style from game features.
        
        Returns:
            {
                "style_cluster": str,
                "confidence": float,
                "style_scores": Dict[str, float]
            }
        """
        pass
```

### 2. Enhanced LLM Service

**File:** `src/api/services/llm_analysis_service.py` (UPDATE EXISTING)

**Enhancement:**
```python
async def generate_pedagogical_report(
    self,
    db: Session,
    analysis_id: int,
    player_elo: Optional[int] = None,
    include_style_classification: bool = True  # NEW PARAMETER
) -> Dict:
    """
    Generate pedagogical report with optional style classification.
    
    If include_style_classification=True:
        1. Extract game features
        2. Classify player style
        3. Inject style context into prompt
        4. Generate style-aware coaching report
    """
    pass
```

### 3. Output Validation

**File:** `src/api/services/json_validator.py` (UPDATE EXISTING)

**Add new schema:**
```python
STYLE_REPORT_SCHEMA = {
    "type": "object",
    "required": [
        "style_analysis",
        "coaching_summary", 
        "strengths",
        "weaknesses",
        "training_recommendations"
    ],
    "properties": {
        "style_analysis": {"type": "string"},
        "coaching_summary": {"type": "string"},
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "panic_detection": {"type": "string"},
        "training_recommendations": {"type": "array", "items": {"type": "string"}}
    }
}
```

### 4. Error Handling

**Challenges:**
- LLM may produce invalid JSON format
- Style classification model may have low confidence
- Missing feature data for classification

**Mitigation:**
```python
try:
    style_data = style_classifier.classify_style(features)
except Exception as e:
    logger.warning(f"Style classification failed: {e}")
    style_data = {"style_cluster": "unknown", "confidence": 0.0}
    
try:
    llm_response = await self.client.chat.completions.create(...)
    validated_output = validate_json(llm_response.content, STYLE_REPORT_SCHEMA)
except JSONValidationError:
    # Fallback to generic report
    return generate_fallback_report()
```

---

## Integration with Existing Architecture

### Current Pipeline (Implemented)

```
PGN Upload
→ Stockfish Analysis
→ Feature Extraction  
→ ML Error Prediction
→ SHAP Analysis
→ Feature Summarizer
→ RAG Retrieval
→ LLM Report Generation
→ UI Rendering
```

### Enhanced Pipeline with Style Classification

```
PGN Upload
→ Stockfish Analysis
→ Feature Extraction
→ ML Error Prediction
→ **ML Style Classification** ← NEW
→ SHAP Analysis
→ Feature Summarizer (with style context) ← ENHANCED
→ RAG Retrieval
→ LLM Report Generation (style-aware prompts) ← ENHANCED
→ UI Rendering (display style badge) ← ENHANCED
```

---

## Example Output

### Without Style Classification (Current)

```json
{
  "strengths": [
    "Good opening preparation",
    "Active piece play in middlegame"
  ],
  "weaknesses": [
    "Missed tactical opportunity at move 17",
    "Weak king safety in endgame"
  ],
  "recommendations": [
    "Study tactical patterns",
    "Practice endgame technique"
  ]
}
```

### With Style Classification (Enhanced)

```json
{
  "style_analysis": "This player exhibits an aggressive tactical style (87% confidence). The early kingside attack is characteristic of this approach, but the style-driven impulse led to premature commitments without adequate preparation.",
  
  "coaching_summary": "Your aggressive style created tactical pressure early, which is a strength. However, the impulse to attack before completing development (move 12-14) is a recurring pattern in aggressive players. Channel this energy into prepared attacks.",
  
  "strengths": [
    "Excellent tactical vision (fork on move 23)",
    "Aggressive initiative created psychological pressure",
    "Strong attacking instincts in open positions"
  ],
  
  "weaknesses": [
    "Premature attack before development complete (typical of aggressive style)",
    "Overextension in move 17 (style-driven impulse vs. positional calculation)",
    "Time pressure from complex positions (aggressive players often enter time trouble)"
  ],
  
  "panic_detection": "Move 24 took 8 seconds in a critical position with 2 minutes remaining. This suggests time pressure, not a fundamental misunderstanding. The aggressive style leads to complex positions that consume clock time.",
  
  "training_recommendations": [
    "Practice speed chess to improve time management in complex positions",
    "Study games by Tal and Kasparov (aggressive style masters)",
    "Drill: 'When to attack' - develop checklist before launching attacks",
    "Tactical exercises: attacking with incomplete development (your weakness)"
  ]
}
```

---

## Data Storage

### Database Schema Enhancement

**Table:** `analysis_results` (UPDATE EXISTING)

Add columns:
```sql
ALTER TABLE analysis_results
ADD COLUMN style_cluster VARCHAR(20),
ADD COLUMN style_confidence FLOAT,
ADD COLUMN style_scores JSONB;
```

**Example row:**
```json
{
  "analysis_id": 12345,
  "game_id": "abc123",
  "style_cluster": "aggressive",
  "style_confidence": 0.87,
  "style_scores": {
    "aggressive": 0.87,
    "tactical": 0.62,
    "positional": 0.31,
    "solid": 0.18,
    "speculator": 0.45
  }
}
```

---

## Testing Strategy

### Unit Tests

**File:** `tests/test_style_classifier.py` (TO CREATE)

```python
def test_style_classification_aggressive():
    """Test aggressive player classification."""
    features = load_test_features("aggressive_game.json")
    classifier = PlayerStyleClassifier(model_path="models/style_classifier.pkl")
    
    result = classifier.classify_style(features)
    
    assert result["style_cluster"] == "aggressive"
    assert result["confidence"] > 0.7

def test_style_classification_low_confidence():
    """Test handling of ambiguous style."""
    features = load_test_features("mixed_style_game.json")
    classifier = PlayerStyleClassifier(model_path="models/style_classifier.pkl")
    
    result = classifier.classify_style(features)
    
    if result["confidence"] < 0.5:
        assert "style_cluster" in result
        # Should still return best guess, but with low confidence
```

### Integration Tests

**File:** `tests/test_llm_style_integration.py` (TO CREATE)

```python
async def test_pedagogical_report_with_style():
    """Test LLM report generation with style classification."""
    service = LLMAnalysisService()
    
    report = await service.generate_pedagogical_report(
        db=test_db,
        analysis_id=12345,
        player_elo=1800,
        include_style_classification=True
    )
    
    assert "style_analysis" in report
    assert "training_recommendations" in report
    assert len(report["training_recommendations"]) > 0
```

---

## UI Integration

### Display Style Badge

**Frontend Component:** `GameAnalysisView.tsx` (UPDATE EXISTING)

```tsx
interface StyleBadge {
  cluster: string;
  confidence: number;
}

function PlayerStyleBadge({ cluster, confidence }: StyleBadge) {
  const styleColors = {
    aggressive: 'red',
    tactical: 'orange',
    positional: 'blue',
    solid: 'green',
    speculator: 'purple'
  };
  
  return (
    <div className={`badge badge-${styleColors[cluster]}`}>
      Playing Style: {cluster} ({Math.round(confidence * 100)}%)
    </div>
  );
}
```

---

## Roadmap Integration

### Dependencies

**Requires:**
- ✅ Stockfish integration (COMPLETED)
- ✅ Feature extraction pipeline (COMPLETED)
- ✅ ML models (XGBoost/RF/NN) (COMPLETED)
- ✅ LLM service (COMPLETED)
- ✅ RAG system (COMPLETED)

**To Implement:**
- ⬜ Player style classification model training
- ⬜ Style classifier service integration
- ⬜ Enhanced prompts with style context
- ⬜ Database schema updates
- ⬜ UI style badge rendering

### Implementation Phases

**Phase 1 - Model Training (2 weeks)**
- Collect labeled training data
- Train style classification model
- Validate accuracy on test set

**Phase 2 - Service Integration (1 week)**
- Implement `PlayerStyleClassifier`
- Update `LLMAnalysisService`
- Add database migrations

**Phase 3 - Prompt Enhancement (1 week)**
- Update prompt templates
- Test with various style profiles
- Validate output quality

**Phase 4 - UI Integration (1 week)**
- Add style badge component
- Update report display
- End-to-end testing

---

## References

**Related Documents:**
- [0-ai_chess_coach_roadmap.md](0-ai_chess_coach_roadmap.md) - Overall system roadmap
- [2-ai_chess_coach_module_spec.md](2-ai_chess_coach_module_spec.md) - Module architecture
- [4-ai_chess_coach_structured_output.md](4-ai_chess_coach_structured_output.md) - Output schemas
- [6-ai_chess_coach_patterm_analysis.md](6-ai_chess_coach_patterm_analysis.md) - Multi-game pattern analysis

**Implemented Code:**
- `src/api/services/llm_analysis_service.py` - LLM coaching service
- `src/ai_coach/feature_summarizer.py` - Feature to text conversion
- `src/ai_coach/rag/chess_rag.py` - RAG knowledge retrieval

---

## Success Criteria

✅ **Technical:**
- Style classification accuracy > 75% on test set
- LLM output validation passes 95% of time
- Report generation < 10 seconds end-to-end

✅ **User Experience:**
- Coaching advice is personalized and actionable
- Style classification feels accurate to users
- Recommendations align with player's natural tendencies

✅ **Educational Value:**
- Users can identify their playing style
- Training recommendations match style profile
- Progress tracking shows style evolution over time

---

**Status:** SPECIFICATION COMPLETE - Implementation Pending

**Next Steps:**
1. Review and approve specification
2. Create implementation issue/ticket
3. Begin Phase 1 (Model Training)
4. Update roadmap with timeline
