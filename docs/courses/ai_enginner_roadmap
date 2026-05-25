Especificación completa para Copilot
Curso AI Engineering basado en ChessTrainer

--- v1 Status ---
Notebooks disponibles en docs/courses/ (junto a este archivo):
  01_architecture_overview.ipynb   — Módulo 0: Foundations  ✅
  02_run_feature_pipeline.ipynb    — Módulo 1: Data Pipeline  ✅
  03_dataset_builder.ipynb         — Módulo 2: Dataset Generation  ✅
Módulos 3-12: pendientes de implementación futura.
-----------------


El curso debe reutilizar la infraestructura existente del proyecto.
No debe reimplementar el pipeline de extracción de features.
Arquitectura del sistema
Pipeline base
Plain text
PGN (.pgn / .pgn.gz)
      ↓
feature extraction script (existente)
      ↓
features table (database)
      ↓
dataset builder
      ↓
ML prediction
      ↓
pattern detection
      ↓
RAG retrieval
      ↓
LLM explanation
      ↓
report
Los PGN pueden estar comprimidos.
Ubicación:

data/games/
Tipos de datasets:

novice/
personal/
fide/
elite/
engine/
Script existente
Existe un script que:

detecta archivos pgn.gz
los descomprime
parsea partidas
ejecuta análisis
genera features
guarda features en base
Copilot debe reutilizarlo.
Ejemplo esperado:
Python
subprocess.run(["python", "scripts/generate_features.py"])
No crear un parser nuevo.
Base de datos
Tabla principal:

features
Columnas esperadas:

game_id
move_number
fen
elo
opening
material_total
num_pieces
king_safety
center_control
has_castling_rights
is_pawn_endgame
score_cp
mate_in
depth_score_diff
error_label
tags
Copilot debe generar:

data_access/features_repository.py
Dataset builder
Pipeline:

features table
      ↓
dataset cleaning
      ↓
feature encoding
      ↓
training dataset
Archivo:

dataset/build_training_dataset.py
Target:

error_label
Clases:

good
inaccuracy
mistake
blunder
Estructura del curso
Copilot debe generar:

ai_engineer_course/
módulos:

00_foundations
01_data_pipeline
02_dataset_generation
03_feature_analysis
04_machine_learning
05_model_evaluation
06_llm_explanations
07_rag_system
08_ai_agents_phase1
09_ai_system_architecture
10_production_ai
11_capstone
12_phase2_agentic_system
Módulo 0 — Foundations
Objetivo:
comprender pipeline completo.
Notebook:

01_architecture_overview.ipynb  [v1 — disponible en docs/courses/]
Módulo 1 — Data pipeline
No implementar parsing.
Notebook:

02_run_feature_pipeline.ipynb  [v1 — disponible en docs/courses/]
Ejecuta script existente.
Módulo 2 — Dataset generation
Notebook:

03_dataset_builder.ipynb  [v1 — disponible en docs/courses/]
Lee tabla features.
Módulo 3 — Feature analysis
Notebook:

feature_analysis.ipynb
Análisis:

error distribution
error by elo
error by opening
centipawn loss
Módulo 4 — Machine Learning
Modelos:

RandomForest
LightGBM
XGBoost
CatBoost
Scripts:

ml/train_random_forest.py
ml/train_lightgbm.py
ml/train_xgboost.py
ml/train_catboost.py
Módulo 5 — Model explainability
Métodos:

SHAP
feature importance
Notebook:

shap_analysis.ipynb
Módulo 6 — LLM explanation
Pipeline:

ML prediction
↓
pattern detection
↓
RAG retrieval
↓
LLM explanation
Stack:

LangChain
Ollama
llama3.2:3b
Archivos:

llm/prompt_templates.py
llm/llm_explainer.py
Módulo 7 — RAG
Fuentes:

chess books
annotated games
stored explanations
Pipeline:

text chunking
embedding
vector database
retrieval
Herramientas:

ChromaDB
LangChain
Módulo 8 — AI Agents (fase 1)
Agente simple.
Herramientas:

stockfish_tool
dataset_lookup_tool
pattern_detection_tool
Uso:
resolver análisis de posición.
Módulo 9 — System architecture
Arquitectura:

Streamlit
↓
FastAPI
↓
ML services
↓
database
Módulo 10 — Production AI
Endpoints:

/analyze_game
/predict_move_quality
/explain_position
Capstone
Sistema final:

AI chess coach
Funciones:

upload PGN
run feature pipeline
predict errors
generate explanations
generate training advice
FASE 2 — Arquitectura agentic avanzada
Esta fase introduce arquitectura con:

Planner
Executor
Critic
Memory
Arquitectura fase 2

analysis_request
      ↓
planner
      ↓
executor
      ↓
critic
      ↓
memory
      ↓
final explanation
Componentes
Planner
Decide qué pasos ejecutar.
Ejemplo:

analyze_position
detect_patterns
retrieve_context
generate_explanation
Archivo:

agents/planner.py
Executor
Ejecuta herramientas.
Herramientas disponibles:

stockfish_tool
feature_lookup_tool
dataset_search_tool
rag_retriever
Archivo:

agents/executor.py
Critic
Verifica consistencia.
Debe detectar:

contradicciones con Stockfish
explicaciones incorrectas
errores conceptuales
Archivo:

agents/critic.py
Memory
Almacena:

historial de análisis
patrones detectados
errores frecuentes del jugador
Permite personalización.
Archivo:

agents/memory.py
Flujo completo fase 2

position
↓
planner
↓
executor
↓
pattern detection
↓
RAG retrieval
↓
LLM explanation
↓
critic validation
↓
memory update
↓
final report
Objetivo fase 2
Transformar el sistema en un AI chess coach adaptativo.
Capacidades:

aprende de errores del jugador
adapta recomendaciones
mejora explicaciones
Resultado esperado
Copilot debe generar aproximadamente:

30 notebooks
40 scripts
ML pipeline completo
RAG pipeline
LLM explanation system
agentic architecture
production API
Todo construido sobre el sistema real de ChessTrainer.
