# ChessTrainer — Arquitectura Orquestada (Planner / Executor / Critic / Memory)

## Objetivo

Reestructurar la arquitectura actual del sistema (RAG + ML + CV) hacia un modelo **determinista, modular y validado**, donde:

- No haya generación sin evidencia
- No haya acoplamiento entre módulos
- El LLM no sea fuente de verdad
- Todo pase por un flujo controlado

---

# 1. Problema de la arquitectura actual

Arquitectura actual:

React
↓
FastAPI
↓
RAG Service
↓
ChromaDB
↓
LLM


Problemas:

- Mezcla de responsabilidades
- Falta de control de flujo
- Sin validación de coherencia
- LLM produce contenido sin grounding fuerte
- ML, RAG y CV no están integrados

---

# 2. Nueva arquitectura propuesta

## 2.1 Flujo principal

React / UI
↓
FastAPI
↓
Use Case Layer (Application)
↓
Planner
↓
Executor
↓
Critic
↓
Memory
↓
Response


---

## 2.2 Responsabilidades

### Planner
Define qué analizar.

- Selección de jugadas críticas
- Definición de tipo de análisis:
  - táctico
  - posicional
  - entrenamiento
- Priorización

Salida:

```json
{
  "target_moves": [12, 18, 24],
  "analysis_modes": ["engine", "features", "ml", "rag"],
  "priority": {
    "12": "high"
  }
}
```

---

## 2.2 Responsabilidades

### Planner
Define qué analizar.

- Selección de jugadas críticas
- Definición de tipo de análisis:
  - táctico
  - posicional
  - entrenamiento
- Priorización

Salida:

```json
{
  "target_moves": [12, 18, 24],
  "analysis_modes": ["engine", "features", "ml", "rag"],
  "priority": {
    "12": "high"
  }
}
```
Executor

Produce evidencia objetiva.

Incluye:

- Stockfish
- Feature extraction
- Modelos ML
- RAG retrieval
- CV (FEN desde imágenes)

Salida:

```json
{
  "ply": 18,
  "score_diff": 155,
  "best_move": "Qh5+",
  "features": {...},
  "ml_prediction": {...},
  "rag_context": [...]
}
```
Critic

Valida coherencia.

Reglas:

- No puede haber explicación sin soporte del engine
- No puede haber “blunder” con score_diff bajo
- No puede haber táctica sin evidencia

Salida:

```json
{
  "is_consistent": true,
  "issues": [],
  "confidence": 0.91
}
```

Memory

Persistencia + aprendizaje acumulado.

Guarda:

- análisis por jugada
- features
- patrones del usuario
- frecuencia de errores

Permite:

- personalización
- clustering
- entrenamiento futuro

3. Integración con módulos existentes
3.1 RAG

RAG pasa a ser parte del Executor:

- retrieve_books
- retrieve_user_data
- retrieve_positions
- rerank
- build_prompt

El Planner define qué buscar
El Executor ejecuta la búsqueda
El Critic valida la salida

3.2 Machine Learning

ML pasa a ser parte del Executor:

- predicción de error_label
- clasificación de jugadas
- features dinámicas

El Critic valida consistencia con engine

3.3 Computer Vision (FEN)

También dentro del Executor:

- extracción de tablero desde PDF
- conversión a FEN
- feature extraction desde FEN

4. Use Case principal
class AnalyzeGameUseCase:

```python
    def __init__(self, planner, executor, critic, memory, explainer):
        self.planner = planner
        self.executor = executor
        self.critic = critic
        self.memory = memory
        self.explainer = explainer

    def run(self, game, options):

        plan = self.planner.build_plan(game, options)

        results = self.executor.execute(game, plan)

        final = []

        for r in results:

            explanation = self.explainer.generate(r)

            critique = self.critic.validate(r, explanation)

            if not critique["is_consistent"]:
                explanation = self.explainer.generate_restricted(r, critique)

            enriched = {
                **r,
                "explanation": explanation,
                "critique": critique
            }

            self.memory.store_move_analysis(game.id, enriched)

            final.append(enriched)

        self.memory.update_player_patterns(game.player_id, final)

        return final
```

5. Estructura de carpetas sugerida

```json
chess_trainer/
├── api/
├── application/
│   ├── services/
│   │   ├── planner_service.py
│   │   ├── executor_service.py
│   │   ├── critic_service.py
│   │   ├── memory_service.py
│   │   └── explanation_service.py
│   ├── use_cases/
│   │   └── analyze_game.py
├── domain/
│   ├── models/
│   ├── rules/
├── infrastructure/
│   ├── engine/
│   ├── ml/
│   ├── rag/
│   ├── cv/
│   ├── persistence/
│   └── llm/
```
1. Roadmap de implementación
- Fase 1
Planner simple (reglas)
Executor con Stockfish + features
Memory básica

- Fase 2
ML predictor integrado
Critic por reglas

- Fase 3
RAG integrado al Executor
Explicaciones con LLM (prompt estructurado)

- Fase 4
Generación de ejercicios
Uso de Memory para personalización

- Fase 5
CV para FEN automático
clustering de errores
critic híbrido (reglas + LLM)

1. Reglas de diseño obligatorias
   
- El LLM nunca es fuente de verdad
- El engine es la autoridad
- ML es evidencia secundaria

Todo output debe pasar por Critic

- No usar agentes autónomos
- No usar texto libre entre módulos
- Usar JSON estructurado siempre

1. Principio central
   
- Planner → decide
- Executor → produce evidencia
- Critic → valida
- Memory → aprende

Todo lo demás es infraestructura.