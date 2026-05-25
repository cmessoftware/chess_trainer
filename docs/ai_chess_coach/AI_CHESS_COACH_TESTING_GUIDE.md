# AI Chess Coach - Testing Guide

**Last Updated:** March 23, 2026  
**System Status:** Backend Operational (~50% Complete)

## 📋 Overview

This guide provides step-by-step instructions for testing the AI Chess Coach system, including:

- LLM-based pedagogical report generation
- ELO-adaptive coaching feedback
- Anti-hallucination validation
- Competitive context analysis
- Batch report processing

---

## 🎯 System Capabilities

The AI Chess Coach can:

✅ Generate personalized coaching reports based on game analysis  
✅ Adapt language and depth to player ELO (4 levels)  
✅ Detect critical moments (material losses, evaluative swings)  
✅ Provide result-aware feedback (win/loss/draw)  
✅ Prevent hallucinations (no invented material losses or positions)  
✅ Identify phase-specific errors (opening/middlegame/endgame)  
✅ Compare player performance vs opponent  

---

## 🔧 Prerequisites

### 1. Environment Setup

```powershell
# CRITICAL: Always use conda environment
conda activate chess_trainer

# Verify Python version
python --version  # Should be 3.10+
```

### 2. Database Running

```powershell
# Start PostgreSQL
docker-compose up -d postgres

# Verify connection
python -c "from db.session import get_db_context; print('✅ DB Connected')"
```

### 3. Analyzed Games Available

```powershell
# Check for games with analysis
python list_analyzed_games.py --limit 10
```

**What to look for:**
- Analysis completeness >80%
- Both WHITE and BLACK moves analyzed
- Recent games with SHAP values

**If no games available:**
```powershell
# Generate analysis for imported games
python src/scripts/generate_features_with_tactics.py --source stockfish
```

---

## 📍 Step 1: Find a Game to Test

### List Available Games

```powershell
# All analyzed games
python list_analyzed_games.py --limit 20

# Filter by source
python list_analyzed_games.py --source stockfish --limit 20  # Robot games
python list_analyzed_games.py --source personal --limit 20   # Your games
python list_analyzed_games.py --source elite --limit 20      # Master games

# Filter by player
python list_analyzed_games.py --player "PlayerName" --limit 10

# Combine filters
python list_analyzed_games.py --source stockfish --limit 20
```

### Example Output

```
1. Opening: Sicilian Defense
   Players: Base-b4c239b (W) vs New-9f312c8 (B)
   Source: stockfish
   Analysis: 165/182 moves (91% complete)  ← Look for >80%
   Colors: WHITE=91 moves, BLACK=91 moves   ← Both colors analyzed
   Game ID: b73806ebf5c0d72a1d0a74ecb6b8a28a6504e2974b1c7907e72af355b9e9ef79
```

**Copy the full Game ID from a game with:**
- ✅ Analysis >80% complete
- ✅ Both WHITE and BLACK present
- ✅ Source: stockfish (recommended for testing - consistent quality)

---

## 📍 Step 2: Get Analysis ID

The API requires `analysis_id`, not `game_id`. Convert:

```powershell
# Replace YOUR_GAME_ID with the actual game ID
python -c "
from db.session import get_db_context
from db.models.analysis_results import AnalysisResult

game_id = 'YOUR_GAME_ID_HERE'

with get_db_context() as db:
    analysis = db.query(AnalysisResult).filter(
        AnalysisResult.game_id == game_id
    ).first()
    
    if analysis:
        print(f'✅ Analysis Found!')
        print(f'Analysis ID: {analysis.id}')
        print(f'Game ID: {analysis.game_id}')
        print(f'Total moves: {analysis.total_moves}')
        print(f'Blunders: {analysis.blunder_count}')
        print(f'Mistakes: {analysis.mistake_count}')
        print(f'Inaccuracies: {analysis.inaccuracy_count}')
        print(f'Good moves: {analysis.good_move_count}')
        print(f'ACPL: {analysis.average_centipawn_loss}')
    else:
        print('❌ No analysis found for this game')
        print('Run: python src/scripts/generate_features_with_tactics.py')
"
```

**Copy the `Analysis ID`** (e.g., `123`)

### Quick Script to List Analysis IDs

```powershell
# List first 10 analysis IDs with game info
python -c "
from db.session import get_db_context
from db.models.analysis_results import AnalysisResult

with get_db_context() as db:
    analyses = db.query(AnalysisResult).limit(10).all()
    
    print('Available Analysis IDs:\n')
    for a in analyses:
        print(f'ID: {a.id:4d} | Moves: {a.total_moves:3d} | Errors: {a.blunder_count + a.mistake_count:2d} | Game: {a.game_id[:30]}...')
"
```

---

## 📍 Step 3: Start Backend API

### Option A: Using VS Code Task

1. Open Command Palette (`Ctrl+Shift+P`)
2. Run Task: `🚀 Start Chess API`
3. Wait for: `Uvicorn running on http://localhost:8000`

### Option B: Manual Start

```powershell
# Navigate to API directory
cd src/api

# Start with hot-reload
python -m uvicorn main:app --reload --port 8000
```

### Verify API is Running

```powershell
# Open in browser
start http://localhost:8000/docs

# Or test with curl
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-03-23T..."
}
```

---

## 📍 Step 4: Generate LLM Report

### Method 1: Using Swagger UI (Recommended for First Test)

1. Open `http://localhost:8000/docs`
2. Scroll to: **POST /api/analysis/generate-llm-report**
3. Click **"Try it out"**
4. Enter request body:
   ```json
   {
     "analysis_id": 123,
     "player_elo": 1800
   }
   ```
5. Click **"Execute"**
6. Review response below

### Method 2: Using curl (PowerShell)

```powershell
# With player ELO (recommended)
curl -X POST "http://localhost:8000/api/analysis/generate-llm-report" `
  -H "Content-Type: application/json" `
  -d '{
    "analysis_id": 123,
    "player_elo": 1800
  }'

# Without player ELO (uses intelligent default)
curl -X POST "http://localhost:8000/api/analysis/generate-llm-report" `
  -H "Content-Type: application/json" `
  -d '{
    "analysis_id": 123
  }'
```

### Method 3: Using Python

```python
import requests
import json

response = requests.post(
    "http://localhost:8000/api/analysis/generate-llm-report",
    headers={"Content-Type": "application/json"},
    json={
        "analysis_id": 123,
        "player_elo": 1800
    }
)

result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
```

---

## 📍 Step 5: Interpret Results

### Successful Response Structure

```json
{
  "success": true,
  "report": {
    "diagnostic": "En la jugada 17, durante el medio juego, perdiste una pieza menor. Este fue el momento más crítico de la partida...",
    "concrete_actions": [
      "En situaciones como la de la jugada 17, antes de mover verifica que todas tus piezas estén protegidas",
      "Antes de lanzar un ataque, completa el desarrollo de tus piezas",
      "Practica ejercicios de visualización para detectar piezas desprotegidas"
    ],
    "detected_strength": "A pesar del error material, lograste crear contraataque en el flanco de rey, lo que demuestra resiliencia táctica",
    "competitive_context": {
      "result": "loss",
      "player_color": "white",
      "player_error_ratio": 0.18,
      "opponent_error_ratio": 0.12,
      "critical_move": 17,
      "decisive_phase": "middlegame",
      "decisive_swing": 3.2,
      "material_events": [
        {
          "move": 33,
          "chess_notation_move": 17,
          "type": "piece_captured",
          "value_lost": 3.0,
          "phase": "middlegame"
        }
      ]
    },
    "metadata": {
      "player_elo": 1800,
      "elo_bucket": "intermediate",
      "version": "v6",
      "timestamp": "2026-03-23T10:30:45"
    }
  },
  "analysis_id": 123,
  "game_id": "b73806ebf5c0d72a1d0a74ecb6b8a28a...",
  "processing_time_seconds": 8.5
}
```

### Key Components

**1. Diagnostic (📊 ¿Qué pasó?)**
- Natural language explanation of the game
- Identifies critical moment (move number + phase)
- Explains impact on game outcome
- Tone: empathetic and educational

**2. Concrete Actions (🎯 ¿Qué mejorar?)**
- 2-6 specific recommendations (varies by ELO)
- Actionable advice, not generic
- References specific moves
- Practical training suggestions

**3. Detected Strength (✅ ¿Qué hiciste bien?)**
- Positive reinforcement
- Based on actual game data
- Motivational tone
- Even in losses, finds learning opportunities

**4. Competitive Context (🔍 Contexto técnico)**
- Result: win/loss/draw
- Player color
- Error ratios (player vs opponent)
- Critical move identification
- Material events (verified, not hallucinated)
- Evaluative swings (>50 centipawns)

**5. Metadata**
- ELO bucket (novice/intermediate/advanced/expert)
- System version (v6 = latest)
- Processing time

---

## 📍 Step 6: Test Different ELO Levels

The system adapts coaching to player skill level:

### ELO Buckets

| ELO Range | Level                 | Language              | Recommendations | Focus                     |
| --------- | --------------------- | --------------------- | --------------- | ------------------------- |
| <1600     | Novice/Intermediate   | Simple, analogies     | 3 max           | Material, basic tactics   |
| 1600-2000 | Intermediate/Advanced | Positional concepts   | 5 max           | Development, coordination |
| 2000-2100 | Advanced              | Technical terminology | 6 max           | Pawn structure, plans     |
| >2100     | Expert                | Deep analysis         | 6 max           | Optimization, precision   |

### Test Each Level

```powershell
# Novice (simple language, 3 recommendations, material focus)
curl -X POST "http://localhost:8000/api/analysis/generate-llm-report" `
  -H "Content-Type: application/json" `
  -d '{"analysis_id": 123, "player_elo": 1200}'

# Intermediate (positional concepts, 5 recommendations)
curl -X POST "http://localhost:8000/api/analysis/generate-llm-report" `
  -H "Content-Type: application/json" `
  -d '{"analysis_id": 123, "player_elo": 1800}'

# Advanced (technical analysis, 6 recommendations)
curl -X POST "http://localhost:8000/api/analysis/generate-llm-report" `
  -H "Content-Type: application/json" `
  -d '{"analysis_id": 123, "player_elo": 2200}'

# Expert (deep precision analysis)
curl -X POST "http://localhost:8000/api/analysis/generate-llm-report" `
  -H "Content-Type: application/json" `
  -d '{"analysis_id": 123, "player_elo": 2500}'
```

### Compare Outputs

**Novice (1200):**
> "En la jugada 17, perdiste una pieza. Antes de mover, siempre pregúntate: ¿está mi pieza protegida?"

**Expert (2500):**
> "La jugada 17.Nd5 comprometió la coordinación de tus piezas menores sin compensación posicional suficiente, resultando en un desequilibrio material de 3 puntos con estructura de peones debilitada en el flanco de dama."

---

## 📍 Step 7: Test Batch Processing

Generate reports for multiple games at once:

```powershell
curl -X POST "http://localhost:8000/api/analysis/generate-batch-llm-reports" `
  -H "Content-Type: application/json" `
  -d '{
    "analysis_ids": [123, 124, 125],
    "player_elo": 1800
  }'
```

**Response:**
```json
{
  "success": true,
  "reports": [
    {"analysis_id": 123, "report": {...}},
    {"analysis_id": 124, "report": {...}},
    {"analysis_id": 125, "report": {...}}
  ],
  "total_processed": 3,
  "total_time_seconds": 25.3
}
```

---

## ✅ Validation Checklist

### Quality Indicators

**✅ No Hallucinations:**
- [ ] Does NOT mention material loss if `material_events` is empty
- [ ] Does NOT mention "changes of 0 centipawns" or meaningless swings
- [ ] Does NOT invent moves outside the actual game
- [ ] All move numbers cited exist in the game

**✅ Specificity:**
- [ ] Cites specific move numbers (e.g., "jugada 17")
- [ ] Mentions game phase (opening/middlegame/endgame)
- [ ] Explains WHAT happened, not generic advice
- [ ] References actual material events or swings from FACTS_PACK

**✅ ELO Adaptation:**
- [ ] Language complexity matches ELO level
- [ ] Number of recommendations correct (3/5/6 based on level)
- [ ] Focus areas appropriate (material for novice, structure for expert)
- [ ] Technical depth matches skill level

**✅ Result-Aware:**
- [ ] Win: mentions strengths that compensated errors
- [ ] Loss: identifies decisive factor
- [ ] Draw: points out missed opportunities
- [ ] Tone appropriate to outcome (motivational for loss, reinforcing for win)

**✅ Technical Accuracy:**
- [ ] `decisive_move` matches engine_analysis
- [ ] `material_events` are real (not hallucinated)
- [ ] `top_swings` have meaningful delta_cp (≥50)
- [ ] Phase distribution matches error_distribution

---

## 🐛 Troubleshooting

### Error: "OPENAI_API_KEY not found"

**Cause:** Environment variable missing

**Solution:**
```powershell
# Check .env file
cat .env | Select-String OPENAI_API_KEY

# If missing, add it
echo "OPENAI_API_KEY=your_api_key_here" >> .env

# Restart API
```

### Error: "Analysis not found"

**Cause:** Invalid `analysis_id` or no analysis for that game

**Solution:**
```powershell
# Verify analysis exists
python -c "
from db.session import get_db_context
from db.models.analysis_results import AnalysisResult

with get_db_context() as db:
    count = db.query(AnalysisResult).count()
    print(f'Total analyses: {count}')
"

# If count is 0, run analysis
python src/scripts/generate_features_with_tactics.py
```

### Error: "No moves with SHAP values"

**Cause:** Missing ML analysis (SHAP values not calculated)

**Solution:**
```powershell
# Regenerate SHAP analysis
python src/scripts/generate_features_with_tactics.py --source stockfish
```

### Report Quality Issues

**Generic feedback (e.g., "mejorar coordinación")**

**Cause:** LLM not following FACTS_PACK constraints

**Debug:**
1. Check API logs for FACTS_PACK content
2. Verify `material_events` and `top_swings` have data
3. Look for "V5 - FILTRADO DE SWINGS" in logs
4. Ensure OpenAI API key is valid (not rate-limited)

**Hallucinated material losses**

**Cause:** LLM ignoring anti-hallucination rules

**Debug:**
1. Check if `material_loss_claimed = false` in structured JSON
2. Verify FACTS_PACK has empty `material_events`
3. Update prompt with stricter rules (edit `llm_analysis_service.py`)

---

## 📊 Automated Testing

### Quick Test Script

```powershell
# Test basic pipeline
python src/scripts/test_ai_coach_pipeline.py
```

**This verifies:**
- ✅ Database connection
- ✅ RAG system operational
- ✅ Features available
- ✅ ML models loaded

### Unit Tests (Future)

```powershell
# When implemented
pytest tests/ai_coach/test_llm_service.py -v
pytest tests/ai_coach/test_validation.py -v
```

---

## 🔍 Advanced Testing

### View Internal Processing

The API logs show internal processing:

```
🔧 V4 - JSON ESTRUCTURADO (100% DETERMINÍSTICO):
   decisive_move_used: 17
   error_type: single (swing: 320 cp)
   material_loss_claimed: true (1 events)
   phase_problems: opening=false, middle=true, end=false
   confidence: 0.90

🧹 V5 - FILTRADO DE SWINGS:
   Swings crudos: 8
   Swings filtrados (|delta| >= 50): 3

✅ FACTS_PACK construido:
   Evento decisivo: {'chess_move': 17, 'type': 'piece_captured', ...}
   Material events: 1
   Top swings relevantes: 3
```

### Test Anti-Hallucination

**Test Case: No Material Loss**

1. Find game with NO material events
2. Generate report
3. Verify report does NOT mention "perdiste una pieza"

**Example validation:**
```python
# After getting report
report_text = result["report"]["diagnostic"]

# Should NOT contain
forbidden_phrases = [
    "perdiste una pieza",
    "perdiste el caballo",
    "perdiste la torre",
    "pérdida material"
]

for phrase in forbidden_phrases:
    if phrase in report_text.lower():
        print(f"❌ HALLUCINATION DETECTED: '{phrase}'")
    else:
        print(f"✅ No hallucination: '{phrase}'")
```

---

## 📈 Performance Metrics

### Expected Processing Times

| Report Type             | Time Range | Notes                      |
| ----------------------- | ---------- | -------------------------- |
| Single report (GPT-4)   | 5-15s      | Depends on game complexity |
| Single report (GPT-3.5) | 3-8s       | Faster but lower quality   |
| Batch (3 games)         | 15-45s     | Sequential processing      |

### Monitoring

```powershell
# Check processing time in response
{
  "processing_time_seconds": 8.5  # Should be <15s
}
```

If consistently >20s:
- Check OpenAI API rate limits
- Consider using GPT-3.5-turbo for faster responses
- Optimize prompt length (currently ~1500 tokens)

---

## 🎓 Understanding the System

### Architecture Flow

```
Game → Analysis → SHAP → Competitive Context
                          ↓
                    FACTS_PACK (filtered data)
                          ↓
                    Structured JSON (deterministic)
                          ↓
                    Validation
                          ↓
                    Narrative Prompt (pedagogical)
                          ↓
                    LLM Generation
                          ↓
                    Pedagogical Report
```

### Why Double-Pass Architecture?

**Pass 1 (Structured JSON):**
- Deterministic fact extraction
- No room for hallucination
- Verifiable data points

**Pass 2 (Narrative):**
- LLM explains facts (doesn't invent them)
- Pedagogical tone
- ELO-adaptive language

### Anti-Hallucination Strategy

1. **FACTS_PACK:** Only verified data from engine analysis
2. **Filtering:** Remove meaningless swings (delta < 50 cp)
3. **Strict Rules:** Explicit prohibitions in prompt
4. **Validation:** JSON schema enforcement
5. **Calibration:** Material loss only if verified >2 pawn advantage

---

## 📚 References

**Documentation:**
- [AI Coach Roadmap](0-ai_chess_coach_roadmap.md) - Overall system status
- [Module Specification](2-ai_chess_coach_module_spec.md) - Architecture
- [Structured Output](4-ai_chess_coach_structured_output.md) - JSON schemas
- [Style Classification](7-ai_chess_coach_style_classification.md) - Future enhancement

**Implementation:**
- `src/api/services/llm_analysis_service.py` - Main service (2,200+ lines)
- `src/api/routers/analysis.py` - API endpoints
- `src/api/services/json_validator.py` - Output validation
- `src/api/services/prompt_validator.py` - Prompt validation

**Scripts:**
- `list_analyzed_games.py` - Find games for testing
- `src/scripts/test_ai_coach_pipeline.py` - Automated testing
- `src/scripts/generate_features_with_tactics.py` - Generate analysis

---

## 🚀 Quick Start Checklist

- [ ] **1.** Activate conda environment: `conda activate chess_trainer`
- [ ] **2.** Start database: `docker-compose up -d postgres`
- [ ] **3.** Find game: `python list_analyzed_games.py --source stockfish --limit 10`
- [ ] **4.** Get Analysis ID: Use Python snippet from Step 2
- [ ] **5.** Start API: `cd src/api && python -m uvicorn main:app --reload --port 8000`
- [ ] **6.** Open Swagger: `http://localhost:8000/docs`
- [ ] **7.** Test endpoint: POST `/api/analysis/generate-llm-report`
- [ ] **8.** Validate output: Check for specificity, no hallucinations, ELO adaptation
- [ ] **9.** Test different ELOs: 1200, 1800, 2200
- [ ] **10.** Verify quality: Use validation checklist

---

## 💡 Tips for Best Results

✅ **Use Stockfish games for testing** - Consistent quality, both colors analyzed  
✅ **Test with different ELOs** - Verify adaptation works correctly  
✅ **Check logs** - Internal FACTS_PACK shows what data LLM receives  
✅ **Validate anti-hallucination** - Ensure no invented material losses  
✅ **Compare win/loss/draw** - Verify result-aware feedback  

---

**Last Updated:** March 23, 2026  
**System Version:** v6 (Double-pass architecture with FACTS_PACK validation)  
**Status:** Backend operational, ready for testing and refinement
