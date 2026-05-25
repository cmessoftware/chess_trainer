# ChessTrainer — RAG + NLP + Computer Vision Enhancement Plan

## Objetivo

Diseñar una arquitectura que permita:

1. Mejorar la calidad de las recomendaciones en lenguaje natural (data-driven, no genéricas)
2. Incorporar extracción de posiciones (FEN) desde PDFs mediante visión por computadora
3. Generar ejercicios personalizados basados en:
   - teoría (libros)
   - errores reales del usuario

---

# 1. Mejora de Recomendaciones (RAG + NLP)

## 1.1 Problema actual

- Embeddings sobre texto plano → bajo valor semántico
- Recomendaciones genéricas
- Sin conexión fuerte entre teoría y errores reales

---

## 1.2 Estrategia

### A. Preprocesamiento semántico

Transformar texto de libros en documentos estructurados:

```json
{
  "book": "My System",
  "chapter": "Centralization",
  "section": "Outposts",
  "text": "...",
  "language": "en",
  "concepts": ["outpost"],
  "phase": "middlegame",
  "difficulty": "intermediate"
}
B. NLP (reglas + diccionario)

Detectar conceptos clave en español e inglés:

CHESS_TERMS = {
    "clavada": "pin",
    "pin": "pin",
    "doble ataque": "fork",
    "fork": "fork",
    "sobrecarga": "overload",
    "overload": "overload",
    "rayos x": "xray",
    "x-ray": "xray"
}

Salida esperada:

{
  "concepts": ["pin"],
  "phase": "middlegame"
}
C. Embeddings enriquecidos

No indexar solo texto:

texto

conceptos

metadata

dificultad

idioma

D. Retrieval híbrido

Combinar:

similitud semántica

filtros estructurados

Ejemplo:

collection.query(
    query_texts=["errores en clavadas"],
    where={
        "concepts": "pin",
        "phase": "middlegame"
    }
)
E. Fusión de contexto

Recuperar:

teoría (libros)

datos del usuario (features, errores)

F. Prompt estructurado
ROLE: ChessTrainer Analyst

INPUT:
- contexto teórico
- errores reales del usuario

TASK:
1. identificar patrón
2. explicar causa
3. sugerir corrección concreta
4. vincular con concepto

OUTPUT:
- recomendaciones accionables
1.3 Ranking personalizado

Score final:

score =
    similarity
  + weight_user_data
  + weight_error_frequency
  + weight_phase_match
2. Extracción de FEN desde imágenes (Computer Vision)
2.1 Problema

PDFs contienen diagramas de tablero

parsers de texto no los interpretan

se pierde información crítica

2.2 Objetivo

Convertir:

imagen tablero → FEN
2.3 Estrategias
Nivel 1 — Manual (bootstrap)

seleccionar posiciones clave

registrar FEN manualmente

Nivel 2 — Semi-automático

Pipeline:

Extraer imágenes del PDF

Detectar tablero (bounding box)

Dividir en grilla 8x8

Clasificar piezas por celda

Nivel 3 — Modelo CV

Opciones:

CNN simple (clasificación por celda)

modelos tipo YOLO (detección de piezas)

librerías existentes:

chesscog

lichess board recognition

2.4 Representación
{
  "source": "book",
  "concept": "pin",
  "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3",
  "description": "ejemplo de clavada en columna e",
  "phase": "middlegame"
}
2.5 Indexación en ChromaDB
collection.add(
    documents=[description],
    metadatas=[{
        "fen": fen,
        "concept": "pin",
        "phase": "middlegame",
        "source": "book"
    }]
)
2.6 Features derivadas desde FEN
{
  "material_balance": 0,
  "open_files": ["e"],
  "king_safety": "weak",
  "tactical_tags": ["pin"]
}
3. Generación de Ejercicios Personalizados
3.1 Input

dataset del usuario:

error_label

tactical_tags

score_diff

base de libros (con FEN)

clustering de errores

3.2 Pipeline
1. detectar patrón dominante
2. recuperar ejemplos teóricos (libros)
3. recuperar posiciones similares (usuario)
4. generar ejercicio
3.3 Ejemplo

Input:

{
  "pattern": "pin",
  "frequency": 18,
  "phase": "middlegame"
}

Output:

{
  "exercise_id": "pin_001",
  "fen": "...",
  "task": "encontrar la mejor jugada",
  "concept": "pin",
  "source": "book + user",
  "explanation": "la pieza está sobrecargada..."
}
3.4 Tipos de ejercicios

detección táctica (mate, fork, pin)

prevención de errores

mejora posicional (outposts, estructura)

decisiones críticas

3.5 Matching teoría ↔ errores

Regla clave:

si usuario falla en X
→ buscar teoría de X
→ generar ejercicio de X
3.6 Loop de aprendizaje
ejercicio → respuesta usuario → evaluación → feedback → dataset
4. Soporte multilenguaje (ES / EN)
4.1 Normalización

Mapear conceptos a forma canónica:

clavada → pin
horquilla → fork
4.2 Indexación

Guardar:

{
  "original_text": "...",
  "language": "es",
  "concepts": ["pin"]
}
4.3 Query

Permitir:

queries en español

queries en inglés

5. Arquitectura propuesta
Streamlit
   ↓
FastAPI
   ↓
RAG Service
   ├── retrieve_books
   ├── retrieve_user_data
   ├── retrieve_positions (FEN)
   ├── rerank
   └── build_prompt
   ↓
ChromaDB
   ↓
LLM (Llama 3.1 / Ollama)
6. Roadmap de implementación
Fase 1

parsing estructurado de PDFs

NER simple (diccionario)

indexación en ChromaDB

Fase 2

integración con datos del usuario

RAG híbrido (books + user)

Fase 3

extracción de FEN (manual + semi-automática)

indexación de posiciones

Fase 4

generación de ejercicios

loop de feedback

Fase 5

modelos CV para automatizar FEN

clustering de errores

personalización avanzada

Resultado esperado

Sistema que:

entiende conceptos ajedrecísticos

conecta teoría con errores reales

usa posiciones concretas (FEN)

genera recomendaciones accionables

produce ejercicios personalizados

No es un chatbot.

Es un sistema de entrenamiento cognitivo basado en datos + teoría + visión.