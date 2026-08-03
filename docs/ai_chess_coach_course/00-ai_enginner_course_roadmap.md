# AI Engineering Course — ChessTrainer Roadmap

> **Ubicación del curso:** `docs/ai_chess_coach_course/`  
> **Hito actual del curso:** Módulos **0–6.6** (pipeline de datos → ML → SHAP → coaching LLM → validación humana y redefinición del producto)  
> **Módulos 7+:** planificados y condicionados por evidencia (RAG, LLM local, agentes, MVP UI)

---

## Resumen de módulos (0 → 6.6)

| Módulo                                   | Notebook                                    | Qué hace el alumno                                                                                                                                                                            | Artefactos / código clave                                              | Estado   |
| ---------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- | -------- |
| **0** Foundations                        | `00_architecture_overview.ipynb`            | Recorre el pipeline completo del proyecto real (PGN → features → ML → explicación)                                                                                                            | Visión de arquitectura                                                 | ✅        |
| **1** Data pipeline                      | `01_run_feature_pipeline.ipynb`             | Ejecuta el **script existente** de extracción de features; no reimplementa el parser PGN                                                                                                      | `CourseFeaturesRepository`, SQLite/Postgres `features`                 | ✅        |
| **2** Dataset                            | `02_dataset_builder.ipynb`                  | Limpia, codifica y exporta parquet de entrenamiento desde `features`                                                                                                                          | `dataset/build_training_dataset.py`, `course_training_dataset.parquet` | ✅        |
| **3** Feature analysis                   | `03_feature_analysis.ipynb`                 | Explora distribución de errores, ELO, aperturas, pérdida de centipeones                                                                                                                       | Análisis exploratorio sobre parquet/DB                                 | ✅        |
| **4** Machine learning                   | `04_ml_training.ipynb`                      | Entrena clasificador **Human Pattern** (multiclass `error_label`); compara familias de modelos                                                                                                | `artifacts/module04/`, modelo base para SHAP                           | ✅        |
| **5** MLflow                             | `05_mlflow_experiment_tracking.ipynb`       | Registra params, métricas y artefactos; compara runs y elige mejor modelo                                                                                                                     | `experiment_tracking/`, `artifacts/module05/`                          | ✅        |
| **6** SHAP                               | `06_shap_analysis.ipynb`                    | Explica predicciones por jugada con SHAP; define columnas “human” vs motor                                                                                                                    | `artifacts/module06/human_model.joblib`, explainability                | ✅        |
| **6.5** LLM coaching                     | `06_5_llm_coaching_recommendations.ipynb`   | Convierte SHAP + patrones + **diagnóstico estructurado** en informe de coaching V7 (español); LLM opcional                                                                                    | `coaching/`, `llm/`, `artifacts/module06_5/`                           | ✅        |
| **6.6** Product reset + human validation | `06_6_product_reset_human_validation.ipynb` | Audita la utilidad real del coaching V7, separa evidencia de narrativa, define protocolo de validación con entrenador y replantea el MVP hacia diagnóstico longitudinal y análisis de rivales | `evaluation/`, `validation/`, `artifacts/module06_6/`                  | 🟡 Diseño |

**Arco pedagógico 0–6.6:** de “datos reales del ChessTrainer” a recomendaciones de coaching fundamentadas y, luego, a una **evaluación explícita de su utilidad ajedrecística**. El LLM **narra**; Python **diagnostica**; un protocolo humano determina si la recomendación es pedagógicamente válida.

```text
[0] Arquitectura
      ↓
[1] features (script existente → DB)
      ↓
[2] parquet + encoding + splits por game_id
      ↓
[3] EDA errores / ELO / aperturas
      ↓
[4] Human Pattern model (multiclass)
      ↓
[5] MLflow — mejor run reproducible
      ↓
[6] SHAP por jugada
      ↓
[6.5] RCA + DiagnosisBuilder + V7 → informe coaching (DeepSeek/Gemini opcional)
      ↓
[6.6] Auditoría de fiabilidad + validación humana + redefinición del MVP
```

**Referencias 6.5:** [Spec](./06_5-ai_chess_coach_course_llm_coaching_recommendations.md) · [Arquitectura](./6.5_llm_integration_architecture.md) · [Formato V7](./accc_llm_coaching_recommendations_v7.md) · [`.env.example`](./.env.example)

---

## Phase 00 - AI Engineering Course Based on ChessTrainer

**Notebooks disponibles** (todos en `docs/ai_chess_coach_course/`):

| Notebook                                  | Módulo                   |
| ----------------------------------------- | ------------------------ |
| `00_architecture_overview.ipynb`          | 0 — Foundations ✅        |
| `01_run_feature_pipeline.ipynb`           | 1 — Data Pipeline ✅      |
| `02_dataset_builder.ipynb`                | 2 — Dataset Generation ✅ |
| `03_feature_analysis.ipynb`               | 3 — Feature Analysis ✅   |
| `04_ml_training.ipynb`                    | 4 — Machine Learning ✅   |
| `05_mlflow_experiment_tracking.ipynb`     | 5 — MLflow ✅             |
| `06_shap_analysis.ipynb`                  | 6 — SHAP ✅               |
| `06_5_llm_coaching_recommendations.ipynb` | 6.5 — LLM Coaching ✅     |

Módulos **7–13:** pendientes (ver más abajo).
It must not reimplement the feature extraction pipeline.

## System Architecture
### Base Pipeline
Plain text

PGN (.pgn / .pgn.gz)
      ↓
feature extraction script (existing)
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

PGN files can be compressed.
Location:

data/games/
Dataset Types:

      novice/
      personal/
      fide/
      elite/
      engine/

Existing Script
There is a script that:

      detects pgn.gz files
      decompresses them
      parses games
      executes analysis
      generates features
      saves features to database
      Copilot must reuse it.
Expected Example:
Python
subprocess.run(["python", "scripts/generate_features.py"])
Do not create a new parser.
Database
Main Table:

features
Expected Columns:

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
Copilot Must Generate:

data_access/features_repository.py
Dataset Builder
Pipeline:

features table
      ↓
dataset cleaning
      ↓
feature encoding
      ↓
training dataset
File:

dataset/build_training_dataset.py
Target:

error_label
Classes:

good
inaccuracy
mistake
blunder
## Course Structure
Copilot Must Generate:

### ai_engineer_course/
modules:

### Phase 1: Foundations + notebooks + helper scripts (NO UI, NO agentic orchestration)

Scope constraints for Phase 1:
- Use notebooks and helper scripts only.
- Do not implement UI.
- Do not implement planner -> executor -> critic -> memory in this phase.
- Show baseline LLM limitations in tests (inconsistencies and hallucinations) as part of learning goals.

- 00_foundations
- 01_data_pipeline
- 02_dataset_generation
- 03_feature_analysis
- 04_machine_learning
- 05_mlflow_experiment_tracking
- 06_shap_model_evaluation
- **06_5_llm_coaching** ✅ (hito técnico: generación de recomendaciones V7)
- **06_6_product_reset_human_validation** 🟡 (punto de quiebre: medir utilidad, fiabilidad y valor pedagógico antes de agregar complejidad)
- 07_rag_system
- 08_llm_explanations
- 09_llm_consistency_and_hallucination_tests

### Phase 2: Agentic architecture (planner -> executor -> critic -> memory)

- 10_phase2_agentic_architecture
- 11_capstone — [proyecto integrador](#capstone); ver Módulo 11

### Phase 3: MVP delivery (basic UI + FastAPI) and production bridge

- 12_mvp_ui_fastapi
- 13_react_vite_production_bridge

## Glosario

### Capstone

**Capstone** (inglés *capstone*: “piedra de remate” / culminación) es el **proyecto integrador final** de un programa formativo. No introduce un tema nuevo desde cero: **reúne** lo ya aprendido en una entrega única, evaluable y cercana a un caso real.

| Aspecto                             | Qué significa                                                                                                 |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Propósito**                       | Demostrar competencia **sistémica** (varias piezas funcionando juntas), no solo dominio de un módulo aislado. |
| **Entrada**                         | Componentes, notebooks y servicios construidos en módulos previos.                                            |
| **Salida**                          | Demo **end-to-end** + evidencia (métricas, informe, referencias MLflow, tests).                               |
| **Diferencia vs. un módulo normal** | Menos teoría nueva; más **ensamblaje, prueba y documentación** del flujo completo.                            |
| **Diferencia vs. MVP (módulo 12)**  | El capstone puede ser **solo backend** (script/notebook/API interna); el MVP añade interfaz para usuarios.    |

**En este curso:** el capstone es el **Módulo 11** (Phase 2 — *Agentic Backend Integration*). Integra Phase 1 (datos → ML → SHAP → coaching 6.5 → validación 6.6) con RAG, LLM, tests de alucinación y arquitectura agentic (módulos 7–10). Detalle en [Module 11 — Capstone](#module-11--capstone-agentic-backend-integration).

---

## Phase 1

### Module 0 — Foundations

**Objetivo:** Entender el pipeline end-to-end del ChessTrainer real antes de tocar ML o LLM.

|            |                                                                                    |
| ---------- | ---------------------------------------------------------------------------------- |
| Notebook   | `00_architecture_overview.ipynb`                                                   |
| Entregable | Mapa mental: PGN → features → dataset → modelo → explicabilidad → (futuro) RAG/LLM |

---

### Module 1 — Data Pipeline

**Objetivo:** Poblar la tabla `features` reutilizando el pipeline existente (**no** escribir un parser PGN nuevo).

|          |                                                                      |
| -------- | -------------------------------------------------------------------- |
| Notebook | `01_run_feature_pipeline.ipynb`                                      |
| Código   | `data_access/features_repository.py`                                 |
| Datos    | `course_data.sqlite` (curso) o DB del proyecto; PGN en `data/games/` |

---

### Module 2 — Dataset Generation

**Objetivo:** Pasar de filas por jugada en SQL a un parquet listo para entrenamiento.

|          |                                                            |
| -------- | ---------------------------------------------------------- |
| Notebook | `02_dataset_builder.ipynb`                                 |
| Spec     | `02-ai_chess_coach_leakage_detection.md` (fugas train/val) |
| Script   | `dataset/build_training_dataset.py`                        |
| Target   | `error_label` → `good`, `inaccuracy`, `mistake`, `blunder` |
| Salida   | `data/datasets/course_training_dataset.parquet`            |

---

### Module 3 — Feature Analysis

**Objetivo:** Conocer el dataset antes de modelar (sesgos, aperturas, ELO, distribución de errores).

|          |                                                                          |
| -------- | ------------------------------------------------------------------------ |
| Notebook | `03_feature_analysis.ipynb`                                              |
| Spec     | `03-ai_chess_coach_course_shap_human_pattern.md` (puente hacia módulo 6) |
| Análisis | Distribución de clases, errores por ELO/apertura, pérdida de centipeones |

---

### Module 4 — Machine Learning

**Objetivo:** Entrenar el modelo **Human Pattern** que usarán SHAP y coaching (clasificación multiclass por jugada).

|          |                                                                                                           |
| -------- | --------------------------------------------------------------------------------------------------------- |
| Notebook | `04_ml_training.ipynb`                                                                                    |
| Spec     | `04-ai_chess_coach_course_llm_recommendationsf_from_shap_+_pattern_engine.md` (catálogo ampliado, futuro) |
| Modelos  | LogisticRegression, KNN, SVM, RandomForest, LightGBM, XGBoost, CatBoost                                   |
| Split    | Por `game_id` (evitar leakage jugada a jugada de la misma partida)                                        |

---

### Module 5 — MLflow Experiment Tracking

**Objetivo:** Comparar experimentos de forma reproducible y fijar el mejor run para módulos 6 y 6.5.

|               |                                                                         |
| ------------- | ----------------------------------------------------------------------- |
| Notebook      | `05_mlflow_experiment_tracking.ipynb`                                   |
| Spec          | `05-ai_chess_coach_course_mlflow_experiment_tracking.md`                |
| Paquete       | `experiment_tracking/course_mlflow.py`, `training_runner.py`            |
| Backend local | SQLite MLflow; logs de params, métricas, matrices de confusión, modelos |

---

### Module 6 — Model Explainability (SHAP)

**Objetivo:** Obtener evidencia **por jugada** (qué features empujan la predicción) sin enviar SHAP crudo al LLM.

|            |                                                                       |
| ---------- | --------------------------------------------------------------------- |
| Notebook   | `06_shap_analysis.ipynb`                                              |
| Método     | SHAP sobre el Human Pattern model                                     |
| Artefactos | `artifacts/module06/human_model.joblib`, columnas de features humanas |
| Uso en 6.5 | `explain_player_games()` alimenta Pattern Engine + filas para RCA     |

---

### Module 6.5 — LLM Coaching Recommendations (hito del curso v1)

**Objetivo:** Primera versión **end-to-end de coaching**: una partida (Phase A) o muestra de perfil (Phase B) → informe en español estilo entrenador humano (V7), con LLM opcional.

|                 |                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------- |
| Notebook        | `06_5_llm_coaching_recommendations.ipynb`                                                   |
| Spec            | `06_5-ai_chess_coach_course_llm_coaching_recommendations.md`                                |
| Arquitectura    | `6.5_llm_integration_architecture.md`                                                       |
| Formato informe | `accc_llm_coaching_recommendations_v7.md` (4 secciones: resumen, lecciones, momentos, plan) |

**Phase A — una partida**

1. Elige `game_id` (`prepare_player_game_analysis`, split validación, jugador `cmess1315` por defecto).
2. SHAP + Pattern Engine v1 en todas las jugadas del alumno.
3. **RCA:** agrupa síntomas bajo jugadas raíz (`root_cause.py`).
4. **DiagnosisBuilder (V4–V6):** tags SQLite + detectores de tablero + `diagnosis_type` + estilos de texto.
5. **V7:** `lesson_synthesizer` → 2–3 lecciones; prompt con reglas estrictas.
6. **LLM opcional:** DeepSeek (`deepseek-chat`, default) o Gemini; CI usa dry-run.
7. Validación post-LLM; fallback determinista si falla.

**Phase B — perfil (varias partidas):** `context_builder` + prompt de perfil (formato pre-V7; mejora futura).

**Paquetes**

- `llm/` — `LLMProvider`, DeepSeek (OpenAI-compatible), Gemini, cuota/fallback  
- `coaching/` — pipeline, RCA, diagnosis, prompt, `coaching_generate`, validación V7  

**Política de invocación:** pytest **nunca** llama API de pago; notebook genera prompts por defecto; celda opcional `invoke_llm=True`.

**Fuera de alcance 6.5:** ChromaDB/RAG (7), Ollama en paquete curso (8), corrección masiva de tags tácticos en DB (mejora upstream documentada).

Al completar **0–6.5**, el alumno tiene un arco técnico de coaching completo sin vector stores ni UI. El módulo **6.6** determina si ese arco produce recomendaciones confiables y si existe evidencia suficiente para continuar.


### Module 6.6 — Product Reset, Reliability Audit and Human Validation

**Objetivo:** detener la expansión técnica del sistema y comprobar si las recomendaciones generadas hasta 6.5 son correctas, relevantes, priorizadas y útiles para mejorar el juego.

Este módulo no descarta lo construido. Reutiliza:

- features por jugada;
- modelo Human Pattern;
- MLflow;
- SHAP;
- Pattern Engine;
- RCA;
- DiagnosisBuilder;
- formato V7;
- proveedores LLM y fallback determinista.

El cambio consiste en pasar de:

```text
generar una explicación convincente
```

a:

```text
demostrar que la recomendación es útil y defendible
```

|             |                                                                                               |
| ----------- | --------------------------------------------------------------------------------------------- |
| Notebook    | `06_6_product_reset_human_validation.ipynb`                                                   |
| Estado      | 🟡 Diseño / siguiente módulo                                                                   |
| Entrada     | Diagnóstico estructurado + informe V7 + posiciones críticas                                   |
| Validadores | Reglas automáticas + entrenador humano                                                        |
| Salida      | Dataset de evaluación, métricas de fiabilidad, decisiones de producto y nuevo alcance del MVP |

#### 6.6.1 — Hipótesis a validar

1. El sistema identifica correctamente la causa raíz del error.
2. La recomendación se apoya en evidencia observable.
3. El tema elegido es más importante que explicaciones alternativas.
4. La recomendación es adecuada para el nivel del jugador.
5. El plan de entrenamiento propuesto es accionable.
6. La redacción del LLM no introduce afirmaciones nuevas no sustentadas.
7. El informe aporta más valor que una simple variante de Stockfish.

#### 6.6.2 — Separación estricta de responsabilidades

```text
Stockfish / features / SHAP / reglas
            ↓
evidencia estructurada verificable
            ↓
motor de diagnóstico
            ↓
recomendación candidata
            ↓
LLM
            ↓
redacción, síntesis y adaptación del lenguaje
```

El LLM no debe decidir libremente:

- cuál fue la causa raíz;
- qué patrón ocurrió;
- cuál es la prioridad pedagógica;
- qué tema estudiar;
- qué plan recomendar.

Esas decisiones deben provenir de datos, reglas, modelos o validación humana. El LLM puede resumir, explicar y adaptar el nivel de lenguaje.

#### 6.6.3 — Dataset de validación humana

Construir un conjunto inicial de 50–100 casos representativos.

Cada caso debe incluir:

```json
{
  "case_id": "game_123_move_27",
  "player_elo": 1600,
  "fen_before": "...",
  "played_move": "Nxe5",
  "engine_best_move": "Bxh7+",
  "engine_evaluation_before": 0.4,
  "engine_evaluation_after": -1.8,
  "diagnosis_type": "tactical_oversight",
  "root_cause": "defender_removed",
  "recommended_topic": "loose_pieces_and_defenders",
  "system_explanation": "...",
  "system_training_action": "...",
  "coach_review": {}
}
```

El entrenador completa:

```json
{
  "correctness": 1,
  "relevance": 2,
  "priority": 1,
  "level_fit": 2,
  "actionability": 2,
  "preferred_diagnosis": "calculation_failure",
  "preferred_training_action": "resolver ejercicios de eliminación del defensor",
  "comments": "La explicación es correcta, pero el problema principal fue cortar el cálculo una jugada antes."
}
```

Escala sugerida:

- `0`: incorrecto o perjudicial;
- `1`: parcialmente correcto;
- `2`: correcto y útil.

#### 6.6.4 — Métricas del módulo

No usar únicamente métricas de lenguaje.

Medir:

| Dimensión                | Métrica                                              |
| ------------------------ | ---------------------------------------------------- |
| Corrección ajedrecística | acuerdo con entrenador                               |
| Causa raíz               | accuracy / macro-F1 sobre categorías validadas       |
| Relevancia               | promedio de evaluación humana                        |
| Priorización             | top-1 y top-3 agreement                              |
| Adecuación al nivel      | promedio de evaluación humana                        |
| Accionabilidad           | porcentaje de recomendaciones aplicables             |
| Grounding                | porcentaje de afirmaciones respaldadas por evidencia |
| Consistencia             | variación entre múltiples generaciones               |
| Valor incremental        | comparación contra informe sin LLM                   |

#### 6.6.5 — Experimentos mínimos

Comparar cuatro variantes:

```text
A. Stockfish + variante
B. Diagnóstico determinista sin LLM
C. Diagnóstico + LLM
D. Diagnóstico + LLM + revisión humana
```

Preguntas de evaluación:

- ¿El LLM mejora comprensión o solo agrega texto?
- ¿El diagnóstico determinista ya es suficiente?
- ¿Qué tipos de recomendación requieren entrenador?
- ¿En qué categorías el sistema es confiable?
- ¿Cuándo debe abstenerse de recomendar?

#### 6.6.6 — Política de abstención

El sistema debe poder responder:

```text
No hay evidencia suficiente para emitir una recomendación confiable.
```

Casos de abstención:

- motores en fuerte desacuerdo;
- diagnóstico ambiguo;
- baja confianza del modelo;
- ausencia de patrón repetido;
- recomendación no validada para ese nivel;
- evidencia insuficiente en la muestra del jugador.

#### 6.6.7 — Nuevo enfoque del MVP

El MVP deja de intentar ser un analizador general de partidas.

Se orienta a dos casos de uso verificables:

##### A. Diagnóstico longitudinal del jugador

Entrada:

```text
100–1000 partidas propias
```

Salida:

- errores recurrentes;
- distribución por fase;
- evolución temporal;
- aperturas problemáticas;
- patrones tácticos y estratégicos;
- temas prioritarios;
- plan de estudio basado en evidencia.

##### B. Preparación de rivales

Entrada:

```text
colección PGN de un rival
```

Salida:

- repertorio con blancas y negras;
- variantes frecuentes;
- resultados por apertura;
- errores recurrentes;
- comportamiento por fase;
- tendencias tácticas y estratégicas;
- posiciones donde pierde precisión;
- informe de preparación con nivel de confianza.

Las recomendaciones específicas de match-up deben distinguir claramente:

```text
hecho observado
inferencia estadística
recomendación estratégica
opinión del entrenador
```

#### 6.6.8 — Arquitectura revisada

```text
PGN
  ↓
SQLite
  ↓
feature extraction existente
  ↓
ML + SHAP + Pattern Engine
  ↓
agregación longitudinal por jugador
  ↓
diagnóstico estructurado
  ↓
reglas de confianza y abstención
  ↓
validación humana
  ↓
LLM como capa de explicación
  ↓
informe de jugador o rival
```

#### 6.6.9 — Entregables

- `06_6_product_reset_human_validation.ipynb`
- `evaluation/coach_review_schema.py`
- `evaluation/reliability_metrics.py`
- `validation/human_review_template.csv`
- `validation/validated_cases.sqlite`
- `validation/annotation_guidelines.md`
- `artifacts/module06_6/reliability_report.md`
- `artifacts/module06_6/product_reset_decision.md`
- conjunto inicial de casos revisados por entrenador;
- decisión explícita de continuar, limitar o descartar cada tipo de recomendación.

#### 6.6.10 — Criterio de salida

No avanzar a RAG, agentes o UI hasta cumplir:

- corrección promedio aceptable según entrenador;
- tasa baja de recomendaciones perjudiciales;
- política de abstención implementada;
- separación verificable entre evidencia y narrativa;
- al menos un caso de uso que aporte valor sin depender de texto persuasivo;
- alcance del MVP aprobado sobre evidencia.

#### 6.6.11 — Decisión pedagógica

Este módulo convierte el cuello de botella en contenido central del curso:

- evaluación de sistemas generativos;
- human-in-the-loop;
- diseño de ground truth;
- incertidumbre;
- abstención;
- trazabilidad;
- diferencia entre exactitud técnica y utilidad de producto;
- redefinición de un MVP a partir de evidencia.

---

### Module 7 — RAG
Notebook:
07_rag_analysis.ipynb

Sources:

chess books
annotated games
stored explanations
Pipeline:

text chunking
embedding
vector database
retrieval
Tools:

ChromaDB
LangChain

### Module 8 — LLM Explanation (extends Module 6.5)

Notebook:
08_llm_explanation.ipynb

Builds on Module 6.5 provider abstraction and context contract; adds RAG retrieval (Module 07) and optional local runtime.

Pipeline:

ML prediction
↓
pattern detection (extended catalog)
↓
RAG retrieval
↓
LLM explanation (Gemini and/or local)
Stack:

LangChain
Ollama
llama3.2:3b
Files:

llm/prompt_templates.py
llm/llm_explainer.py

### Module 9 — LLM Consistency and Hallucination Tests
Objective:
make LLM limitations explicit before agentic safeguards are introduced.

Deliverables:

- test suite with inconsistent/hallucinated response examples
- baseline guardrails and evaluation checks
- report documenting failure patterns and mitigations to be addressed in Phase 2

## Phase 2

### Module 10 — Advanced Agentic Architecture
This phase introduces architecture with:

Planner
Executor
Critic
Memory

Phase 2 Architecture

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

Components

Planner
Decides which steps to execute.
Example:

analyze_position
detect_patterns
retrieve_context
generate_explanation
File:

agents/planner.py

Executor
Executes tools.
Available Tools:

stockfish_tool
feature_lookup_tool
dataset_search_tool
rag_retriever
File:

agents/executor.py

Critic
Verifies consistency.
Must detect:

contradictions with Stockfish
incorrect explanations
conceptual errors
File:

agents/critic.py

Memory
Stores:

analysis history
detected patterns
player's frequent errors
Allows personalization.
File:

agents/memory.py

Complete Phase 2 Flow

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

### Module 11 — Capstone (Agentic Backend Integration)

> **Definición general:** [Glosario — Capstone](#capstone).

**Aplicación en ChessTrainer:** proyecto integrador de cierre de **Phase 2**. Un solo flujo reproducible (notebook o script) demuestra que el “AI Chess Coach” funciona de punta a punta con: datos reales (1–2), modelo y MLflow (4–5), SHAP y coaching 6.5, RAG (7), LLM (8), pruebas de alucinación (9) y orquestación planner → executor → critic → memory (10). Prioridad **backend**; la UI pública llega en el módulo 12.
|         |                                                  |
| ------- | ------------------------------------------------ |
| Estado  | 📋 Planificado (Phase 2)                          |
| Formato | Demo E2E + informe de evaluación                 |
| UI      | No obligatoria; prioridad backend y orquestación |

**Objective:**
integrate all Phase 1 + Phase 2 backend components in one coherent AI Chess Coach workflow.

Scope:

- no full UI required yet
- backend and orchestration integration first

Mandatory Capstone Features:

- upload/read PGN input
- run existing feature pipeline (reuse, no parser rewrite)
- predict move quality/errors
- generate grounded explanation (RAG + LLM)
- validate explanation consistency via critic
- persist memory signals for personalization

Mandatory Evidence:

- demo script or notebook running end-to-end
- MLflow run references for model stage
- evaluation report including inconsistency/hallucination findings and improvements vs Module 9 baseline

## Phase 3

### Module 12 — MVP UI + FastAPI (Final Course Demo)
Objective:
deliver a quick MVP of AI Chess Coach visible to end users.

Architecture:

Basic UI (Streamlit or minimal web UI)
↓
FastAPI
↓
ML + RAG + LLM + Agentic backend services
↓
database

Endpoints:

/analyze_game
/predict_move_quality
/explain_position

### Module 13 — React + Vite Production Bridge
Objective:
define migration path from course MVP to production-grade ChessInsight rebuild using React + Vite.

Deliverables:

- UI/API contract definition for frontend migration
- component/page map from MVP to React + Vite
- phased migration plan from course MVP to production ChessInsight architecture

Expected Result
Copilot must generate approximately:

30 notebooks
40 scripts
Complete ML pipeline
RAG pipeline
LLM explanation system
agentic architecture
MVP API + basic UI
React + Vite migration foundation

Everything built on the real ChessTrainer system.