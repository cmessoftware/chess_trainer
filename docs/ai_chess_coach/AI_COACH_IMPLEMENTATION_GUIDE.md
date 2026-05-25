# AI Chess Coach - Installation & Setup Guide

## 🎯 Objetivo
Implementar el sistema completo de AI Chess Coach según el roadmap definido en `docs/0-ai_chess_coach_roadmap.md`

---

## 📋 FASE 1: Instalación de Dependencias

### 1.1 Dependencias Python (RAG + LLM)

```powershell
# CRITICAL: Activar ambiente conda chess_trainer
conda activate chess_trainer

# Instalar dependencias AI Coach
pip install -r requirements_ai_coach.txt

# Verificar instalación
python -c "import sentence_transformers; import chromadb; print('✅ RAG dependencies OK')"
```

### 1.2 Instalación de Ollama (Servidor LLM Local)

**Windows:**
```powershell
# Descargar e instalar Ollama
# https://ollama.ai/download/windows
# Descargar instalador desde el navegador
Start-Process "https://ollama.com/download/windows"

# O usar PowerShell para descargar
$url = "https://ollama.com/download/OllamaSetup.exe"
$output = "$env:USERPROFILE\Downloads\OllamaSetup.exe"
Invoke-WebRequest -Uri $url -OutFile $output

# Luego ejecutar el instalador
& "$env:USERPROFILE\Downloads\OllamaSetup.exe"

# O usar winget
winget install Ollama.Ollama

# Verificar instalación
ollama --version

# Descargar modelos recomendados
ollama pull llama3.2:3b      # Pequeño, rápido (3GB)
ollama pull mistral:7b       # Balanceado (4.1GB)
ollama pull phi3:medium      # Microsoft, optimizado (7.9GB)

# Verificar que Ollama está corriendo
Invoke-WebRequest -Uri http://localhost:11434 -Method GET
```

**Docker Alternative (si prefieres contenedores):**
```powershell
# Agregar servicio Ollama a docker-compose.yml
docker-compose up -d ollama
```

---

## 📂 FASE 2: Estructura de Directorios

```powershell
# Crear estructura para AI Coach
New-Item -ItemType Directory -Force -Path "src/ai_coach"
New-Item -ItemType Directory -Force -Path "src/ai_coach/rag"
New-Item -ItemType Directory -Force -Path "src/ai_coach/llm"
New-Item -ItemType Directory -Force -Path "src/ai_coach/prompts"
New-Item -ItemType Directory -Force -Path "data/chess_books"
New-Item -ItemType Directory -Force -Path "data/chess_books/raw"
New-Item -ItemType Directory -Force -Path "data/chess_books/processed"
New-Item -ItemType Directory -Force -Path "data/vectorstore"
```

---

## 🔧 FASE 3: Implementación de Módulos

### 3.1 Feature Summarizer (Phase 2)
**Archivo:** `src/ai_coach/feature_summarizer.py`

```python
"""
Converts ML features into interpretable summaries for LLM prompts.
"""
from typing import Dict, List, Any
import pandas as pd
import numpy as np

class FeatureSummarizer:
    """Summarizes chess game features for LLM coaching."""
    
    def summarize_game(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw features into coaching-friendly summaries.
        
        Returns:
            {
                "opening": str,
                "critical_moments": List[Dict],
                "patterns_detected": List[str],
                "tactical_motifs": List[str],
                "positional_themes": List[str]
            }
        """
        pass

    def summarize_player_history(self, games: pd.DataFrame) -> Dict[str, Any]:
        """Aggregate patterns from multiple games."""
        pass
```

### 3.2 RAG Knowledge System (Phase 3)
**Archivo:** `src/ai_coach/rag/chess_rag.py`

```python
"""
Chess Knowledge RAG System using ChromaDB + SentenceTransformers.
"""
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from typing import List, Dict
import logging

class ChessKnowledgeRAG:
    """RAG system for chess coaching knowledge."""
    
    def __init__(self, 
                 vectorstore_path: str = "data/vectorstore",
                 model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize RAG system.
        
        Args:
            vectorstore_path: Path to Chroma vector database
            model_name: SentenceTransformer model for embeddings
        """
        self.embedding_model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path=vectorstore_path)
        self.collection = self.client.get_or_create_collection(
            name="chess_knowledge",
            metadata={"hnsw:space": "cosine"}
        )
        
    def ingest_chess_book(self, pdf_path: str):
        """Extract and index chess book content."""
        pass
    
    def retrieve_knowledge(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve relevant chess knowledge.
        
        Args:
            query: Coaching context (e.g., "King safety in middlegame")
            top_k: Number of results
            
        Returns:
            List of relevant knowledge chunks
        """
        pass
```

### 3.3 LLM Integration (Phase 4)
**Archivo:** `src/ai_coach/llm/coaching_llm.py`

```python
"""
LLM Integration using Ollama for chess coaching.
"""
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from typing import Dict, Any
import json

class ChessCoachLLM:
    """LLM-powered chess coaching assistant."""
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        """
        Initialize coaching LLM.
        
        Args:
            model_name: Ollama model to use
        """
        self.llm = OllamaLLM(
            model=model_name,
            base_url="http://localhost:11434",
            temperature=0.7
        )
        
    def generate_coaching_report(self, 
                                  game_summary: Dict[str, Any],
                                  rag_context: List[Dict]) -> Dict[str, Any]:
        """
        Generate structured coaching report.
        
        Returns:
            {
                "opening_analysis": str,
                "strengths": List[str],
                "weaknesses": List[str],
                "critical_mistakes": List[Dict],
                "training_recommendations": List[str]
            }
        """
        pass
```

### 3.4 Complete Pipeline Orchestrator  
**Archivo:** `src/ai_coach/coach_pipeline.py`

```python
"""
Complete AI Chess Coach Pipeline.
"""
from .feature_summarizer import FeatureSummarizer
from .rag.chess_rag import ChessKnowledgeRAG
from .llm.coaching_llm import ChessCoachLLM
from typing import Dict, Any
import logging

class ChessCoachPipeline:
    """Orchestrates complete AI coaching pipeline."""
    
    def __init__(self):
        self.summarizer = FeatureSummarizer()
        self.rag = ChessKnowledgeRAG()
        self.llm = ChessCoachLLM()
        
    def analyze_game(self, game_id: int) -> Dict[str, Any]:
        """
        Complete game analysis pipeline.
        
        Steps:
            1. Load game features from DB
            2. Summarize features
            3. Retrieve relevant knowledge (RAG)
            4. Generate LLM coaching report
            5. Validate and format output
        """
        pass
    
    def analyze_player_profile(self, player_id: str, 
                                num_games: int = 50) -> Dict[str, Any]:
        """Aggregate analysis across multiple games."""
        pass
```

---

## 🧪 FASE 4: Testing & Validation

### 4.1 Test de Instalación

```python
# tests/ai_coach/test_installation.py
import pytest

def test_ollama_connection():
    """Verify Ollama is running."""
    import httpx
    response = httpx.get("http://localhost:11434")
    assert response.status_code == 200

def test_embeddings():
    """Test sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(["test sentence"])
    assert embeddings.shape[0] == 1

def test_chromadb():
    """Test vector database."""
    import chromadb
    client = chromadb.Client()
    collection = client.create_collection("test")
    assert collection.name == "test"
```

### 4.2 Test Funcional de Pipeline

```python
# tests/ai_coach/test_pipeline.py
def test_feature_summarizer():
    """Test feature summarization."""
    pass

def test_rag_retrieval():
    """Test knowledge retrieval."""
    pass

def test_llm_generation():
    """Test LLM report generation."""
    pass

def test_complete_pipeline():
    """Test end-to-end pipeline."""
    pass
```

---

## 📊 FASE 5: Integración con API Backend

### 5.1 Nuevos Endpoints en FastAPI  
**Archivo:** `src/api/routers/ai_coach.py`

```python
from fastapi import APIRouter, HTTPException
from src.ai_coach.coach_pipeline import ChessCoachPipeline

router = APIRouter(prefix="/ai-coach", tags=["AI Coach"])
pipeline = ChessCoachPipeline()

@router.post("/analyze-game/{game_id}")
async def analyze_game(game_id: int):
    """Generate AI coaching report for a game."""
    try:
        report = pipeline.analyze_game(game_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-player/{player_id}")
async def analyze_player(player_id: str, num_games: int = 50):
    """Generate player profile analysis."""
    try:
        profile = pipeline.analyze_player_profile(player_id, num_games)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 🎯 FASE 6: Integración con Frontend React

### 6.1 Nuevos Componentes React
```typescript
// src/frontend/src/components/AICoach/CoachingReport.tsx
export const CoachingReport = ({ gameId }: { gameId: number }) => {
  // Fetch coaching report from backend
  // Display: strengths, weaknesses, recommendations
}

// src/frontend/src/components/AICoach/PlayerProfile.tsx
export const PlayerProfile = ({ playerId }: { playerId: string }) => {
  // Display long-term patterns and recommendations
}
```

---

## ⚡ COMANDOS RÁPIDOS DE IMPLEMENTACIÓN

```powershell
# 1. Instalar todo
conda activate chess_trainer
pip install -r requirements_ai_coach.txt
ollama pull llama3.2:3b

# 2. Crear estructura
./setup_ai_coach_structure.ps1

# 3. Ejecutar tests
pytest tests/ai_coach/ -v

# 4. Iniciar servicios
docker-compose up -d
ollama serve  # Si no está como servicio

# 5. Probar pipeline
python src/scripts/test_ai_coach_pipeline.py
```

---

## 📚 RECURSOS ADICIONALES

### Chess Books para RAG
- **Recomendados:**
  - "My System" - Aron Nimzowitsch
  - "Logical Chess Move by Move" - Irving Chernev
  - "The Art of Attack in Chess" - Vladimir Vukovic
  - "Endgame Strategy" - Mikhail Shereshevsky

### Modelos LLM Recomendados
| Modelo      | Tamaño | Uso                | Velocidad |
| ----------- | ------ | ------------------ | --------- |
| llama3.2:3b | 3GB    | Desarrollo/Testing | ⚡⚡⚡       |
| mistral:7b  | 4.1GB  | Producción         | ⚡⚡        |
| llama3.1:8b | 4.7GB  | Producción         | ⚡⚡        |
| phi3:medium | 7.9GB  | Enterprise         | ⚡         |

---

## 🚨 NOTAS IMPORTANTES

1. **⚠️ CRITICAL**: Usar SIEMPRE `conda activate chess_trainer` antes de ejecutar scripts
2. **Ollama**: Debe estar ejecutándose en `localhost:11434`
3. **RAM**: Modelos LLM requieren mínimo 8GB RAM
4. **GPU**: Opcional pero recomendado para modelos > 7B
5. **Vector DB**: Chroma se guarda en disco, no requiere servidor adicional

---

## 📝 PRÓXIMOS PASOS

1. ✅ Instalar dependencias (`requirements_ai_coach.txt`)
2. ✅ Instalar Ollama y descargar modelo
3. 🔄 Implementar `feature_summarizer.py`
4. 🔄 Implementar `chess_rag.py`
5. 🔄 Implementar `coaching_llm.py`
6. 🔄 Crear pipeline completo
7. 🔄 Tests unitarios e integración
8. 🔄 Integrar con API backend
9. 🔄 Integrar con frontend React

---

**Última actualización:** 2026-03-13
**Estado:** Listo para implementación
