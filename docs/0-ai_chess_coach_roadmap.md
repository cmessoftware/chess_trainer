Roadmap general del sistema

# ChessTrainer AI Coach – Implementation Roadmap

## Objective

Provide a roadmap for implementing the AI coaching system in ChessTrainer.

The system combines:

- Stockfish analysis
- ML feature extraction
- RAG knowledge retrieval
- local LLM coaching
- player pattern analysis

---

# Documentation Map

This roadmap references the design documents and guides.

## Design Documents

1. [AI Coach Design](1-ai_chess_coach_rag_design.md)
   
2. [Module Specification](2-ai_chess_coach_module_spec.md)
   
3. [UI Integration Flow](3-ai_chess_coach_ui_flow.md)
   
4. [Structured Output](4-ai_chess_coach_structured_output.md)
   
5. [Engine Grounding Layer](5-ai_chess_coach_engine_grounding.md)
   
6. [Player Pattern Analysis](6-ai_chess_coach_patterm_analysis.md)
   
7. [Player Style Classification & ML-Based Coaching](7-ai_chess_coach_style_classification.md)
   
8. [Kasparov-Inspired Analysis Module](8-ai_chess_coach_kasparov_roadmap.md)
   
9. [Kasparov Decision Engine - Functional Design](9-ai_chess_coach_kasparov_inspired_functional.md)
    
10. [Kasparov Decision Engine - Technical Design](10-ai_chess_coach_kasparov_technical_design.md)

11. [Position Embeddings](11-ai_chess_coach_position_embeddings.md)

## Implementation Guides

- [**Testing Guide**](AI_CHESS_COACH_TESTING_GUIDE.md) - How to test the AI Coach system ⭐ **START HERE**
- [Implementation Guide](AI_COACH_IMPLEMENTATION_GUIDE.md) - Full implementation walkthrough
- [Quick Start](AI_COACH_QUICKSTART.md) - Fast setup and installation
- [Checklist](AI_COACH_CHECKLIST.md) - Implementation progress tracker


---

# System Overview

Complete pipeline:

PGN upload  
→ Stockfish analysis  
→ feature extraction  
→ ML evaluation  
→ **ML style classification** *(planned)*  
→ feature summarizer  
→ RAG retrieval  
→ LLM structured report  
→ UI rendering  
→ dataset storage  
→ player pattern analysis

---

# Development Phases

The system should be implemented in phases.

---

# Implementation Status

**Last Updated:** March 23, 2026

**Overall Progress: ~50%** (Core backend operational, UI integration pending)

## Completed Phases

### ✅ Phase 1 – Core Game Analysis (COMPLETED - 100%)
- PGN parsing functional
- Stockfish integration working
- Feature extraction pipeline operational
- ML predictions active
- **Script:** `src/scripts/generate_features_with_tactics.py`

### ✅ Phase 3 – RAG Knowledge System (COMPLETED)
**Status:** Operational with 53/66 chess books processed

**Achievements:**
- ChromaDB vector database: 8,553 documents indexed
- SentenceTransformers embeddings: `all-MiniLM-L6-v2` model
- PDF processing pipeline with checkpoint system
- Multi-format support: pdfplumber + PyPDF2 + OCR
- Knowledge sources:
  - Modern Chess Openings (MCO-15) - processing with OCR
  - Various tactical/strategic chess books
  - Opening theory references

**Implementation:**
- `src/ai_coach/rag/chess_rag.py` - RAG system class
- `src/ai_coach/rag/pdf_processor.py` - PDF extraction with OCR
- `src/scripts/init_chess_rag.py` - Batch processing script
- `data/chess_books/chroma_db/` - Vector database storage
- `data/chess_books/processing_checkpoint.json` - Resume capability

**Pending:**
- 13 scanned PDFs require Tesseract OCR binary installation
- Complete processing of remaining books

### ✅ Phase 4 – LLM Integration (OPERATIONAL - 85%)
**Status:** Backend API functional with pedagogical report generation

**Achievements:**
- ✅ Ollama containerized (Docker Compose)
- ✅ Models operational:
  - `llama3.2:3b` (development, 3GB) - ACTIVE
  - `llama3.1:8b` (production, 4.7GB) - AVAILABLE
- ✅ **LLM Analysis Service implemented** (`src/api/services/llm_analysis_service.py`)
  - Double-pass architecture (JSON → Narrative)
  - Anti-hallucination system with FACTS_PACK validation
  - ELO-adaptive pedagogy (4 levels: <1600, 1600-2000, 2000-2100, >2100)
  - Competitive context analysis
  - Material event tracking
  - Evaluative swing detection
- ✅ **API Endpoints active:**
  - `POST /api/analysis/generate-llm-report` - Individual report
  - `POST /api/analysis/generate-batch-llm-reports` - Batch processing
- ✅ RAG+LLM integration tests passing

**Implementation:**
- `src/api/services/llm_analysis_service.py` - Main service (2,200+ lines)
- `src/api/services/prompt_validator.py` - Prompt validation
- `src/api/services/json_validator.py` - Output validation
- `src/api/routers/analysis.py` - API endpoints
- `docker-compose.yml` - Ollama service configuration

**Key Features:**
- Anti-hallucination rules (prevents inventing material losses, swings)
- Result-aware coaching (win/loss/draw adaptive feedback)
- Phase-specific error analysis (opening/middlegame/endgame)
- Calibrated severity by player ELO

**Pending:**
- OpenAI integration for production (currently uses OpenAI API, not Ollama)
- Full Ollama migration for local deployment

### ✅ Engine Grounding Layer (IMPLEMENTED)
**Status:** RAG mitigation working, pending full Stockfish integration

**Purpose:** Prevent LLM hallucinations using verified chess knowledge

**Implementation:**
- RAG retrieval from 8,553 chess book excerpts
- Context injection before LLM generation
- Test validation: RAG vs non-RAG shows 100% accuracy improvement

**Design Document:** [5-ai_chess_coach_engine_grounding.md](5-ai_chess_coach_engine_grounding.md)

**Pending:**
- Full integration: Stockfish analysis → RAG → LLM pipeline
- Structured JSON output from Stockfish
- Move validation layer

## In Progress

### ⏳ Phase 2 – Feature Summarizer (PARTIAL - 40%)
**Status:** Base implementation complete, integration pending

**Completed:**
- ✅ `src/ai_coach/feature_summarizer.py` - Feature to text conversion
- ✅ Tactical motifs mapping
- ✅ Positional themes detection
- ✅ Opening summarization
- ✅ Performance metrics formatting

**Pending:**
- Full integration with LLM service
- Extended pattern detection
- Multi-game aggregation

### ⏳ Phase 5 – Structured Output (PARTIAL - 40%)
**Status:** JSON validation implemented, schema expansion pending

**Completed:**
- ✅ `src/api/services/json_validator.py` - JSON schema validation
- ✅ Structured analysis schema (decisive_move, error_type, etc.)
- ✅ Validation in double-pass architecture

**Pending:**
- Complete schema definition for all report types
- Extended validation rules
- Schema versioning system

### ⏳ RAG System Completion (OCR Processing - 90%)
**Current Status:** 53/66 books processed, 13 scanned PDFs pending
- ✅ Tesseract OCR installed and configured
- ✅ Spanish language data (spa.traineddata) installed
- ✅ Memory-optimized batch processing (5 pages at 200 DPI)
- ⏳ Remaining: 13 scanned PDFs (~1-2 hours)
- Current: 8,553 documents in ChromaDB
- Expected final: ~10,000-12,000 total chunks

**Technical Implementation:**
- OCR Engine: Tesseract v5.5.0 with pytesseract wrapper
- Languages: Spanish + English (spa+eng)
- Processing: Batch processing to avoid MemoryError
- Performance: ~10-15 sec/page
- Checkpoint system: Resume capability on interruption

## Not Started

### ⏸️ Phase 6 – UI Integration (NOT STARTED - 0%)
**Blocker:** Requires React frontend development

**Pending:**
- Frontend component for report display
- API integration with `/generate-llm-report` endpoint
- Report visualization (strengths/weaknesses/recommendations)
- Styling and UX design

### ⏸️ Phase 7 – Player Pattern Analysis (NOT STARTED - 0%)
**Blocker:** Requires report storage system and multi-game database

**Pending:**
- Report storage schema
- Multi-game aggregation logic
- Pattern detection algorithms
- Player profile generation

### ⏸️ Phase 7.5 – Player Style Classification (SPECIFICATION COMPLETE - 0%)
**Status:** Design document complete, implementation pending

**Documentation:** [7-ai_chess_coach_style_classification.md](7-ai_chess_coach_style_classification.md)

**Taxonomy:** Aggressive, Tactical, Positional, Solid, Speculator

**Pending:**
- ML model training (style classification)
- Model integration with LLM service
- Enhanced prompts with style context
- Database schema for style data
- UI style badge component

**Estimated Timeline:** 4 weeks

### ⏸️ Phase 8 – Training Recommendation Engine (NOT STARTED - 0%)
**Blocker:** Requires player patterns and style classification

**Pending:**
- Exercise database
- Recommendation algorithms
- Style-specific training paths
- Progress tracking system

### ⏸️ Phase 9 – Advanced Features (NOT STARTED - 0%)
**Blocker:** Requires complete system integration

**Planned:**
- Position embeddings
- Kasparov-inspired decision engine
- Advanced tactical pattern recognition

---

# Phase 1 – Core Game Analysis

Goal:

generate structured features for a game.

Tasks:

- PGN parsing
- Stockfish analysis
- feature extraction
- ML predictions

Output:

structured game dataset.

---

# Phase 2 – Feature Summarizer

Goal:

convert features into interpretable summaries for LLM prompts.

Tasks:

implement:

feature_summarizer.py

Output example:

Opening  
Critical moments  
Patterns detected  
Tactical motifs

---

# Phase 3 – RAG Knowledge System

Goal:

retrieve chess knowledge from books.

Tasks:

1 collect chess books
2 extract text from PDFs
3 chunk text
4 generate embeddings
5 store vectors in database

Recommended stack:

SentenceTransformers  
Chroma vector DB

---

# Phase 4 – LLM Integration

Goal:

generate coaching reports.

Tasks:

- integrate Ollama
- implement prompt builder
- generate structured JSON reports

Models:

llama3  
mistral  
phi3

---

# Phase 5 – Structured Output

Goal:

enforce consistent report format.

Tasks:

- define JSON schema
- validate output
- retry on invalid response

Output example:

{
"opening": "",
"strengths": [],
"weaknesses": [],
"training_topics": []
}


---

# Phase 6 – UI Integration

Goal:

connect pipeline to user interface.

User workflow:

Upload PGN  
System analyzes game automatically  
UI displays report and metrics

UI sections:

- coaching report
- metrics dashboard
- critical moments viewer

---

# Phase 7 – Player Pattern Analysis

Goal:

analyze hundreds of games.

Tasks:

- store reports
- aggregate metrics
- detect recurring errors
- generate player profile

Example output:

Most frequent mistakes  
Training recommendations

---

# Phase 7.5 – Player Style Classification & ML-Based Coaching

**Design Document:** [7-ai_chess_coach_style_classification.md](7-ai_chess_coach_style_classification.md)

Goal:

Classify player style using ML models and personalize coaching feedback.

Tasks:

- Train style classification models (aggressive, tactical, positional, solid, speculator)
- Integrate style predictions into LLM prompts
- Generate style-aware coaching reports
- Display style badges in UI

Style Taxonomy:

- **Aggressive** - High risk, tactical play, frequent attacks
- **Tactical** - Combination-focused, sharp positions  
- **Positional** - Strategic, long-term planning, solid structure
- **Solid** - Defensive, low error rate, patient play
- **Speculator** - High variance, risky moves, unbalanced positions

Example output:

```json
{
  "style_cluster": "aggressive",
  "confidence": 0.87,
  "style_analysis": "Aggressive style created early pressure but led to premature attacks",
  "style_specific_recommendations": [
    "Study prepared attacks (Tal, Kasparov games)",
    "Practice 'when to attack' checklist"
  ]
}
```

**Status:** PLANNED - Model training pending

---

# Phase 8 – Training Recommendation Engine

Goal:

suggest exercises automatically.

Inputs:

- player patterns
- detected weaknesses
- player style classification

Outputs:

training topics

Example:

fork tactics  
king safety  
endgame technique

---

# Phase 9 – Advanced Features

Future improvements:

- conversational chess coach
- automatic puzzle generation
- embeddings for chess positions
- similarity search for positions
- training plan generator
- **chess diagram recognition from books** ⚠️ (see Phase 10)

---

# Phase 10 – Chess Diagram Recognition (Future)

**Status:** Not prioritized - Text-based RAG is sufficient for MVP

**Goal:** Extract FEN positions from chess diagrams in PDF books

**Current Limitation:**
- OCR extracts **text only** (moves, annotations, explanations)
- Chess board **diagrams are ignored** (visual images)
- No FEN generation from book positions

**Why Not Critical:**
- Algebraic notation (1.e4 e5 2.Nf3) allows position reconstruction
- LLM can simulate positions from move sequences
- Real game analysis uses database FENs (not book diagrams)

**Implementation Options:**

### Option A: Computer Vision (Open Source)
**Complexity:** High (~80-120 hours development)

**Tech Stack:**
```python
import cv2                    # Board detection
import tensorflow as tf      # Piece classification
from PIL import Image
```

**Libraries:**
- `tensorflow-chessbot` - Deep learning for board recognition
- `chessboard-finder` - OpenCV board detection
- `chess-board-recognition` - CNN + FEN generator

**Process:**
1. Detect chess diagram in PDF page (OpenCV edge detection)
2. Extract 8×8 grid squares
3. Classify each piece with CNN (trained model required)
4. Generate FEN from piece positions
5. Index FEN in ChromaDB with context

**Challenges:**
- 📖 Each book has different diagram styles
- 🎨 Varying piece graphics (figurine notation vs symbols)
- ⚠️ False positives on partial boards
- 🧠 Requires training/fine-tuning CNN on chess book images

### Option B: Chessify API (Paid Service) ✨
**Complexity:** Low (~8-16 hours integration)

**Service:** [Chessify Board Recognition API](https://chessify.me/api)

**Pricing:** (Verify current rates)
- Pay-per-image processing
- Subscription tiers available
- Enterprise options for bulk processing

**Integration:**
```python
import requests
from pdf2image import convert_from_path

def extract_diagrams_with_chessify(pdf_path, api_key):
    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=300)
    
    fens = []
    for i, image in enumerate(images):
        # Call Chessify API
        response = requests.post(
            "https://api.chessify.me/v1/board-recognition",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"image": image_to_bytes(image)}
        )
        
        if response.json().get("board_detected"):
            fen = response.json()["fen"]
            fens.append({"page": i, "fen": fen})
    
    return fens
```

**Advantages:**
- ✅ Robust recognition (commercial-grade)
- ✅ Handles multiple diagram styles
- ✅ No training data required
- ✅ API handles edge cases
- ✅ Faster time to production

**Disadvantages:**
- 💰 Ongoing cost (pay per image)
- 🔒 Dependency on external service
- 🌐 Requires internet connectivity
- 📊 Cost analysis needed for 66 books

**Cost Estimation Example:**
- 66 books × ~50 diagrams/book = **3,300 diagrams**
- If $0.05/image → **$165 one-time**
- If $0.10/image → **$330 one-time**
- Verify current Chessify pricing

### Option C: Hybrid Approach
- Use **text OCR** for most content (current implementation)
- Manually annotate **critical positions** from key books
- Use **Chessify API** only for high-priority books (e.g., MCO-15)
- Defer full automation until proven ROI

### Recommendation
**Priority:** LOW (Phase 10 - deferred)

**Rationale:**
1. Text-based RAG covers ~95% of chess knowledge
2. Move sequences allow position reconstruction
3. Development cost (80-120h) vs benefit unclear
4. API cost ($165-$330) acceptable if feature proves valuable

**Decision Point:**
- ✅ Launch AI Coach with text-only RAG
- 📊 Measure user demand for diagram search
- 💡 If users request "find this position" frequently → implement
- 🚀 If adoption is high → justify Chessify API or CV development

**Documentation:**
- See `docs/DIAGRAM_RECOGNITION_OPTIONS.md` (to be created)
- Chessify API docs: https://chessify.me/api/docs

---

# Final Vision

The completed system will function as an AI chess coach.

Capabilities:

Analyze games  
Explain mistakes  
Recommend training  
Track long-term improvement

ChessTrainer evolves from:

Game analyzer

into:

AI training platform.

