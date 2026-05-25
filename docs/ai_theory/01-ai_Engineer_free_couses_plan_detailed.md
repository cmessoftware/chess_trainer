# AI Engineering Roadmap 2026 — Descripción detallada de temas

---

## ETAPA 1 — Fundamentos AI/ML (Semanas 1–4)

### Semana 1: Microsoft AI for Beginners Foundation

**Sesión A (Lunes) — Intro to AI (2h)**
- **Objetivo:** Entender qué es AI, historia, definiciones y relación entre ML/DL/GenAI
- **Recurso:** https://github.com/microsoft/AI-For-Beginners
- **Temas:** ¿Qué es AI?, aplicaciones reales, casos de uso, diferencia hype vs realidad
- **Laboratorio:** Investigar 3 casos de éxito de AI en dominios diversos
- **ColorId:** 9 (Blueberry)

**Sesión B (Miércoles) — Machine Learning Basics (2h)**
- **Objetivo:** Conceptos fundamentales de ML: tipos de aprendizaje, pipeline, metrics
- **Temas:** Supervised/unsupervised/reinforcement learning, train/test/validation, overfitting, underfitting, métricas básicas (accuracy, precision, recall, F1)
- **Laboratorio:** Generar dataset simple de ajedrez (posición → mejor movimiento), train/test split
- **ColorId:** 9 (Blueberry)

**Sesión C (Viernes) — Lab: PGN → Features (2h)**
- **Objetivo:** Extraer features estructurados de archivos PGN
- **Implementar:**
  - Parser de PGN (usando python-chess)
  - Feature extraction: movimientos legales, material balance, control del centro, etc.
  - DataFrame con features por posición
  - Visualización de distribución de features
- **Entregable:** Script funcional + análisis exploratorio de 100 partidas
- **ColorId:** 9 (Blueberry)

---

### Semana 2: Neural Networks & NLP Intro

**Sesión A (Lunes) — Neural Networks (2h)**
- **Objetivo:** Arquitectura neuronal, forward pass, backpropagation, activaciones
- **Temas:** Perceptrón, redes densas, capas, funciones de activación (ReLU, sigmoid, tanh), backprop intuición, gradient descent
- **Laboratorio:** Entrenar red simple en sklearn/numpy
- **ColorId:** 9 (Blueberry)

**Sesión B (Miércoles) — NLP Basics (2h)**
- **Objetivo:** Procesamiento de texto, vectorización, contexto
- **Temas:** Tokenización manual, bag-of-words, TF-IDF, conceptos de secuencia, n-gramas
- **Laboratorio:** Vectorizar análisis de ajedrez (texto descriptivo → vector)
- **ColorId:** 9 (Blueberry)

**Sesión C (Viernes) — Lab: Data Cleaning (2h)**
- **Objetivo:** Validar, limpiar y perfilar datasets de ajedrez
- **Implementar:**
  - Script de validación (tipos, valores faltantes, outliers)
  - Tratamiento de duplicados y errores
  - Reporte de calidad (% missing, distribución de variables)
  - Documentación de data dictionary
- **Entregable:** Dataset limpio + reporte de calidad de datos
- **ColorId:** 9 (Blueberry)

---

### Semana 3: Transformers & Embeddings

**Sesión A (Lunes) — Tokenization & Transformers (2h)**
- **Objetivo:** Cómo funcionan los tokenizadores modernos y arquitectura Transformer
- **Recurso:** https://huggingface.co/learn/nlp-course
- **Temas:** BPE (Byte Pair Encoding), WordPiece, SentencePiece, mecanismo de atención, multi-head attention, positional encoding
- **Laboratorio:** Experimentar con diferentes tokenizadores (HF)
- **ColorId:** 9 (Blueberry)

**Sesión B (Miércoles) — Transformers en Profundidad (2h)**
- **Objetivo:** Entender arquitecturas encoder/decoder: BERT, GPT, T5
- **Temas:** BERT (bidirectional), GPT (causal), T5 (seq2seq), pre-training, fine-tuning, transfer learning
- **Laboratorio:** Cargar modelo pre-entrenado, explorar embeddings
- **ColorId:** 9 (Blueberry)

**Sesión C (Viernes) — Lab: Embeddings Básicos (2h)**
- **Objetivo:** Generar embeddings de movimientos de ajedrez
- **Implementar:**
  - Cargar modelo pre-entrenado (ej. sentence-transformers)
  - Generar embeddings para posiciones ajedrez (descripción textual)
  - Calcular similitud coseno entre posiciones
  - Visualización 2D (t-SNE o UMAP)
- **Entregable:** Matriz de embeddings + visualización de similitud
- **ColorId:** 9 (Blueberry)

---

### Semana 4: Applied ML & Feature Engineering

**Sesión A (Lunes) — Embeddings Avanzados (2h)**
- **Objetivo:** Dense embeddings, similarity metrics, indexación escalable
- **Temas:** Cosine similarity, dot product, Euclidean distance, ANN (Approximate Nearest Neighbors), FAISS basics, scaling a millones de vectores
- **Laboratorio:** Comparar métodos de similitud en embeddings
- **ColorId:** 9 (Blueberry)

**Sesión B (Miércoles) — Data Quality & ML Lifecycle (2h)**
- **Objetivo:** Profundidad en calidad de datos y ciclo de vida ML
- **Recurso:** https://madewithml.com
- **Temas:** Data validation, data drift, concept drift, versioning de datasets, reproducibilidad, data lineage
- **Laboratorio:** Detectar drift en features históricos
- **ColorId:** 9 (Blueberry)

**Sesión C (Viernes) — Lab: Clustering de Errores (2h)**
- **Objetivo:** Agrupar movimientos fallidos usando embeddings
- **Implementar:**
  - Etiquetar posiciones como "movimiento bueno" vs "movimiento malo"
  - Agrupar con K-means sobre embeddings
  - Analizar características comunes de cada cluster
  - Dashboard de patrones de error
- **Entregable:** Análisis de clusters de errores + documento de patrones
- **ColorId:** 9 (Blueberry)

---

## ETAPA 2 — GenAI Foundation & Prompting (Semanas 5–7)

### Semana 5: Foundation Models & GenAI Intro

**Sesión A (Lunes) — Foundation Models (2h)**
- **Objetivo:** Qué son, escala, propiedades emergentes
- **Recurso:** Chip Huyen — "AI Engineering"
- **Temas:** Large Language Models (LLMs), escala (parámetros, tokens), propiedades emergentes, in-context learning, token economy, costo por token
- **Laboratorio:** Analizar características de 3 modelos (parámetros, costo, velocidad)
- **ColorId:** 5 (Banana)

**Sesión B (Miércoles) — GenAI L01: Introduction to GenAI and LLMs (2h)**
- **Objetivo:** Arquitectura de LLMs, tokens, casos de uso
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/01-introduction-to-genai
- **Temas:** Qué es GenAI, cómo funcionan los LLMs, tokenization, BPE en contexto real, casos de uso (generación, clasificación, Q&A)
- **Laboratorio:** Jugar con API de LLM (OpenAI/Claude), explorar outputs con diferentes temperaturas
- **ColorId:** 5 (Banana)

**Sesión C (Viernes) — Lab: Model Selection (2h)**
- **Objetivo:** Criterios para elegir modelo según caso de uso
- **Implementar:**
  - Comparar 4 modelos: GPT-4o, Claude 3.5, Mistral, Llama 2
  - Matriz de criterios: costo, latencia, capacidades, contexto window
  - Test simple: análisis de partida de ajedrez en cada modelo
  - Reporte: qué modelo para qué tarea
- **Entregable:** Matriz de comparación + documento de recomendación
- **ColorId:** 5 (Banana)

---

### Semana 6: Prompt Engineering Fundamentals

**Sesión A (Lunes) — GenAI L02: Exploring and Comparing LLMs (2h)**
- **Objetivo:** Benchmarks, trade-offs, criterios de evaluación
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/02-exploring-and-comparing-different-llms
- **Temas:** LLM benchmarks (MMLU, HellaSwag, etc.), cost/performance trade-offs, latency, context windows, multimodal capabilities
- **Laboratorio:** Ejecutar benchmark simple en 3 modelos
- **ColorId:** 5 (Banana)

**Sesión B (Miércoles) — GenAI L04: Prompt Engineering Fundamentals (2h)**
- **Objetivo:** Técnicas de prompting: few-shot, zero-shot, system prompts
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/04-prompt-engineering-fundamentals
- **Temas:** Few-shot learning, zero-shot learning, system prompts, roles, CoT (chain-of-thought) intro, best practices
- **Laboratorio:** Diseñar 5 variaciones de prompt para análisis de partida
- **ColorId:** 5 (Banana)

**Sesión C (Viernes) — Lab: Prompting Practice (2h)**
- **Objetivo:** Template y evaluación de prompts para ajedrez
- **Implementar:**
  - Crear template estándar para análisis de partida
  - Probar 5 variaciones (different system prompts, CoT)
  - Evaluar outputs (claridad, precisión, largo)
  - Documentar mejor variante
- **Entregable:** Prompt template documentado + notas de evaluación
- **ColorId:** 5 (Banana)

---

### Semana 7: Advanced Prompting & Retrieval

**Sesión A (Lunes) — GenAI L05: Advanced Prompts (2h)**
- **Objetivo:** Técnicas avanzadas: CoT, ReAct, self-consistency
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/05-advanced-prompts
- **Temas:** Chain-of-thought (CoT), ReAct (reasoning + acting), self-consistency, prompt chaining, meta-prompting
- **Laboratorio:** Implementar CoT para análisis táctico
- **ColorId:** 6 (Tangerine)

**Sesión B (Miércoles) — Chip Huyen: Retrieval Systems (2h)**
- **Objetivo:** Information retrieval, ranking, recuperación de contexto relevante
- **Recurso:** "AI Engineering" cap. Retrieval
- **Temas:** BM25, TF-IDF, neural retrieval, ranking methods, precision@K, recall
- **Laboratorio:** Comparar BM25 vs embeddings en búsqueda simple
- **ColorId:** 6 (Tangerine)

**Sesión C (Viernes) — Lab: ChromaDB Setup (2h)**
- **Objetivo:** Inicializar vector database local
- **Implementar:**
  - Instalar y configurar ChromaDB
  - Crear colección de partidas históricas
  - Generar e indexar embeddings
  - Query básicas: "búsqueda de apertura Siciliana"
- **Entregable:** ChromaDB funcional con 500+ partidas indexadas
- **ColorId:** 6 (Tangerine)

---

## ETAPA 3 — RAG & Agents (Semanas 8–10)

### Semana 8: RAG Pipeline Complete

**Sesión A (Lunes) — GenAI L08: Building Search Applications + Vector Databases (2h)**
- **Objetivo:** Embeddings, similitud, indexación para búsqueda
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/08-building-search-applications
- **Temas:** Embedding selection, similarity search, indexing strategies, scaling (FAISS, Pinecone, Azure AI Search)
- **Laboratorio:** Setup de búsqueda semántica en ChromaDB
- **ColorId:** 6 (Tangerine)

**Sesión B (Miércoles) — GenAI L15: RAG and Vector Databases (2h)**
- **Objetivo:** RAG pipeline completo: chunking, retrieval, ranking
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/15-rag-and-vector-databases
- **Temas:** RAG architecture, document chunking strategies, retriever, ranker, re-ranking
- **Laboratorio:** Implementar RAG básico sobre PDFs
- **ColorId:** 6 (Tangerine)

**Sesión C (Viernes) — Lab: RAG on Chess PDFs (2h)**
- **Objetivo:** RAG sobre libros y papers de ajedrez
- **Implementar:**
  - PDF loader (PyPDF2 o similar)
  - Chunking strategy (por párrafo, página, etc.)
  - Embedding y indexación de chunks
  - RAG query: usuario pregunta → busca contexto → LLM responde
- **Entregable:** RAG funcional sobre 3+ PDFs de ajedrez, ejemplos de queries
- **ColorId:** 6 (Tangerine)

---


### Semana 9: LLM Systems & Text Generation

**Sesión A (Lunes) — Full Stack Deep Learning: LLM Systems (2h)**
- **Objetivo:** Arquitectura de sistemas con LLMs, agents, orquestación
- **Recurso:** https://fullstackdeeplearning.com
- **Temas:** LLM systems design, orchestration patterns, tool use, function calling workflows
- **Laboratorio:** Diseñar arquitectura simple de agent
- **ColorId:** 11 (Graphite)

**Sesión B (Miércoles) — GenAI L06: Building Text Generation Applications (2h)**
- **Objetivo:** Diseño de aplicaciones de generación de texto
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/06-text-generation-apps
- **Temas:** Text generation apps, parametrización (temperature, top-k, top-p), output control, formatting
- **Laboratorio:** Build simple text generator
- **ColorId:** 4 (Flamingo)

**Sesión C (Viernes) — Lab: Generador de recomendaciones (MVP ChessInsightAI) (2h)**
- **Objetivo:** MVP de generación de recomendaciones automáticas para partidas de ajedrez en ChessInsightAI
- **Implementar:**
  - Integrar LLM para generar recomendaciones textuales a partir de una partida PGN
  - Definir prompt base para recomendaciones (ejemplo: "Sugiere mejoras para las jugadas blancas")
  - Probar con 3-5 partidas reales
  - Analizar outputs y ajustar prompt/temperatura
- **Entregable:** Script o notebook funcional que genere recomendaciones automáticas para partidas
- **ColorId:** 4 (Flamingo)

---

### Semana 10: AI Agents & Memory

**Sesión A (Lunes) — GenAI L17: AI Agents (2h)**
- **Objetivo:** Agent loops, planning, memory, ReAct pattern
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/17-ai-agents
- **Temas:** Agent architecture, ReAct (reasoning + acting), planning, tool use loops, memory systems (short-term/long-term)
- **Laboratorio:** Entender y adaptar ejemplo de ReAct
- **ColorId:** 11 (Graphite)

**Sesión B (Miércoles) — Full Stack DL: Orchestration & Async (2h)**
- **Objetivo:** Orquestación de agents, ejecución async, latency
- **Temas:** Multi-agent orchestration, async/await, prompt caching, request batching
- **Laboratorio:** Implementar agent chain simple
- **ColorId:** 11 (Graphite)

**Sesión C (Viernes) — Lab: Agent with Memory (2h)**
- **Objetivo:** Agente coach con memoria de sesión
- **Implementar:**
  - Conversation memory (store last N turns)
  - Tool list: analyze_position, suggest_move, explain_tactic
  - Multi-turn flow: usuario → agent → response
  - Persist conversation log
- **Entregable:** Chat interface funcional, memoria persistente, 5 conversaciones ejemplo
- **ColorId:** 11 (Graphite)

---

## ETAPA 4 — LLMOps & Production (Semanas 11–13)

### Semana 11: LLMOps & Application Lifecycle

**Sesión A (Lunes) — Full Stack DL: LLMOps (2h)**
- **Objetivo:** Operacionalizar LLMs en producción
- **Temas:** Prompt versioning, evaluation systems, tool use logging, memory management, cost monitoring
- **Laboratorio:** Diseñar prompt versioning system
- **ColorId:** 3 (Grape)

**Sesión B (Miércoles) — GenAI L14: GenAI Application Lifecycle (2h)**
- **Objetivo:** End-to-end LLMOps workflow
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/14-the-generative-ai-application-lifecycle
- **Temas:** LLMOps definition, continuous evaluation, prompt versioning, quality metrics, feedback loops
- **Laboratorio:** Crear evaluation framework
- **ColorId:** 3 (Grape)

**Sesión C (Viernes) — Lab: Evaluation Pipeline (2h)**
- **Objetivo:** Setup de evaluación automática de responses
- **Implementar:**
  - Define metrics: relevance, factuality, coherence (manual + LLM-based)
  - Build test dataset (10-20 cases)
  - Evaluate baseline vs improved prompts
  - Report: score comparisons
- **Entregable:** Evaluation suite + benchmark results
- **ColorId:** 3 (Grape)

---

### Semana 12: Security & Guardrails

**Sesión A (Lunes) — GenAI L13: Securing AI Applications (2h)**
- **Objetivo:** Seguridad en applicaciones AI
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/13-securing-ai-applications
- **Temas:** Prompt injection, jailbreaks, hallucinations, guardrails, red teaming, safety best practices
- **Laboratorio:** Intentar inyectar prompt, documentar vulnerabilidades
- **ColorId:** 3 (Grape)

**Sesión B (Miércoles) — Made With ML: Monitoring & Observabilidad (2h)**
- **Objetivo:** Monitorear y observar LLMs en producción
- **Temas:** Logging, tracing, metrics (latency, cost, quality), drift detection, alerting
- **Laboratorio:** Setup logging y tracing
- **ColorId:** 3 (Grape)

**Sesión C (Viernes) — Lab: Guardrails Implementation (2h)**
- **Objetivo:** Proteger endpoint de análisis contra inyecciones y hallucinations
- **Implementar:**
  - Input validation: sanitize user queries
  - Output filtering: detectar respuestas nonsensical
  - Fallback mechanism: "I don't know" cuando es necesario
  - Test: try 10 injection attempts
- **Entregable:** Guardrails implementation + security test report
- **ColorId:** 3 (Grape)

---

### Semana 13: Open Source Models & Fine-tuning Intro

**Sesión A (Lunes) — HuggingFace: Fine-tuning Introduction (2h)**
- **Objetivo:** Conceptos de fine-tuning, transfer learning, adaptadores
- **Temas:** Fine-tuning vs in-context learning, LoRA, QLoRA, full fine-tuning, dataset requirements
- **Laboratorio:** Revisar ejemplos de LoRA
- **ColorId:** 7 (Peacock)

**Sesión B (Miércoles) — GenAI L16: Open Source Models + HuggingFace (2h)**
- **Objetivo:** Ecosistema OSS, deployment, licencias
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/16-open-source-models
- **Temas:** HuggingFace Hub, modelos OSS populares (Llama, Mistral, Phi), licencias, deployment options
- **Laboratorio:** Descargar y ejecutar modelo OSS locally
- **ColorId:** 7 (Peacock)

**Sesión C (Viernes) — Lab: Model Comparison (2h)**
- **Objetivo:** Comparar rendimiento OSS vs propietarios
- **Implementar:**
  - Benchmark suite: 5 preguntas de ajedrez
  - Test en: GPT-4, Claude, Mistral, Llama 2
  - Metrics: speed, cost, quality
  - Chart: trade-offs visualization
- **Entregable:** Benchmark report con recomendaciones
- **ColorId:** 7 (Peacock)

---

## ETAPA 5 — Advanced Fine-tuning (Semanas 14–15)

### Semana 14: LLM Internals & Fine-tuning

**Sesión A (Lunes) — Andrej Karpathy: GPT Internals (2h)**
- **Objetivo:** Entender internals de GPT: token prediction, arquitectura, scaling
- **Recurso:** https://www.youtube.com/@AndrejKarpathy (vídeos: "Neural Networks: Zero to Hero")
- **Temas:** Token prediction task, transformer architecture deep-dive, scaling laws, training efficiency
- **Laboratorio:** Revisar código de nano-GPT
- **ColorId:** 7 (Peacock)

**Sesión B (Miércoles) — GenAI L18: Fine-Tuning LLMs (2h)**
- **Objetivo:** Técnicas de fine-tuning: LoRA, RLHF, dataset curation
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/18-fine-tuning
- **Temas:** LoRA, QLoRA, instruction tuning, RLHF basics, dataset curation for FT, eval post-FT
- **Laboratorio:** Preparar dataset para fine-tuning
- **ColorId:** 7 (Peacock)

**Sesión C (Viernes) — Lab: LoRA Training (2h)**
- **Objetivo:** Fine-tune modelo con LoRA para estilo de ajedrez
- **Implementar:**
  - Crear dataset: 100+ pares (posición + análisis esperado)
  - Setup LoRA training (Hugging Face transformers)
  - Train en GPU (30-60 min)
  - Evaluate: comparar respuestas antes/después FT
- **Entregable:** LoRA adapter + training log + comparison results
- **ColorId:** 7 (Peacock)

---

### Semana 15: SLMs & Local Inference

**Sesión A (Lunes) — GenAI L19: Building with SLMs (2h)**
- **Objetivo:** Small Language Models, eficiencia, edge deployment
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/19-slm
- **Temas:** SLMs (Phi-3, Mistral Small), edge deployment, quantization, energy efficiency, latency trade-offs
- **Laboratorio:** Explorar SLM capabilities
- **ColorId:** 7 (Peacock)

**Sesión B (Miércoles) — Made With ML: Local Inference (2h)**
- **Objetivo:** Serving modelos locally: Ollama, vLLM
- **Temas:** Ollama, vLLM, quantization (int4, int8), prompt caching, batching, latency optimization
- **Laboratorio:** Setup Ollama con modelo local
- **ColorId:** 7 (Peacock)

**Sesión C (Viernes) — Lab: Ollama Setup (2h)**
- **Objetivo:** Desplegar modelos localmente sin API cloud
- **Implementar:**
  - Install Ollama
  - Pull model (ej. Mistral 7B)
  - Create Ollama model file con system prompt customizado
  - Benchmark: latency, memory, quality vs cloud API
- **Entregable:** Local model running, benchmark report, cost comparison
- **ColorId:** 7 (Peacock)

---

## ETAPA 6 — Complementaria & Especialización (Semanas 16–19)


### Semana 16: Function Calling & Chat Applications

**Sesión A (Lunes) — GenAI L11: Function Calling (2h)**
- **Objetivo:** Tool use, schemas, structured outputs
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/11-integrating-with-function-calling
- **Temas:** Function calling, tool schemas (JSON), JSON mode, structured outputs, parsing
- **Laboratorio:** Implementar LLM que pueda llamar función simple
- **ColorId:** 11 (Graphite)

**Sesión B (Miércoles) — GenAI L07: Building Chat Applications (2h)**
- **Objetivo:** Diseño conversacional, manejo de historial
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/07-building-chat-applications
- **Temas:** Chat design, multi-turn dialogs, context management, conversation memory, prompt injection in chats
- **Laboratorio:** Build chat interface
- **ColorId:** 4 (Flamingo)

**Sesión C (Viernes) — Lab: Demo Coach Bot (2h)**
- **Objetivo:** Prototipo conversacional de coach de ajedrez
- **Implementar:**
  - Chat interface (Streamlit o Gradio)
  - System prompt para coach role
  - Multi-turn: mantener contexto de conversación
  - Integraciones: RAG, function calling (Stockfish)
- **Entregable:** Working demo, test with 5+ conversaciones
- **ColorId:** 4 (Flamingo)

---

### Semana 17: Image & Low-code

**Sesión A (Lunes) — GenAI L09: Building Image Generation Applications (2h)**
- **Objetivo:** Generación de imágenes, evaluation visual
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/09-building-image-applications
- **Temas:** Image generation (Dall-E, Stable Diffusion), prompting for images, evaluation
- **Laboratorio:** Generate chess board diagrams
- **ColorId:** 4 (Flamingo)

**Sesión B (Miércoles) — GenAI L10: Building Low Code AI Applications (2h)**
- **Objetivo:** Prototipado rápido sin-código/bajo-código
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/10-building-low-code-ai-applications
- **Temas:** No-code/low-code tools (Zapier, Make, Flowise), rapid validation, workflows
- **Laboratorio:** Build workflow en tool low-code
- **ColorId:** 4 (Flamingo)

**Sesión C (Viernes) — Lab: Visual Features (2h)**
- **Objetivo:** Visualizaciones didácticas de análisis
- **Implementar:**
  - Board diagram + highlights (mejores movimientos)
  - Position annotation (evaluaciones numéricas)
  - Move sequences visualization
  - Training materials generation
- **Entregable:** Visualization module + 10+ examples
- **ColorId:** 4 (Flamingo)

---

### Semana 18: UX & Model Families

**Sesión A (Lunes) — GenAI L12: Designing UX for AI Applications (2h)**
- **Objetivo:** UX patterns para aplicaciones AI
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/12-designing-ux-for-ai-applications
- **Temas:** Transparency, trust, feedback loops, error handling, user expectations, explainability
- **Laboratorio:** Design UX mockup para coach app
- **ColorId:** 4 (Flamingo)

**Sesión B (Miércoles) — GenAI L20: Building with Mistral Models (2h)**
- **Objetivo:** Especializarse en familia Mistral
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/20-mistral
- **Temas:** Mistral family (7B, 8x7B, Large), capabilities, cost/performance, function calling, structured outputs
- **Laboratorio:** Compare Mistral variants
- **ColorId:** 4 (Flamingo)

**Sesión C (Viernes) — Lab: Multi-model Test (2h)**
- **Objetivo:** Benchmarking de modelos Mistral
- **Implementar:**
  - Test suite: 10 preguntas específicas de ajedrez
  - Compare: Mistral 7B, 8x7B, Large
  - Metrics: latency, quality, cost
  - Recommendation: mejor trade-off
- **Entregable:** Benchmark report + model selection doc
- **ColorId:** 4 (Flamingo)

---

### Semana 19: Meta Models & Production Ready

**Sesión A (Lunes) — GenAI L21: Building with Meta Models (2h)**
- **Objetivo:** Especializarse en familia Meta (Llama)
- **Link:** https://github.com/cmessoftware/generative-ai-for-beginners/tree/main/21-meta
- **Temas:** Llama family (2, 3, 3.1), open source advantages, fine-tuning, specialized versions
- **Laboratorio:** Compare Llama variants
- **ColorId:** 4 (Flamingo)

**Sesión B (Miércoles) — Full Stack DL: Production Ready (2h)**
- **Objetivo:** Deployment checklist, escalabilidad, monitoring
- **Temas:** Production deployment, scaling, failover, monitoring, observability, SLAs, cost optimization
- **Laboratorio:** Diseñar deployment architecture
- **ColorId:** 4 (Flamingo)

**Sesión C (Viernes) — Lab: Final Integration (2h)**
- **Objetivo:** Integrar todo en ChessInsightAI para producción
- **Implementar:**
  - End-to-end pipeline: PGN → analysis → user-facing API
  - Documentation: architecture, deployment, monitoring
  - Production checklist: security, scalability, reliability
  - Deployment script / IaC
- **Entregable:** Production-ready codebase + deployment docs
- **ColorId:** 4 (Flamingo)

---

## Notas finales

- **Flexibilidad:** Cada sesión es autónoma; puedes reordenar según tu disponibilidad.
- **Aplicación práctica:** Todos los laboratorios aplican directamente a ChessInsightAI.
- **Checkpoint:** Evalúa progreso al final de cada etapa (semanas 4, 7, 10, 13, 15, 19).
- **Actualización:** Este plan evoluciona; ajusta recursos y temas según cambios en el estado del arte.
