# CHESS TRAINER - Versión: v0.1.138-fda75dc

# ♟ chess_trainer – Analysis and Training for All Chess Players

This project automates the import, analysis, labeling, and training from thousands of chess games across all skill levels (from beginners to masters), combining tactical analysis with visual exploration and personalized exercise generation using a modern tech stack with **React + Vite** frontend and **FastAPI** backend.

## 🚀 Tech Stack

### Frontend
- **React 19** + **TypeScript** - Modern component-based UI framework
- **Vite** - Fast build tool and development server
- **Material-UI (MUI)** - Professional React component library
- **React Query (@tanstack/react-query)** - Server state management
- **Chess.js** + **React-Chessboard** - Chess logic and interactive board
- **React Router Dom** - Client-side routing

### Backend  
- **FastAPI** - High-performance Python web framework
- **PostgreSQL** - Production-ready relational database
- **MLflow** - Machine learning experiment tracking
- **Stockfish** - Chess engine for move analysis
- **Docker + Docker Compose** - Containerized development environment

### Data Science & ML
- **Python** ecosystem: pandas, numpy, scikit-learn, tensorflow
- **Jupyter Notebooks** - Interactive data analysis and ML experimentation
- **Alembic** - Database migrations
- **PGN parsing** - Chess game format processing

### 🤖 AI Chess Coach
- **Ollama + LangChain** - Local LLM server for coaching report generation
- **ChromaDB + SentenceTransformers** - Vector database (RAG) for chess knowledge retrieval
- **Orchestrated Architecture** - Planner / Executor / Memory / Critic / Explainer pipeline
- **FeatureSummarizer** - Converts ML features into human-readable coaching prompts

---

## 📚 Documentation Index

### Core Documentation
- **[Changelog](./docs/CHANGELOG.md)** - Complete project changelog with version history
- **[Main README](./README.md)** - Complete project documentation (this file)  
- **[README (Español)](./docs/README_es.md)** - Documentación completa del proyecto en español
- **[Version Base (English)](./docs/VERSION_BASE.md)** - Project overview and quick start guide
- **[Version Base (Español)](./docs/VERSION_BASE_es.md)** - Descripción del proyecto y guía rápida en español
- **[Technical Roadmap](./docs/ROADMAP_TECHNICAL.md)** - 6-phase development roadmap with current status
- **[Frontend Roadmap](./docs/ROADMAP_FRONT_CHESS_TRAINER.md)** - React frontend development roadmap

### Technical Documentation
- **[MLflow PostgreSQL Integration](./docs/MLFLOW_POSTGRES_INTEGRATION.md)** - Guide for the MLflow PostgreSQL backend integration
- **[Reliable Predictions with MLflow](./docs/PREDICCIONES_FIABLES_MLFLOW.md)** - Complete guide for making reliable chess move predictions
- **[ELO Standardization Guide](./docs/ELO_STANDARDIZATION_GUIDE.md)** - Technical guide for the ELO standardization system
- **[Issue #21 Completion Report](./docs/ISSUE_21_COMPLETION_REPORT.md)** - Complete report on ELO standardization implementation
- **[Docker Development Strategy](./docs/DOCKER_DEVELOPMENT_STRATEGY.md)** - Docker development workflow guide
- **[Datasets Volumes Config](./docs/DATASETS_VOLUMES_CONFIG.md)** - Volume configuration for datasets
- **[Git LFS Setup Guide](./docs/GIT_LFS_SETUP_GUIDE.md)** - Git Large File Storage setup guide

### Development & Setup Guides
- **[Ejecutar Entorno DEV](./docs/EJECUTAR_ENTORNO_DEV.md)** - Guía completa para configurar entorno de desarrollo
- **[Feature Enhancement Guide](./docs/GENERATE_FEATURES_ENHANCEMENT.md)** - Guide for chess feature generation improvements
- **[Architecture Improvement Update](./docs/ARCHITECTURE_IMPROVEMENT_UPDATE.md)** - Latest architecture improvements and updates
- **[Postman Runner Guide](./docs/POSTMAN_RUNNER_GUIDE.md)** - API testing with Postman automation
- **[Task Completion Summary](./docs/TASK_COMPLETION_SUMMARY.md)** - Project milestones and completion status

### Training & Studies System
- **[Complete PGN Studies System](./docs/ESTUDIOS_PGN_SISTEMA_COMPLETO.md)** - Sistema completo de estudios PGN y análisis
- **[Training System Complete](./docs/TRAINING_SYSTEM_COMPLETE.md)** - Complete training resources management system
- **[Custom Studies Tutorial](./docs/TUTORIAL_ESTUDIOS_PERSONALIZADOS.md)** - Tutorial for creating personalized chess studies
- **[Datasets Report](./docs/DATASETS_REPORT.md)** - Comprehensive analysis of available chess datasets

### 🤖 AI Chess Coach Documentation
- **[AI Coach Roadmap](./docs/0-ai_chess_coach_roadmap.md)** - Vision and roadmap for the AI coaching system
- **[AI Coach Module Spec](./docs/2-ai_chess_coach_module_spec.md)** - Technical module specification
- **[RAG Design](./docs/1-ai_chess_coach_rag_design.md)** - ChromaDB + SentenceTransformers RAG design
- **[Structured Output](./docs/4-ai_chess_coach_structured_output.md)** - JSON schema validation for coaching output
- **[Orchestrated Architecture](./docs/ChessTrainer%20%E2%80%94%20Arquitectura%20Orquestada%20(Planner%20,%20Executor,%20Critic%20,%20Memory).md)** - Planner/Executor/Critic/Memory architecture
- **[Player Pattern Analysis](./docs/6-ai_chess_coach_patterm_analysis.md)** - Player error patterns and clustering
- **[Player Style Analysis](./docs/7-ai_chess_coach_player_style_analysis.md)** - Playing style classification system

## 🚀 Quick Start

### Option 1: Complete Environment Setup (Recommended)

#### Windows Users - One-Command Setup:
```powershell
# Complete setup: Backend + Frontend + Database
.\build_up_clean_all.ps1
```

#### Manual Setup:
```bash
# Start all services with Docker Compose
docker-compose up -d

# Install frontend dependencies and start development server
cd src/frontend
npm install
npm run dev

# Start FastAPI backend (in another terminal)
cd src/api
python -m uvicorn main:app --reload --port 8000
```

### Option 2: Development Mode

#### Start Backend API:
```powershell
# Using PowerShell tasks (recommended)
.\ds_tools.ps1 -Action StartAPI

# Or manually
cd src/api
python -m uvicorn main:app --reload --port 8000
```

#### Start Frontend:
```bash
cd src/frontend
npm run dev
```

### 🌐 Access Points:
- **Frontend (React)**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **MLflow UI**: http://localhost:5000
- **Database**: PostgreSQL on localhost:5432

### 🎯 Benefits of Current Architecture:
- **Modern UI/UX**: React + Material-UI for professional interface
- **Type Safety**: TypeScript for frontend reliability  
- **High Performance**: Vite for fast development and FastAPI for backend speed
- **Real-time Updates**: React Query for efficient server state management
- **Scalable**: Docker containerization for consistent environments
- **ML Integration**: MLflow for experiment tracking and model management

# chess_trainer
Modern chess training platform using React + TypeScript frontend, FastAPI backend, and advanced ML pipeline with MLflow integration for chess analysis and player improvement.

## 🏗️ Architecture Overview

### Frontend Architecture (React + Vite)
```
src/frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Route-based page components  
│   ├── hooks/         # Custom React hooks
│   ├── services/      # API client services
│   ├── utils/         # Helper functions
│   └── types/         # TypeScript type definitions
├── public/            # Static assets
└── package.json       # Dependencies and scripts
```

### Backend Architecture (FastAPI)
```
src/api/
├── routers/           # API route handlers
│   ├── auth.py       # Authentication endpoints
│   ├── chess.py      # Chess-specific endpoints
│   └── logs.py       # Logging endpoints
├── models/           # Pydantic data models
├── services/         # Business logic services
├── middleware/       # Custom middleware
└── main.py          # FastAPI application entry point
```

### 🤖 AI Chess Coach Architecture (Orchestrated)
```
src/ai_coach/
├── feature_summarizer.py           # ✅ ML features → human-readable text
├── rag/
│   ├── chess_rag.py                # ✅ ChromaDB + SentenceTransformers RAG system
│   └── pdf_processor.py            # ✅ PDF chess book ingestion
├── orchestrated/                   # ✅ Orchestrated analysis pipeline (v0.1.108+)
│   ├── schemas.py                  # ✅ Pydantic schemas (AnalysisOptions, Plan, Result…)
│   ├── planner_service.py          # ✅ Decides WHAT to analyze (critical move detection)
│   ├── executor_service.py         # ✅ Produces EVIDENCE (engine + ML + RAG async)
│   └── memory_service.py           # ✅ Persists results (dual-write v2.0 + v1.0)
└── llm/
    └── (coaching_llm.py)           # ⏳ LLM coaching report generation (next phase)
```

**Orchestrated Pipeline Flow:**
```
PGN Input
   │
   ▼
PlannerService  ──▶  Identifies critical moves (eval swing, blunders, tactics)
   │
   ▼
ExecutorService ──▶  Engine analysis + Feature extraction + ML (parallel) + RAG
   │
   ▼
MemoryService   ──▶  Persists move_analyses + player_patterns (PostgreSQL)
   │
   ▼
(ExplainerService) ──▶  LLM coaching report (⏳ next phase)
```

### 🔄 Data Flow:
1. **React Frontend** makes API calls to FastAPI backend
2. **FastAPI** processes requests, interacts with PostgreSQL
3. **MLflow** tracks experiments and model performance
4. **Stockfish** provides chess engine analysis
5. **Real-time updates** via React Query state management

## 🧠 Theory on chess game analysis

To use Machine Learning (ML) and Artificial Intelligence (AI) in chess game analysis, you must first understand how game data is represented and how AIs can "learn" game patterns.

To use Machine Learning (ML) and Artificial Intelligence (AI) in chess game analysis, you must first understand how game data is represented and how AIs can "learn" game patterns.

## 1. Representation of game information
Chess games can be represented in different ways. One of the most common is the PGN (Portable Game Notation) format, a standard format used to store the moves of a game. Each move is expressed in algebraic notation, for example: "e4" or "Nf3".

**Some key elements you can analyze from a game are:**

- Opening: The first moves of the game, which are well studied in chess.

- Errors and blunders (serious mistakes): Moves that are significantly worse compared to the best possible moves.

- Accuracy: The number of correct moves made during the game.

- Result: Whether you won, lost, or drew.

- Time spent: Whether the player made impulsive moves or thought a lot before playing.

**Game features**

In Machine Learning terms, the features of the game are the data that feed the models so they can make predictions.

**Some key features could be:**

- Number of errors and blunders: This could indicate the player's general skill.

- Move accuracy: How close the player is to optimal moves.

- Openings: Whether the player prefers a specific opening (e.g., Sicilian, Ruy Lopez, etc.).

- Piece development: Whether the player follows good opening and positioning principles.

- Game score: Whether it was a win, loss, or draw.

## 2. Machine Learning applied to chess

**Objective of Machine Learning in chess**

The main objective of Machine Learning (ML) in this context is to build a model that can identify patterns or make predictions about a player's playing style or the outcome of a game, based on historical data (previous games). Depending on the type of problem, there are several ways to approach the solution:

- Classification: Predict a class (e.g., whether a game will have serious errors or not).

- Regression: Predict a continuous value (such as a player's accuracy during a game).

- Cluster analysis: Group players with similar characteristics (e.g., players who make similar mistakes).

- Outcome prediction: Determine the probability that a player will win, lose, or draw based on previous moves.

**Machine Learning models**

Some of the most used models for chess and game analysis are:

- Regression models:

    To predict a continuous variable, such as a player's accuracy or score.

- Classification models:

    To classify games according to the type of error or whether the player has an "aggressive", "defensive", etc. style.

    For example, Random Forest and Support Vector Machines (SVM) are useful for these types of tasks.

- Neural networks:

    More advanced, these networks can learn complex patterns in the data. They are used for tasks such as pattern recognition or move prediction.

    Neural networks are also used in chess for more sophisticated predictions, such as those made by AlphaZero, which uses a deep neural network to play chess.

## 3. How to apply Machine Learning to chess analysis

**Data preprocessing**

Before feeding a Machine Learning model, you need to preprocess the data to transform it into a form the model can understand. This may include:

- Data cleaning:

    - Remove or impute null values.

    - Ensure all data is in the correct format (e.g., convert dates to a proper date format or classify errors).

**Data transformation:**

- Convert moves and openings into a numeric format:

    For example, using one-hot encoding or natural language processing techniques like Word2Vec for openings.

- Normalization and scaling:

    Some features (such as accuracy) may have different ranges. Make sure to scale them so the model is not biased toward certain features.

- Model training

    Once you have preprocessed your data, you can start training your model. To do this, you must split your data into two parts:

        Training set:
        The dataset on which you train the model.

        Test set:
        The dataset the model has not seen, to evaluate its performance.

The model will learn from the features of the games, such as errors, accuracy, and openings, and will try to predict the outcome of the game or identify playing patterns.

- Model evaluation

    Once your model is trained, you must evaluate its performance using the test set. Some common metrics for evaluating classification models are:

        Accuracy: Proportion of correct predictions.

        Precision: How accurate the positive predictions are.

        Recall: How well the model detects all positive predictions.

        F1-score: A combination of precision and recall.

        Hyperparameter tuning

        Some models like Random Forest or SVM have "hyperparameters" that you can adjust to improve model performance. You can use techniques like GridSearchCV to find the best hyperparameters.

## 4. Personalized recommendations to improve play

Once the model is trained, you can use it to make personalized recommendations to players based on their playing style and previous mistakes. For example:

- Opening recommendations:

    If the player makes mistakes in a specific opening, you can suggest other safer openings.

- Move suggestions:

    Based on their style and mistakes made in previous games, the model can suggest more accurate moves or more effective strategies.

- Analysis of previous games:

    Show the player the games in which they made the most mistakes, how they could have played better, and give advice to avoid those mistakes.

# 5. Summary of next steps: ML Pipeline & Application Goals

## 📊 Estado de Completitud por Fase del Roadmap

| Fase       | Componente                            | Estado        | Completitud         | Prioridad | Próximos Pasos                  |
| ---------- | ------------------------------------- | ------------- | ------------------- | --------- | ------------------------------- |
| **Fase 1** | Clasificación de errores (ML Clásico) | ✅ Completado  | 95%                 | 🔴 CRÍTICA | Consolidar en MLflow            |
|            | - Etiquetado táctico de features      | ✅             | 100% (328K records) | 🔴         | ✅ Completado                    |
|            | - Logistic Regression L2/L1           | ✅             | 100%                | 🔴         | ✅ F1=0.890                      |
|            | - RandomForest baseline               | ✅             | 90%                 | 🔴         | Consolidar en MLflow            |
|            | - Métricas F1 + Confusion Matrix      | ✅             | 90%                 | 🔴         | ✅ Resultados disponibles        |
| **Fase 2** | Deep Learning Tabular (MLP)           | 🔵 Pendiente   | 0%                  | 🔵         | Esperar resultados Fase 1       |
| **Fase 3** | Análisis Temporal (Errores en cadena) | 🔵 Pendiente   | 0%                  | 🟡         | Features temporales             |
| **Fase 4** | Embeddings y Similitud                | 🔵 Pendiente   | 0%                  | 🟢         | Clustering por ELO              |
| **Fase 5** | Tutor Adaptativo – AI Chess Coach     | 🟡 En Progreso | 45%                 | 🔴         | ExplainerService + API endpoint |
|            | - FeatureSummarizer                   | ✅             | 100%                | 🔴         | ✅ Completado                    |
|            | - RAG (ChromaDB + SentenceTransformers)| ✅            | 100%                | 🔴         | ✅ chess_rag.py + pdf_processor  |
|            | - Orchestrated Architecture (Fase 0)  | ✅             | 100%                | 🔴         | ✅ Docs completas (v0.1.103)     |
|            | - PlannerService                      | ✅             | 100%                | 🔴         | ✅ Completado (v0.1.108)         |
|            | - ExecutorService                     | ✅             | 100%                | 🔴         | ✅ Completado (v0.1.108)         |
|            | - MemoryService                       | ✅             | 100%                | 🔴         | ✅ Completado (v0.1.108)         |
|            | - CoachingLLM (ExplainerService)      | ⏳             | 0%                  | 🔴         | Integrar Ollama + LangChain     |
|            | - API endpoint /ai-coach/             | ❌ Pendiente   | 0%                  | 🔴         | FastAPI router                  |
|            | - Frontend React components           | ❌ Pendiente   | 0%                  | 🟡         | CoachingReport.tsx              |
| **Fase 6** | Human-in-the-Loop                     | 🔵 Planeado    | 0%                  | 🔵         | Futuro (B2B)                    |

### Leyenda de Estados:
- ✅ **Completado**: Implementado y validado
- 🟡 **En Progreso**: Parcialmente implementado
- 🏃 **Ejecutando**: En ejecución activa
- ❌ **Bloqueado**: Requiere acción inmediata
- 🔵 **Pendiente**: Planeado pero no iniciado

### Leyenda de Prioridades:
- 🔴 **CRÍTICA**: Bloquea objetivos principales
- 🟡 **ALTA**: Necesario para funcionalidad completa
- 🟢 **MEDIA**: Importante pero no bloqueante
- 🔵 **BAJA**: Mejoras futuras

---

## 🎯 Objetivos Concretos y Estado de Implementación

| Objetivo       | Descripción                            | Estado         | Completitud | Issue Relacionado  |
| -------------- | -------------------------------------- | -------------- | ----------- | ------------------ |
| **Objetivo 1** | Recomendaciones por partida individual | ⏳ En Diseño    | 10%         | #NEW-4 (Propuesto) |
|                | - Predicción error_label               | ✅ Implementado | 100%        | #78 (Completado)   |
|                | - API endpoint análisis                | ❌ Pendiente    | 0%          | #NEW-4             |
|                | - Sistema explicabilidad (SHAP)        | ❌ Pendiente    | 0%          | #23 (Existente)    |
| **Objetivo 2** | Predicción patrones comunes por nivel  | ⏳ Planeado     | 5%          | #NEW-5 (Propuesto) |
|                | - Dataset multi-nivel ELO              | ✅ Disponible   | 100%        | #21 (Completado)   |
|                | - Clustering por nivel                 | ❌ Pendiente    | 0%          | #NEW-5             |
|                | - Análisis patrones tácticos           | ❌ Pendiente    | 0%          | #NEW-5             |
| **Objetivo 3** | Reporte PDF personalizado              | ⏳ Planeado     | 0%          | #NEW-6 (Propuesto) |
|                | - Estadísticas agregadas               | ❌ Pendiente    | 0%          | #NEW-6             |
|                | - Análisis por fase/color              | ❌ Pendiente    | 0%          | #NEW-6             |
|                | - Generación PDF                       | ❌ Pendiente    | 0%          | #NEW-6             |
| **Objetivo 4** | Predicción estilo de juego             | 🔵 Futuro       | 0%          | Fase 4 (Planeado)  |

---

## 🚀 Plan de Sprints (Próximas 8-12 Semanas)

### Sprint 1 (Semanas 1-3): Foundation - Completar Fase 1
**Objetivo:** Establecer baseline ML sólido y reproducible

**Tareas Críticas:**
1. ✅ **Completar etiquetado masivo** (Issue #NEW-1)
   - ✅ 328,283 features etiquetados (100%)
   - Status: COMPLETADO
   
2. 🏃 **Establecer baseline Phase 1** (Issue #NEW-2)
   - ⏳ Ejecutando phase1_baseline.py ahora
   - ⏳ Registrando en MLflow
   - Target: F1 > 0.70 (actual: 0.890 ✅)
   
3. ✅ **Crear documento teórico ML** (Issue #NEW-3)
   - ✅ ML_THEORETICAL_FRAMEWORK.md completo
   - ✅ 10 algoritmos documentados
   - ✅ L1/L2 regularización explicada

4. ⏳ **Pipeline ML unificado** (Issue #NEW-7)
   - En diseño
   - Integración MLflow Pipelines

**Entregables:**
- ✅ Dataset 100% etiquetado (328K records)
- 🏃 Baseline ML en validación (F1: 0.890)
- ✅ Documento teórico completo
- ⏳ Pipeline ejecutable end-to-end

---

### Sprint 2 (Semanas 4-5): Advanced Analysis
**Objetivo:** Implementar análisis avanzado y recomendaciones

**Tareas:**
1. 🎯 **API de recomendaciones** (Issue #NEW-4)
   - Endpoint /api/v1/games/{id}/analyze
   - Sistema de recomendaciones básico

2. 📊 **Clustering por nivel ELO** (Issue #NEW-5)
   - K-Means por rango ELO
   - Identificación de patrones

3. 📄 **Reportes PDF** (Issue #NEW-6)
   - Generador de reportes
   - Templates con estadísticas

---

### Sprint 3 (Semanas 6-8): Temporal & Optimization
**Objetivo:** Análisis temporal y optimización de modelos

**Tareas:**
1. ⏰ **Features temporales** (Issue #NEW-8)
   - time_pressure, move_time
   - error_streak, prev_error_count

2. 🔄 **Validación cross-dataset** (Issue #NEW-9)
   - Train/test entre datasets
   - Métricas de generalización

3. 🧠 **Fase 3: Análisis temporal**
   - LSTM/GRU para secuencias
   - Detección de colapsos

---

## 📊 Infraestructura y Tecnologías (Estado Actual)

| Componente           | Tecnología                | Estado        | Versión | Notas              |
| -------------------- | ------------------------- | ------------- | ------- | ------------------ |
| **Frontend**         | React + TypeScript + Vite | ✅ Operativo   | 19.x    | -                  |
| **Backend**          | FastAPI + JWT Auth        | ✅ Operativo   | 0.100+  | -                  |
| **Database**         | PostgreSQL + Alembic      | ✅ Operativo   | 13+     | 11,676 partidas    |
| **ML Tracking**      | MLflow (file-based)       | ✅ Operativo   | 3.2.0   | Baseline F1=0.890  |
| **Data Pipeline**    | Python + Pandas           | ✅ Operativo   | -       | 328K features      |
| **Chess Engine**     | Stockfish 17 + NNUE       | ✅ Operativo   | 17      | Análisis táctico   |
| **Containerization** | Docker + Compose          | ✅ Operativo   | -       | PostgreSQL activo  |
| **ML Framework**     | scikit-learn              | ✅ Configurado | 1.7.1   | Phase 1 completado |
| **RAG System**       | ChromaDB + SentenceTransformers | ✅ Implementado | latest | chess_rag.py listo |
| **AI Orchestration** | Planner/Executor/Memory   | ✅ Implementado | v0.1.108 | Clean Architecture |
| **LLM Local**        | Ollama + LangChain        | ⏳ Pendiente   | -       | coaching_llm.py    |

---

## 🎯 Métricas de Éxito del Proyecto

### Corto Plazo (1 mes)
- ✅ Dataset 100% etiquetado (328,283 records)
- ✅ Baseline ML con F1 > 0.70 (actual: 0.890)
- ✅ Confusión grave < 5% (actual: 0.0%)
- ✅ Orchestrated Architecture implementada (Planner + Executor + Memory)
- ✅ RAG System operativo (ChromaDB + SentenceTransformers)

### Mediano Plazo (3 meses)
- ⏳ ExplainerService (LLM coaching via Ollama)
- ⏳ API endpoint /ai-coach/ en FastAPI
- ⏳ Generación de reportes PDF
- ⏳ Sistema de clustering operativo
- ⏳ Análisis temporal implementado

### Largo Plazo (6 meses)
- 🔵 Tutor adaptativo completo (frontend React integrado)
- 🔵 Embeddings para similitud entre partidas
- 🔵 Sistema de mejora continua
- 🔵 Human-in-the-loop básico

---

## 🔧 Comandos de Desarrollo Actualizados

### ML Pipeline Commands
```powershell
# Ejecutar baseline Phase 1
python src/scripts/execute_phase1_baseline.py

# Generar features con análisis táctico
python src/scripts/generate_features_with_tactics.py

# Verificar features en DB
python src/scripts/verify_features.py

# Generar análisis de datasets
python src/ml/analyze_real_datasets.py

# Ver resultados MLflow (local)
# Tracking: mlruns/
# Resultados: src/ml/results/
```

### Frontend Development:
```bash
cd src/frontend
npm run dev          # Start Vite development server
npm run build        # Build for production
npm run lint         # Run ESLint checks
```

### Backend Development:
```bash
cd src/api
python -m uvicorn main:app --reload  # Start FastAPI with hot reload
python -m pytest tests/              # Run API tests
# Documentación: http://localhost:8000/docs
```

### Database Management:
```bash
alembic upgrade head     # Apply database migrations
alembic revision --autogenerate -m "description"  # Create new migration
docker-compose up -d postgres  # Start PostgreSQL
```

---

## 📈 Visualización de Progreso

```
Fase 1: Clasificación ML       ███████████████████░ 95% (F1: 0.890 ✅)
Fase 2: Deep Learning          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  0%
Fase 3: Análisis Temporal      ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  0%
Fase 4: Embeddings             ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  0%
Fase 5: AI Chess Coach         █████████▓▓▓▓▓▓▓▓▓▓▓ 45% (Orchestration ✅, LLM ⏳)
  └─ FeatureSummarizer         ████████████████████ 100% ✅
  └─ RAG System                ████████████████████ 100% ✅
  └─ Planner/Executor/Memory   ████████████████████ 100% ✅
  └─ CoachingLLM (Explainer)   ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   0% ⏳
  └─ API /ai-coach/            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   0% ⏳
  └─ Frontend React            ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   0% ⏳
Fase 6: Human-in-Loop          ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  0%

Infraestructura                ████████████████████ 100%
Pipeline de Datos              ████████████████████ 100% (328K records)
Documentación                  █████████████████░░░  85%
Aplicación Final               ████████░░░░░░░░░░░░  40%

PROGRESO GENERAL:              ████████████░░░░░░░░  65%
```

---

## 📚 Documentación Técnica Detallada

### Documentos Principales (✅ Existentes)
- [ROADMAP_TECHNICAL.md](./docs/ROADMAP_TECHNICAL.md) - Roadmap de 6 fases ML
- [ML_THEORETICAL_FRAMEWORK.md](./docs/ML_THEORETICAL_FRAMEWORK.md) - ✅ Marco teórico completo (10 algoritmos)
- [ML_PROJECT_STATE_ANALYSIS.md](./docs/ML_PROJECT_STATE_ANALYSIS.md) - ✅ Análisis detallado 80+ páginas
- [MLFLOW_COMPLETE_GUIDE.md](./notebooks/docs/MLFLOW_COMPLETE_GUIDE.md) - Guía completa MLflow
- [ELO_STANDARDIZATION_GUIDE.md](./docs/ELO_STANDARDIZATION_GUIDE.md) - Sistema ELO unificado
- [PHASE1_BASELINE_EXECUTION.md](./docs/PHASE1_BASELINE_EXECUTION.md) - ✅ Ejecución baseline activa

### Issues GitHub

#### Completados (✅)
- #74: Data Collection ✅ 100%
- #75: Feature Engineering ✅ 95%
- #76: Parquet Datasets ✅ 90%
- #78: ML Pipeline + MLflow ✅ 100%
- #21: ELO Standardization ✅ 100%

#### En Progreso (🟡)
- #77: UI Architecture Refactor 🟡 40%
- #86: Arquitectura Orquestada Fase 1 ✅ Completado (v0.1.108)
- #87: CriticService ⏳ Pendiente
- #88: ExplainerService (LLM) ⏳ Pendiente

#### Propuestos (Ver [PROPOSED_ML_ISSUES.md](./docs/PROPOSED_ML_ISSUES.md))
- #NEW-1: ✅ Completado (328K records)
- #NEW-2: ✅ Completado (F1: 0.890)
- #NEW-3: ✅ Completado (doc teórico)
- #NEW-4 a #NEW-10: Pendientes

---

**Última actualización:** 25 de Mayo de 2026  
**Versión:** v0.1.138-fda75dc  
**Estado ML:** ✅ Phase 1 completado (F1=0.890) | 🟡 AI Coach – Orchestration ✅, LLM ⏳  
**Análisis completo:** [ML_PROJECT_STATE_ANALYSIS.md](./docs/ML_PROJECT_STATE_ANALYSIS.md)

## 📊 Real Datasets Analysis

The project includes comprehensive analysis tools for comparing ML model performance across different chess dataset types:

### Available Datasets:
- **Elite**: High-level players (Elo 2500+) with rich error labels
- **FIDE**: Official FIDE tournament games  
- **Novice**: Beginner players (Elo ~1200)
- **Personal**: Personal games (Chess.com/Lichess) - Most realistic error distribution
- **Stockfish**: Engine analysis data

### 🎯 ELO Standardization System
**Status: ✅ COMPLETED (Issue #21)**

The project now includes a comprehensive ELO standardization system that:
- **Cross-Platform Conversion**: Standardizes ratings from Chess.com, Lichess, and FIDE
- **Anomaly Detection**: Intelligently detects and corrects problematic ratings (e.g., 655.0 → 800)
- **Quality Metrics**: Provides detailed statistics on data quality (73.3% quality score achieved)
- **Production Ready**: 50% success rate on anomaly corrections with comprehensive logging

**Key Features:**
- Resolves runtime warnings like "Rating 655.0 outside valid range [800, 3500]"
- Handles data entry errors (missing digits, wrong scale, extreme values)
- Comprehensive test suite with 11 validation scenarios
- Real-time quality reporting and metrics

### Quick Analysis:
```powershell
# Load helpers and run analysis
. .\quick-helpers.ps1
Analyze-RealDatasets
```

### Key Findings:
- **Personal dataset** shows most realistic error distribution (good: 1,482, mistake: 726, inaccuracy: 630, blunder: 296)
- **Elite dataset** has concentrated error samples but fewer overall errors
- All datasets show high ML accuracy (1.000) indicating clean, well-structured data
- 10,000+ samples per dataset type with 34 chess-specific features each

## 📚 Technical Documentation

### Core ML Framework Documents:
- **[ML Theoretical Framework](./docs/ML_THEORETICAL_FRAMEWORK.md)** - Conceptos teóricos de algoritmos ML aplicados a chess_trainer
- **[ML Current State Analysis](./docs/ML_CURRENT_STATE_ANALYSIS.md)** - Análisis detallado del estado actual vs objetivos ML
- **[MLflow PostgreSQL Integration](./docs/MLFLOW_POSTGRES_INTEGRATION.md)** - Configuración MLflow con PostgreSQL para tracking
- **[Reliable Chess Predictions](./docs/PREDICCIONES_FIABLES_MLFLOW.md)** - Pipeline completo ML para predicciones fiables

### Current ML Implementation Status:
- **Issue #66**: ✅ Chess data preprocessing completed
- **Issue #67**: ✅ ML model training completed (superseded by #78)
- **Issue #68**: ✅ Model evaluation and optimization completed (superseded by #78)
- **Issue #74**: ✅ PGN capture and ZIP processing completed
- **Issue #75**: ✅ Stockfish features extraction completed
- **Issue #76**: ✅ Parquet datasets generation completed  
- **Issue #78**: ✅ ML Pipeline with MLflow tracking completed
- **Issue #21**: ✅ ELO standardization system completed (100% complete) - Resolves rating anomalies like 655.0 warnings
- **Issue #23**: ⏳ SHAP explainability integration pending

## 💻 Modern Development Stack

### 🎨 Frontend (React + Vite)
- **⚛️ React 19**: Latest React with concurrent features
- **🚀 Vite**: Lightning-fast build tool and dev server  
- **📘 TypeScript**: Type safety and better developer experience
- **🎁 Material-UI**: Professional, accessible component library
- **🔄 React Query**: Powerful server state management
- **♟️ Chess.js**: Robust chess game logic library
- **🏁 React Router**: Declarative client-side routing

### ⚡ Backend (FastAPI)  
- **🐍 FastAPI**: Modern, high-performance web framework
- **🔐 JWT Authentication**: Secure token-based auth
- **🗄️ PostgreSQL**: Enterprise-grade relational database
- **🔄 Alembic**: Database migration management
- **📊 MLflow**: ML experiment tracking and model registry
- **🐳 Docker**: Containerized development environment

### 🧠 Data Science & ML
- **🔬 Jupyter Notebooks**: Interactive data analysis
- **🤖 Stockfish**: World-class chess engine integration
- **📈 scikit-learn**: Machine learning algorithms
- **🐼 pandas**: Data manipulation and analysis
- **📊 numpy**: Numerical computing foundation

## 🏆 Credits

**Chess Trainer** - Modern chess analysis platform combining React + FastAPI with advanced ML capabilities.

Developed by **cmessoftware** as part of their practical work for the Data Science Diploma.

### 🤝 Contributing
This project welcomes contributions! Please check our documentation for development setup and contribution guidelines.

### 📄 License
This project is developed for educational and research purposes.

---

**Last Updated**: May 2026 - Version v0.1.138-fda75dc  
**Tech Stack**: React 19 + TypeScript + Vite + FastAPI + PostgreSQL + MLflow + Docker + ChromaDB + Ollama
