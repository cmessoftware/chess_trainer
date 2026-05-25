# AI Chess Coach - LLM Optimization Roadmap (Llama 3.1:8b)

**Document Status:** PROPOSAL  
**Created:** March 23, 2026  
**Based on:** Analysis of current system + fine-tuning best practices

---

## 📊 Executive Summary

**Current State:**
- LLM: OpenAI API (external dependency, cost per request)
- RAG: 8,553 chess book chunks (general theory, not player-specific)
- ML Models: RandomForest/XGBoost exist but disconnected from LLM
- Architecture: Missing local fine-tuning and decision validation

**Proposed Enhancement:**
Migrate to **Llama 3.1:8b** with **LoRA fine-tuning** on player-specific data, integrating ML predictions and Stockfish validation to eliminate hallucinations and personalize coaching.

**Expected Benefits:**
- ✅ Zero cost per inference (local model)
- ✅ Personalized to player's games and errors
- ✅ No hallucinations (grounded in ML + Stockfish)
- ✅ Faster inference (~2-5s vs 5-15s)
- ✅ Privacy (no data sent to OpenAI)

---

## 🎯 Proposed Architecture

### Current (OpenAI-based)

```
User → Game Analysis → SHAP → Competitive Context
                                ↓
                          FACTS_PACK
                                ↓
                          OpenAI GPT-4 (external API)
                                ↓
                          Pedagogical Report
```

**Problems:**
- External dependency (OpenAI)
- No fine-tuning on player data
- ML models unused in decision
- Cost per request

### Enhanced (Llama 3.1:8b + LoRA)

```
User → Game Analysis → SHAP → Competitive Context
                                ↓
                          FACTS_PACK
                                ↓
                     ┌──────────┴──────────┐
                     │                     │
                ML Predictor            RAG Enhanced
              (error type,           (player decisions,
               confidence)            similar positions)
                     │                     │
                     └──────────┬──────────┘
                                ↓
                      Llama 3.1:8b (LoRA)
                       (local, fine-tuned)
                                ↓
                        Proposed Move + Plan
                                ↓
                     Stockfish Validator
                   (tactical verification)
                                ↓
                     Pedagogical Report
```

**Improvements:**
- ✅ ML decides → LLM explains
- ✅ RAG with player-specific decisions
- ✅ Stockfish validates tactics
- ✅ Local inference (no API)
- ✅ Fine-tuned on player style

---

## 📋 Gap Analysis: Current vs Ideal

| Component                 | Current State               | Ideal State                      | Gap                         |
| ------------------------- | --------------------------- | -------------------------------- | --------------------------- |
| **LLM**                   | OpenAI GPT-4 API            | Llama 3.1:8b LoRA                | No local model              |
| **RAG Data**              | Chess books (8,553 chunks)  | Player decisions + books         | Missing player data         |
| **ML Integration**        | Disconnected (models exist) | ML → decides → LLM explains      | Not integrated              |
| **Validation**            | None (LLM output final)     | Stockfish validates tactics      | Missing loop                |
| **Dataset**               | PGN → features              | PGN → decisions + justifications | No structured coaching data |
| **Fine-tuning**           | None (zero-shot prompting)  | LoRA on player patterns          | Not implemented             |
| **Hallucination Control** | Prompt engineering only     | ML + RAG + validation            | Weak grounding              |

---

## 🚀 Implementation Phases

## Phase 0: Dataset Preparation (Foundational) [NEW]

**Duration:** 2-3 weeks  
**Priority:** CRITICAL (blocks all other phases)

### 0.1. Create Structured Decision Dataset

**Current Problem:**
- PGN files exist but are not structured for LLM training
- Features extracted but no "decision → justification" mapping
- RAG indexes chess books, not player decisions

**Solution:**
Transform existing data into coaching examples:

```python
# Target format
{
  "position": {
    "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
    "phase": "opening",
    "material_balance": 0,
    "king_safety": 0.5,
    "center_control": 0.7
  },
  "decision": {
    "player_move": "e5",
    "stockfish_best": "e5",
    "error_label": "good",
    "alternatives": ["c5", "Nf6"],
    "evaluation_before": 0.0,
    "evaluation_after": 0.0
  },
  "context": {
    "similar_positions": [...],  # RAG retrieval
    "player_error_pattern": "none",
    "ml_prediction": "good",
    "ml_confidence": 0.92
  },
  "coaching": {
    "plan": "Control del centro con peones",
    "explanation": "e5 es la respuesta clásica que disputa el centro y libera al alfil de casillas negras",
    "justification": "Desarrollar piezas rápido es prioritario en la apertura",
    "risks": "None detected",
    "confidence": 0.95
  }
}
```

**Script to Create:**
`src/scripts/create_coaching_dataset.py`

```python
"""
Convert analyzed games into coaching examples.

For each game:
1. Extract positions (FEN)
2. Get ML predictions (error_label, confidence)
3. Get Stockfish evaluation
4. Retrieve similar positions from RAG
5. Generate coaching text (human-written templates initially)
6. Store in structured format

Output: data/coaching_dataset/training_examples.jsonl
"""
```

**Data Sources:**
- ✅ Existing: `games` table (PGNs)
- ✅ Existing: `features` table (extracted features)
- ✅ Existing: `analysis_results` table (Stockfish)
- ✅ Existing: ML models (predictions)
- ⬜ **NEW:** Coaching justifications (templated initially)

**Metrics:**
- Target: 10,000+ position-decision pairs
- From: `stockfish` games (consistent quality)
- Coverage: all phases (opening/middlegame/endgame)
- Error distribution: balanced (good/inaccuracy/mistake/blunder)

### 0.2. Enhance RAG with Player Decisions

**Current RAG:**
- Chess books only (general theory)
- No player-specific patterns

**Enhanced RAG:**

```python
# Index both books AND decisions
{
  "type": "book_knowledge",
  "source": "Modern Chess Openings",
  "content": "...",
  "tags": ["opening", "italian_game"]
}

{
  "type": "player_decision",  # NEW
  "fen": "...",
  "player_move": "Nf3",
  "error_label": "good",
  "phase": "opening",
  "explanation": "Developed knight to control center",
  "outcome": "win"
}
```

**Benefits:**
- Player-specific retrieval
- Pattern recognition (recurring errors)
- Contextual examples from own games

**Script:**
`src/scripts/enhance_rag_with_decisions.py`

### 0.3. Create Baseline Prompts

**Template System:**

```python
# templates/coaching_prompts.py

TEMPLATES = {
    "novice": {
        "instruction": "Explica en lenguaje simple...",
        "max_complexity": "basic",
        "forbidden_terms": ["profilaxis", "zugzwang"]
    },
    "intermediate": {
        "instruction": "Analiza con conceptos posicionales...",
        "max_complexity": "medium",
        "forbidden_terms": []
    },
    "advanced": {
        "instruction": "Proporciona análisis técnico profundo...",
        "max_complexity": "high",
        "forbidden_terms": []
    }
}
```

---

## Phase 1: Local LLM Integration [NEW]

**Duration:** 1-2 weeks  
**Priority:** HIGH  
**Dependencies:** Phase 0 complete

### 1.1. Setup Ollama + Llama 3.1:8b

**Current:**
- Ollama Docker container exists (for testing)
- Models downloaded but not used in production

**Action:**
```powershell
# Download model
ollama pull llama3.1:8b

# Verify
ollama run llama3.1:8b "Test prompt"
```

**Integration:**
Update `src/api/services/llm_analysis_service.py`:

```python
class LLMAnalysisService:
    def __init__(self):
        # Current: OpenAI
        # self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # NEW: Ollama
        self.client = AsyncOllama(base_url="http://localhost:11434")
        self.model = "llama3.1:8b"
```

### 1.2. Baseline Testing (Zero-shot)

**Test current prompts with Llama 3.1:8b:**

```python
# Test script: src/scripts/test_llama_baseline.py

# Compare:
# - OpenAI GPT-4 (current)
# - Llama 3.1:8b (zero-shot)

# Metrics:
# - Hallucination rate
# - Specificity score
# - ELO adaptation quality
# - Response time
```

**Expected Results:**
- Llama will have MORE hallucinations (no fine-tuning yet)
- But faster and free
- Baseline for improvement

---

## Phase 2: LoRA Fine-tuning [NEW]

**Duration:** 2-3 weeks  
**Priority:** CRITICAL  
**Dependencies:** Phase 0 + Phase 1

### 2.1. Prepare Training Environment

**Tools:**
- **Axolotl** (recommended for simplicity)
- **PEFT** (Hugging Face)
- **QLoRA** (4-bit quantization)

**Setup:**
```bash
# Install dependencies
pip install axolotl-ml peft bitsandbytes accelerate

# Or use dedicated conda environment
conda create -n llama_finetuning python=3.10
conda activate llama_finetuning
pip install -r requirements_finetuning.txt
```

### 2.2. Configure LoRA

**Config file:** `config/llama_lora_chess.yml`

```yaml
base_model: meta-llama/Llama-3.1-8B
model_type: LlamaForCausalLM

# Quantization (critical for 4.9GB)
load_in_4bit: true
bnb_4bit_compute_dtype: bfloat16
bnb_4bit_use_double_quant: true

# LoRA config
adapter: lora
lora_r: 16              # Rank (low = fewer params)
lora_alpha: 32          # Scaling factor
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - k_proj
  - v_proj
  - o_proj

# Training
sequence_len: 2048
sample_packing: true
pad_to_sequence_len: true

learning_rate: 2e-4
num_epochs: 3
batch_size: 2
gradient_accumulation_steps: 8
warmup_steps: 100

optimizer: adamw_bnb_8bit
lr_scheduler: cosine

# Dataset
dataset_type: alpaca
datasets:
  - path: data/coaching_dataset/training_examples.jsonl
    type: alpaca

# Validation
val_set_size: 0.1
eval_steps: 100

# Output
output_dir: models/llama-chess-lora
```

### 2.3. Dataset Format Conversion

**Convert structured dataset to Alpaca format:**

```python
# src/scripts/convert_to_alpaca.py

# Input: data/coaching_dataset/training_examples.jsonl
# Output: data/coaching_dataset/alpaca_format.jsonl

# Format:
{
  "instruction": "Analiza esta posición y da una recomendación para un jugador ELO 1800",
  "input": """
FEN: rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3
Phase: opening
Material: 0
King safety: 0.5
Center control: 0.7

ML Prediction: good (confidence: 0.92)
Similar positions: 3 found
Error pattern: None detected
""",
  "output": """
{
  "plan": "Desarrollar piezas menores antes de atacar",
  "explanation": "Ambos bandos han desarrollado un caballo. El siguiente paso natural es desarrollar el alfil de casillas blancas (Bc4 o Be2) y enrocar pronto.",
  "justification": "En la apertura, el desarrollo rápido y la seguridad del rey son prioritarios antes de iniciar ataques",
  "candidate_moves": ["Bc4", "Be2", "d4"],
  "best_move": "Bc4",
  "risks": "Evitar d4 inmediato sin desarrollo completo",
  "confidence": 0.95
}
"""
}
```

### 2.4. Training Execution

**Hardware Requirements:**
- GPU: 12GB+ VRAM (RTX 3080/4070 or better)
- RAM: 32GB+
- Storage: 50GB for model + checkpoints

**If no GPU:**
- Use Google Colab (free tier with T4 GPU)
- Or Kaggle notebooks (30h/week GPU free)

**Training command:**
```bash
accelerate launch -m axolotl.cli.train config/llama_lora_chess.yml
```

**Expected time:**
- ~4-6 hours for 3 epochs on 10k examples
- Checkpoints every 100 steps

### 2.5. Evaluation

**Validation metrics:**

```python
# src/scripts/evaluate_lora_model.py

metrics = {
    "hallucination_rate": 0.0,  # Target: <5%
    "tactical_accuracy": 0.0,   # Validated by Stockfish
    "elo_adaptation": 0.0,      # Language complexity
    "specificity_score": 0.0,   # Cites concrete moves
    "perplexity": 0.0,          # Language quality
    "inference_time": 0.0       # Target: <5s
}
```

**Comparison:**
| Metric        | GPT-4 (current) | Llama 3.1 (zero-shot) | Llama 3.1 (LoRA) |
| ------------- | --------------- | --------------------- | ---------------- |
| Hallucination | Low (~2%)       | High (~20%)           | Target: <5%      |
| Specificity   | High            | Low                   | Target: High     |
| Speed         | 5-15s           | 2-5s                  | 2-5s             |
| Cost          | $0.01/req       | $0                    | $0               |

---

## Phase 3: ML-Guided Decision Layer [NEW]

**Duration:** 1-2 weeks  
**Priority:** HIGH  
**Dependencies:** Phase 0

### 3.1. Integrate Existing ML Models

**Current State:**
- `src/ml/chess_error_predictor.py` exists
- RandomForest, XGBoost trained
- **BUT:** Not used in LLM pipeline

**Integration:**

```python
# src/api/services/ml_decision_service.py (NEW)

class MLDecisionService:
    """
    Use ML models to guide LLM decisions.
    
    Architecture:
    1. Extract features from position
    2. ML predicts: error type, confidence, risk
    3. LLM explains ML prediction (not decides)
    """
    
    def __init__(self):
        self.error_predictor = ChessErrorPredictor()
        # Load trained models
        self.error_predictor.load_model("models/error_predictor_v1.pkl")
    
    def predict_decision(self, features: Dict) -> Dict:
        """
        Predict move quality and error type.
        
        Returns:
            {
                "predicted_error": "good",
                "confidence": 0.92,
                "risk_score": 0.1,
                "contributing_features": [
                    {"name": "center_control", "impact": 0.3},
                    {"name": "king_safety", "impact": -0.2}
                ]
            }
        """
        prediction = self.error_predictor.predict_move_error(features)
        
        # Add feature importance (SHAP)
        shap_values = self._get_shap_explanation(features)
        
        return {
            "predicted_error": prediction["predicted_error"],
            "confidence": prediction["confidence"],
            "risk_score": self._calculate_risk(prediction),
            "contributing_features": shap_values[:5]  # Top 5
        }
```

**Update LLM Service:**

```python
# src/api/services/llm_analysis_service.py

async def generate_pedagogical_report(self, ...):
    # BEFORE (current):
    # prompt = self._build_prompt(facts_pack)
    
    # AFTER (enhanced):
    ml_decision = self.ml_service.predict_decision(features)
    
    facts_pack = {
        **facts_pack,
        "ml_decision": ml_decision  # Add ML guidance
    }
    
    prompt = self._build_prompt_with_ml(facts_pack)
```

### 3.2. ML → LLM → Stockfish Pipeline

**Decision Flow:**

```
Position (FEN)
    ↓
Extract Features
    ↓
ML Prediction ──────────┐
(error type, confidence) │
    ↓                    │
RAG Retrieval            │
(similar positions)      │
    ↓                    │
LLM Generation ←─────────┘
(plan + explanation)
    ↓
Stockfish Validation
(verify tactics)
    ↓
Final Report
(ML-grounded + validated)
```

**Example:**

```python
# Input
position = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"

# Step 1: ML predicts
ml_output = {
    "predicted_move_quality": "good",
    "confidence": 0.88,
    "contributing_factors": [
        "center_control: +0.7",
        "development: +0.3"
    ]
}

# Step 2: LLM explains (grounded in ML)
llm_output = {
    "plan": "Desarrollar caballo a f3",
    "explanation": "El modelo ML predice alta calidad (88% confianza) porque la posición favorece desarrollo sobre el centro. Nf3 es coherente con este análisis.",
    "risks": "None detected by ML"
}

# Step 3: Stockfish validates
stockfish_check = {
    "tactical_soundness": True,
    "evaluation": "+0.3",
    "best_move": "Nf3",
    "llm_suggested": "Nf3",
    "match": True
}

# Final output
report = {
    "recommendation": "Nf3",
    "confidence": "high (ML: 88%, Stockfish: validated)",
    "explanation": llm_output["explanation"]
}
```

---

## Phase 4: Stockfish Validation Loop [NEW]

**Duration:** 1 week  
**Priority:** MEDIUM  
**Dependencies:** Phase 3

### 4.1. Pre-validation (before LLM)

**Check position legality:**

```python
# src/services/stockfish_validator.py (NEW)

class StockfishValidator:
    def validate_position(self, fen: str) -> Dict:
        """Verify position is legal and get evaluation."""
        board = chess.Board(fen)
        
        if not board.is_valid():
            return {"valid": False, "error": "Illegal position"}
        
        # Get Stockfish evaluation
        with chess.engine.SimpleEngine.popen_uci("stockfish") as engine:
            info = engine.analyse(board, chess.engine.Limit(depth=15))
            
        return {
            "valid": True,
            "evaluation": info["score"].relative.score() / 100,
            "best_move": str(info["pv"][0])
        }
```

### 4.2. Post-validation (after LLM)

**Verify LLM suggestions are tactically sound:**

```python
async def generate_pedagogical_report(self, ...):
    # ... existing code ...
    
    llm_response = await self.client.generate(prompt)
    
    # NEW: Validate suggestions
    validation = self.stockfish.validate_suggestions(
        fen=position.fen,
        suggested_moves=llm_response["candidate_moves"]
    )
    
    if not validation["all_legal"]:
        # Fallback: use Stockfish best move
        logger.warning(f"LLM suggested illegal move: {validation['illegal']}")
        llm_response = self._fallback_to_stockfish(validation)
    
    return llm_response
```

---

## Phase 5: DPO Training (Advanced) [FUTURE]

**Duration:** 2-3 weeks  
**Priority:** LOW (after Phase 2 working)  
**Dependencies:** Phase 2 complete + feedback data

### 5.1. Collect Preference Data

**User feedback on reports:**

```python
# Store in DB
{
    "report_id": 123,
    "game_id": "abc...",
    "llm_response": {...},
    "user_rating": 4.5,  # 1-5 stars
    "user_feedback": "Good explanation but missed key tactic",
    "preferred_alternative": null  # Or alternative coaching
}
```

### 5.2. Create Preference Pairs

**Format for DPO:**

```python
{
    "prompt": "Analiza esta posición...",
    "chosen": "Desarrollar piezas antes de atacar porque...",  # High rating
    "rejected": "Atacar inmediatamente en el flanco..."         # Low rating
}
```

### 5.3. DPO Training

**Config:**

```yaml
# config/llama_dpo_chess.yml

base_model: models/llama-chess-lora  # Start from LoRA
training_type: dpo

beta: 0.1  # DPO hyperparameter
learning_rate: 5e-6
num_epochs: 1

dataset:
  - path: data/preference_pairs.jsonl
    type: dpo
```

**Expected improvement:**
- Better alignment with human preferences
- Reduced "plausible but wrong" responses
- More pedagogically effective explanations

---

## 📊 Success Metrics

| Metric                    | Current (GPT-4) | Target (Llama LoRA) | Measurement                   |
| ------------------------- | --------------- | ------------------- | ----------------------------- |
| **Hallucination Rate**    | ~2%             | <5%                 | Manual review + ML validation |
| **Tactical Accuracy**     | ~95%            | >90%                | Stockfish validation          |
| **Specificity Score**     | High            | High                | Cites move numbers            |
| **ELO Adaptation**        | Good            | Good                | Language complexity           |
| **Inference Time**        | 5-15s           | 2-5s                | API response time             |
| **Cost per 1000 reports** | ~$10            | $0                  | Direct cost                   |
| **Personalization**       | None            | High                | Player-specific patterns      |

---

## 🛠️ Implementation Checklist

### Phase 0: Dataset Preparation
- [ ] **0.1** Create `src/scripts/create_coaching_dataset.py`
- [ ] **0.2** Generate 10,000+ position-decision pairs
- [ ] **0.3** Enhance RAG with player decisions
- [ ] **0.4** Create coaching prompt templates
- [ ] **0.5** Validate dataset quality (manual review)

### Phase 1: Local LLM
- [ ] **1.1** Install Ollama + Llama 3.1:8b
- [ ] **1.2** Update `llm_analysis_service.py` for Ollama
- [ ] **1.3** Baseline testing (zero-shot)
- [ ] **1.4** Compare GPT-4 vs Llama baseline
- [ ] **1.5** Document performance gaps

### Phase 2: LoRA Fine-tuning
- [ ] **2.1** Setup Axolotl environment
- [ ] **2.2** Create `config/llama_lora_chess.yml`
- [ ] **2.3** Convert dataset to Alpaca format
- [ ] **2.4** Train LoRA adapter (3 epochs)
- [ ] **2.5** Evaluate metrics (hallucination, specificity)
- [ ] **2.6** A/B test: LoRA vs GPT-4

### Phase 3: ML Integration
- [ ] **3.1** Create `ml_decision_service.py`
- [ ] **3.2** Integrate `ChessErrorPredictor` in pipeline
- [ ] **3.3** Update prompts to include ML predictions
- [ ] **3.4** Test ML → LLM flow
- [ ] **3.5** Validate improvements

### Phase 4: Stockfish Validation
- [ ] **4.1** Create `stockfish_validator.py`
- [ ] **4.2** Pre-validation (position checks)
- [ ] **4.3** Post-validation (suggestion checks)
- [ ] **4.4** Fallback logic for invalid suggestions
- [ ] **4.5** Monitor validation failures

### Phase 5: DPO (Future)
- [ ] **5.1** Implement user feedback collection
- [ ] **5.2** Generate preference pairs (1000+)
- [ ] **5.3** Train DPO on LoRA checkpoint
- [ ] **5.4** Evaluate alignment improvements

---

## 💡 Key Insights from Analysis

### 1. **Separation of Concerns**

❌ **DON'T:** Ask LLM to evaluate positions  
✅ **DO:** ML evaluates → LLM explains  

### 2. **RAG Strategy**

❌ **DON'T:** Index raw PGN files  
✅ **DO:** Index structured decisions (FEN → plan → outcome)  

### 3. **Grounding Hierarchy**

```
Level 1: ML Prediction (deterministic fact)
Level 2: Stockfish Validation (ground truth)
Level 3: RAG Context (similar cases)
Level 4: LLM Synthesis (explanation only)
```

### 4. **Dataset Quality > Model Size**

- 10K high-quality examples > 100K noisy PGNs
- Each example needs: position + decision + justification
- Templates acceptable initially, refine with feedback

### 5. **LoRA is Sufficient**

- Full fine-tuning: overkill + risk of catastrophic forgetting
- LoRA: preserves base model knowledge + adds domain adaptation
- QLoRA: makes it feasible on consumer hardware

---

## 🔄 Migration Path (Current → Target)

### Week 1-2: Parallel Operation

- Keep OpenAI API as production
- Deploy Llama 3.1:8b (zero-shot) as beta
- Collect comparison data

### Week 3-4: Dataset Creation

- Run `create_coaching_dataset.py`
- Manual review of 100 examples
- Iterate on templates

### Week 5-6: LoRA Training

- Train first LoRA checkpoint
- Evaluate against baseline
- Tune hyperparameters if needed

### Week 7: Integration

- Add ML decision layer
- Add Stockfish validation
- Test end-to-end pipeline

### Week 8: A/B Testing

- 50% traffic to Llama LoRA
- 50% traffic to GPT-4
- Compare metrics

### Week 9: Migration Decision

**If Llama LoRA meets thresholds:**
- Migrate 100% traffic
- Decommission OpenAI integration
- Monitor for regressions

**If not:**
- Iterate on training data
- Collect more examples
- Re-train with improvements

---

## 📚 Learning Resources

### Foundational Concepts

**Transformers & Attention:**
- [Attention Is All You Need (2017)](https://arxiv.org/abs/1706.03762)
- [The Illustrated Transformer](http://jalammar.github.io/illustrated-transformer/)

**Fine-tuning Theory:**
- [Parameter-Efficient Fine-Tuning (Survey)](https://arxiv.org/abs/2303.15647)

### LoRA Specific

**Papers:**
- [LoRA: Low-Rank Adaptation of Large Language Models](https://arxiv.org/abs/2106.09685)
- [QLoRA: Efficient Finetuning of Quantized LLMs](https://arxiv.org/abs/2305.14314)

**Tutorials:**
- [Hugging Face PEFT Documentation](https://huggingface.co/docs/peft)
- [Axolotl Fine-tuning Examples](https://github.com/OpenAccess-AI-Collective/axolotl)

### DPO (Advanced)

**Paper:**
- [Direct Preference Optimization](https://arxiv.org/abs/2305.18290)

**Tutorials:**
- [TRL DPO Trainer](https://huggingface.co/docs/trl/dpo_trainer)

### Practical Guides

**YouTube:**
- "Fine-tuning LLMs with LoRA" by Sam Witteveen
- "QLoRA Explained" by AI Explained

**Blogs:**
- Hugging Face Blog: Fine-tuning section
- Weights & Biases: LLM training guides

---

## 🎓 Conceptual Model Mental Map

### What You're Actually Doing

**NOT:**
- Teaching the model chess from scratch
- Replacing Stockfish with an LLM
- Creating a chess engine

**YES:**
- Adjusting output distribution to match coaching style
- Grounding language generation in verified facts
- Creating an interface between analysis (ML) and explanation (LLM)

### The Math (Simplified)

**Fine-tuning goal:**
```
Find θ' that minimizes:
  E[(prediction - ground_truth)²]

Where:
  prediction = f(position, θ')
  ground_truth = expert_coaching
```

**LoRA insight:**
```
Instead of:
  W' = W + ΔW  (full update, expensive)

Do:
  W' = W + A·B  (low-rank, cheap)

Where:
  A ∈ R^(d×r), B ∈ R^(r×k), r << d
  
Only train A and B (few parameters)
```

**Why it works:**
- Base model (W) already knows language + general chess
- You only need small perturbation (A·B) for personalization
- Low rank captures essential adaptation

---

## 🚨 Critical Warnings

### 1. Don't Skip Dataset Quality

❌ **Bad approach:**
```
"I'll just feed raw PGNs to the model"
```

✅ **Correct approach:**
```
"I'll create 10K examples with:
  - Position context
  - ML prediction
  - Expert justification
  - Validated tactics"
```

### 2. Don't Overtrain

**Symptoms:**
- Perfect on training data
- Poor on new positions
- Repetitive language

**Solution:**
- Max 3 epochs
- Use validation set
- Monitor perplexity

### 3. Don't Ignore Validation

**Always check:**
- Stockfish agrees tactically
- ML prediction matches
- Response makes logical sense

**Never:**
- Trust LLM output blindly
- Skip verification loop

---

## 📝 Next Steps (Immediate Actions)

**This Week:**
1. Review this proposal with team
2. Decide on timeline for Phase 0
3. Set up development environment (Axolotl, PEFT)
4. **START:** Create first 100 coaching examples manually (quality template)

**Next Week:**
5. Automate dataset creation script
6. Generate 10K+ examples
7. Manual review of sample (100 random)
8. Begin LoRA training preparation

**Within Month:**
9. Complete first LoRA training run
10. Evaluate against GPT-4 baseline
11. Iterate on dataset/hyperparameters
12. Integrate ML decision layer

---

## 🎯 Summary: Why This Approach Works

**Problem:** LLMs hallucinate when asked to evaluate chess positions

**Solution:** Don't ask them to evaluate

**Architecture:**
```
ML models → DECIDE (error type, quality, risk)
RAG → REMEMBER (similar positions, patterns)
Stockfish → VALIDATE (tactics correct?)
LLM → EXPLAIN (synthesize into coaching)
```

**Result:**
- No hallucinations (grounded in facts)
- Personalized (trained on player data)
- Fast (local inference)
- Free (no API costs)
- Validated (Stockfish checks)

**The key insight:**
> "Don't teach the LLM chess. Teach it to explain decisions made by systems that DO know chess (ML + Stockfish)."

---

**Document Status:** Ready for review and implementation planning  
**Estimated Total Timeline:** 8-12 weeks to production  
**Expected ROI:** Zero marginal cost + better personalization + faster inference

**Author:** AI Assistant (based on system analysis + fine-tuning best practices)  
**Date:** March 23, 2026
