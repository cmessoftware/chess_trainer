# AI Engineering Roadmap 2026

## Perfil objetivo

Backend Architect → AI Engineer → LLMOps / AI Systems Architect

Carga semanal:

* 6 hs estructuradas
* 3 sesiones de 2 hs
* +2 hs opcionales aplicando conceptos en ChessInsightAI

---

# Objetivos del roadmap

Desarrollar capacidades prácticas en:

* AI Engineering
* LLMOps
* ML Systems
* Sistemas híbridos ML + LLM
* RAG
* Evaluation pipelines
* Observabilidad AI
* Orquestación de agentes
* Arquitectura AI productiva

---

# Integración: Generative AI for Beginners

Repositorio forkeado: https://github.com/cmessoftware/generative-ai-for-beginners

Lecciones prioritarias seleccionadas e integradas al roadmap según sinergia con ChessInsightAI y perfil AI Engineer / LLMOps.
Lecciones de bajo valor para este perfil omitidas: 06, 07, 09, 10, 12, 20, 21.

| Item | Semana | Título | Link repo forkeado | Conceptos a aprender | Sinergia con roadmap | Comentarios |
|------|--------|--------|--------------------|----------------------|----------------------|-------------|
| L01 | 5–6 | Introduction to GenAI and LLMs | [L01](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/01-introduction-to-genai) | Qué es GenAI, arquitectura LLMs, tokens, casos de uso, relación ML/DL/GenAI | Complementa Chip Huyen — Foundation models | Lectura obligatoria antes de iniciar Chip Huyen semana 5 |
| L02 | 5–6 | Exploring and Comparing LLMs | [L02](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/02-exploring-and-comparing-different-llms) | Comparación de modelos, criterios de selección, benchmarks, trade-offs costo/calidad | Guía práctica para elegir modelo en ChessInsightAI | Útil al decidir qué modelo usar para análisis de partidas |
| L04 | 5–6 | Prompt Engineering Fundamentals | [L04](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/04-prompt-engineering-fundamentals) | Few-shot, zero-shot, system prompts, templates, roles, best practices | Base práctica que complementa Chip Huyen Prompting | Aplicar directamente en prompts de explicación de jugadas |
| L05 | 5–6 | Advanced Prompts | [L05](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/05-advanced-prompts) | Chain-of-thought, ReAct, self-consistency, prompt chaining, meta-prompting | Profundiza L04, base conceptual para agentes y LLMOps | Aplicar en pipeline de análisis posicional de ChessInsightAI |
| L08 | 7–10 | Building Search Apps + Vector Databases | [L08](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/08-building-search-applications) | Embeddings, cosine similarity, vector search, indexing, Azure AI Search | Paralelo directo a implementación ChromaDB / FAISS / Qdrant | Búsqueda semántica sobre repertorio de aperturas |
| L15 | 7–10 | RAG and Vector Databases | [L15](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/15-rag-and-vector-databases) | RAG pipeline completo, chunking, retrieval, grounding, re-ranking | Paralelo directo a RAG sobre PDFs de ajedrez — Semana 7-10 | Implementar RAG sobre libros y partidas históricas |
| L11 | 11–14 | Function Calling | [L11](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/11-integrating-with-function-calling) | Tool use, function schemas, JSON mode, structured outputs, orquestación | Base para agentes en Full Stack Deep Learning | LLM llamando a Stockfish como herramienta externa |
| L17 | 11–14 | AI Agents | [L17](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/17-ai-agents) | Agent loops, planning, memory, tool use, ReAct pattern, frameworks | Complementa y profundiza Full Stack Deep Learning Agents | Agente coach con memoria de sesión e historial de partidas |
| L13 | 15–18 | Securing AI Applications | [L13](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/13-securing-ai-applications) | Prompt injection, jailbreaks, guardrails, contenido harmful, red teaming | Complementa implementación de guardrails en pipeline LLMOps | Proteger endpoint de análisis contra inyecciones de prompts |
| L14 | 15–18 | GenAI Application Lifecycle | [L14](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/14-the-generative-ai-application-lifecycle) | LLMOps, evaluación continua, versionado de prompts, métricas de calidad | Complementa LLMOps de Full Stack Deep Learning Semana 15-18 | Checklist para llevar ChessInsightAI a producción |
| L16 | 19–22 | Open Source Models + HuggingFace | [L16](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/16-open-source-models) | Modelos OSS, HuggingFace Hub, deployment, licencias, comparativa propietario vs OSS | Complementa HuggingFace NLP Semana 19-22 | Evaluar modelos locales para inferencia offline en ChessInsightAI |
| L18 | 19–22 | Fine-Tuning LLMs | [L18](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/18-fine-tuning) | Fine-tuning, LoRA, RLHF, dataset curation, evaluación post-fine-tune | Paralelo a Andrej Karpathy — LLM architecture | Fine-tune modelo para terminología y estilos de juego de ajedrez |
| L19 | 19–22 | Building with SLMs | [L19](https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/19-slm) | Small Language Models, edge deployment, eficiencia energética, trade-offs | Complementa local inference con Ollama — Semana 19-22 | SLMs para inferencia local sin dependencia de API cloud |

---

# Distribución semanal

## Sesión A — Fundamentos y teoría (2 hs)

Objetivo:

* fundamentos AI/ML,
* transformers,
* embeddings,
* NLP,
* prompting,
* evaluación.

Recursos:

* Microsoft AI for Beginners
* Elements of AI
* HuggingFace NLP
* Chip Huyen

---

## Sesión B — Ingeniería AI / MLOps (2 hs)

Objetivo:

* pipelines,
* observabilidad,
* serving,
* deployment,
* orchestration,
* RAG,
* evaluación.

Recursos:

* Made With ML
* Full Stack Deep Learning

---

## Sesión C — Laboratorio práctico (2 hs)

Objetivo:

* implementación,
* prototipos,
* notebooks,
* APIs,
* embeddings,
* pipelines,
* agentes.

Todo aplicado a:

* ChessInsightAI,
* sistemas locales,
* RAG,
* LLMs.

---

## +2 hs opcionales — ChessInsightAI

Objetivo:

* aplicar conceptos,
* validar arquitectura,
* experimentar,
* construir portfolio técnico.

---

# ETAPA 1 — Fundamentos AI/ML

Duración: 6 semanas

---

# Semana 1–2

## Teoría

### Microsoft AI for Beginners

https://github.com/microsoft/AI-For-Beginners

Temas:

* Introducción a AI
* Machine Learning
* Redes neuronales
* NLP básico

---

### Elements of AI

https://www.elementsofai.com/

Temas:

* Fundamentos conceptuales
* Tipos de IA
* Limitaciones y capacidades
* Pensamiento crítico AI

---

## Ingeniería

### Made With ML

https://madewithml.com/

Temas:

* ML systems overview
* Data quality
* Lifecycle ML

---

## Laboratorio

Implementar:

* Pipeline PGN → features
* Notebook exploratorio
* Visualización de métricas
* Limpieza de datasets

---

# Semana 3–4

## Teoría

### HuggingFace NLP Course

https://huggingface.co/learn/nlp-course/chapter1/1

Temas:

* Tokenization
* Transformers
* Attention
* Embeddings

---

## Ingeniería

### Made With ML

Temas:

* Experiment tracking
* Model evaluation
* Métricas ML

---

## Laboratorio

Implementar:

* Similarity search
* Embeddings básicos
* Clustering de errores de ajedrez

---

# Semana 5–6

## Teoría

### AI Engineering — Chip Huyen

https://www.oreilly.com/library/view/ai-engineering/9781098166298/

Temas:

* Foundation models
* Prompting
* Context windows
* LLM applications

---

### Generative AI for Beginners — Lecciones integradas (Semana 5–6)

https://github.com/cmessoftware/generative-ai-for-beginners

Lecciones:

* **L01** — Introduction to GenAI and LLMs: qué es GenAI, arquitectura LLMs, tokens, casos de uso
* **L02** — Exploring and Comparing LLMs: criterios de selección de modelo, benchmarks, trade-offs costo/calidad
* **L04** — Prompt Engineering Fundamentals: few-shot, zero-shot, system prompts, templates, roles
* **L05** — Advanced Prompts: chain-of-thought, ReAct, self-consistency, prompt chaining

Aplicación en ChessInsightAI:

* Selección de modelo para análisis de partidas
* Prompts para explicación de jugadas y planes posicionales
* Base conceptual para RAG e ingeniería de prompts en etapas posteriores

---

## Ingeniería

### Made With ML

Temas:

* Feature stores
* Serving concepts
* Pipelines productivos

---

## Laboratorio

Implementar:

* FastAPI inference service
* Endpoint PGN → análisis
* Pipeline de inferencia simple

---

# ETAPA 2 — AI Engineering + ML Systems

Duración: 8 semanas

---

# Semana 7–10

## Teoría

### Chip Huyen

Temas:

* Retrieval
* Embeddings
* RAG
* Inference systems

---

### Generative AI for Beginners — Lecciones integradas (Semana 7–10)

https://github.com/cmessoftware/generative-ai-for-beginners

Lecciones:

* **L08** — Building Search Apps + Vector Databases: embeddings, cosine similarity, vector search, indexing
* **L15** — RAG and Vector Databases: RAG pipeline completo, chunking, retrieval, grounding, re-ranking

Aplicación en ChessInsightAI:

* Búsqueda semántica sobre repertorio de aperturas
* RAG sobre libros de ajedrez y partidas históricas
* Indexar posiciones FEN y anotaciones con embeddings

---

## Ingeniería

### Made With ML

Temas:

* Deployment
* Monitoring
* Drift
* Observabilidad

---

## Laboratorio

Implementar:

* Vector DB local
* Búsqueda semántica
* RAG sobre PDFs de ajedrez

Opciones:

* ChromaDB
* FAISS
* Qdrant

---

# Semana 11–14

## Teoría

### Full Stack Deep Learning

https://fullstackdeeplearning.com/

Temas:

* LLM systems
* Agents
* Evaluation
* Orchestration

---

### Generative AI for Beginners — Lecciones integradas (Semana 11–14)

https://github.com/cmessoftware/generative-ai-for-beginners

Lecciones:

* **L11** — Function Calling: tool use, function schemas, JSON mode, structured outputs, orquestación
* **L17** — AI Agents: agent loops, planning, memory, tool use, ReAct pattern, frameworks

Aplicación en ChessInsightAI:

* LLM llamando a Stockfish como herramienta externa mediante function calling
* Agente coach con memoria de sesión e historial de partidas del usuario

---

## Ingeniería

### Full Stack Deep Learning

Temas:

* Serving
* Async pipelines
* Latency
* Batching

---

## Laboratorio

Implementar:

* Planner/Executor básico
* Logging de prompts
* Evaluador simple
* Tracing de inferencias

---

# ETAPA 3 — LLMOps

Duración: 8 semanas

---

# Semana 15–18

## Teoría

### Full Stack Deep Learning

Temas:

* LLMOps
* Prompt evaluation
* Tool use
* Memory systems

---

### Generative AI for Beginners — Lecciones integradas (Semana 15–18)

https://github.com/cmessoftware/generative-ai-for-beginners

Lecciones:

* **L13** — Securing AI Applications: prompt injection, jailbreaks, guardrails, contenido harmful, red teaming
* **L14** — GenAI Application Lifecycle: LLMOps, evaluación continua, versionado de prompts, métricas de calidad

Aplicación en ChessInsightAI:

* Guardrails en endpoint de análisis de ajedrez contra inyecciones de prompts
* Checklist LLMOps para llevar ChessInsightAI a producción

---

## Ingeniería

Temas:

* Prompt versioning
* Retries/fallbacks
* Guardrails
* Observabilidad

---

## Laboratorio

Implementar:

* Evaluation pipeline
* Hallucination checks
* Grounding validator
* Quality scoring

---

# Semana 19–22

## Teoría

### HuggingFace NLP

Temas:

* Fine-tuning overview
* Embeddings avanzados
* Inference optimization

---

### Generative AI for Beginners — Lecciones integradas (Semana 19–22)

https://github.com/cmessoftware/generative-ai-for-beginners

Lecciones:

* **L16** — Open Source Models + HuggingFace: modelos OSS, HuggingFace Hub, deployment, licencias, comparativa vs propietarios
* **L18** — Fine-Tuning LLMs: fine-tuning, LoRA, RLHF, dataset curation, evaluación post-fine-tune
* **L19** — Building with SLMs: Small Language Models, edge deployment, eficiencia energética, trade-offs

Aplicación en ChessInsightAI:

* Fine-tune modelo para terminología y estilos de juego de ajedrez
* SLMs para inferencia local sin dependencia de API cloud
* Evaluar modelos open-source vs propietarios para análisis de partidas

---

### Andrej Karpathy

https://www.youtube.com/@AndrejKarpathy

Temas:

* GPT internals
* Transformers intuition
* Token prediction
* LLM architecture

---

## Ingeniería

Temas:

* Quantization
* Ollama
* vLLM
* Local inference

---

## Laboratorio

Implementar:

* Pipeline híbrido:

  * Stockfish
  * ML tabular
  * LLM explanations

---

# ETAPA 4 — Consolidación

Duración: resto del año

---

# Objetivo

Convertir ChessInsightAI en:

* laboratorio AI,
* portfolio técnico,
* plataforma experimental,
* demostración arquitectónica.

---

# Prioridades de implementación

## Prioridad alta

* Evaluation pipeline
* Explainability
* Embeddings
* RAG
* Observabilidad
* Orquestación

---

## Prioridad media

* Agentes
* Memory systems
* Multi-stage reasoning
* Vector search avanzado

---

## Prioridad baja

* Fine tuning
* LoRA
* Entrenamiento profundo de transformers

---

# Recursos complementarios

## HuggingFace

https://huggingface.co/

---

## LangChain

https://www.langchain.com/

---

## LlamaIndex

https://www.llamaindex.ai/

---

## Ollama

https://ollama.com/

---

## ChromaDB

https://www.trychroma.com/

---

## FAISS

https://github.com/facebookresearch/faiss

---

## Qdrant

https://qdrant.tech/

---

# Comunidades recomendadas

## HuggingFace Community

https://huggingface.co/community

---

## DeepLearning.AI Community

https://community.deeplearning.ai/

---

## Reddit — LocalLLaMA

https://www.reddit.com/r/LocalLLaMA/

---

## Reddit — MachineLearning

https://www.reddit.com/r/MachineLearning/

---

## Kaggle Discussions

https://www.kaggle.com/discussions

---

# Resultado esperado al finalizar

Capacidad sólida para:

* diseñar sistemas AI reales,
* integrar ML + LLM,
* construir pipelines AI,
* implementar RAG,
* desarrollar observabilidad AI,
* construir agentes,
* evaluar outputs generativos,
* diseñar arquitecturas híbridas,
* operar modelos locales.

Además:

* portfolio técnico diferenciador,
* experiencia práctica real,
* base sólida para AI Engineering y LLMOps.
