# Informe de análisis — Specs 07 vs 06*

> **Fecha:** 2026-08-03  
> **Documentos analizados:**
> - [07_criticals_position_and_candidate_moves_analysis.md](./07_criticals_position_and_candidate_moves_analysis.md) (en adelante **07-base**)
> - [07_1_complementary_functional_specification.md](./07_1_complementary_functional_specification.md) (en adelante **07.1**)
> - Specs 06*: [06_5-ai_chess_coach_course_llm_coaching_recommendations.md](./06_5-ai_chess_coach_course_llm_coaching_recommendations.md), [06_5_llm_coaching_recommendations_v7.md](./06_5_llm_coaching_recommendations_v7.md), [6.5_llm_integration_architecture.md](./6.5_llm_integration_architecture.md), [06_6_product_reset_human_validation.md](./06_6_product_reset_human_validation.md)

---

## 1. Resumen ejecutivo

Las specs **07-base** y **07.1** proponen un **cambio de producto coherente** con la conclusión de **6.6**: dejar de optimizar “informes convincentes” y pasar a **diagnóstico del proceso de decisión** apoyado en motor (MultiPV), reglas explicables y validación humana.

**Veredicto general:**

| Dimensión | Valoración |
|-----------|------------|
| Coherencia interna 07 ↔ 07.1 | **Alta** — 07.1 se declara extensión explícita de 07-base |
| Alineación con el diagnóstico de 6.6 | **Muy alta** — responde al mismo “punto de quiebre” pedagógico |
| Compatibilidad con lo implementado en 6.5 | **Parcial** — reutiliza ML/SHAP/features; **sustituye** el núcleo del diagnóstico y el rol del LLM |
| Continuidad del curso (roadmap 07=RAG) | **Conflicto de numeración** — hay que renumerar o bifurcar módulos |
| Viabilidad como siguiente incremento | **Alta como visión**; **baja como un solo salto** desde 6.5 — requiere fases y MVP acotado |

**Recomendación:** tratar 07-base + 07.1 como **nueva línea base de producto** (módulo de curso **7.0 — Decision-process diagnosis**), mantener 6.5 como laboratorio histórico de LLM/V7, y posponer RAG/agentes hasta cumplir criterios de 6.6 **con evidencia engine-backed**.

---

## 2. Qué aporta cada documento

### 2.1 `07_criticals_position_and_candidate_moves_analysis.md` (07-base)

**Tipo:** especificación funcional de **detección y análisis posicional**.

**Pregunta central:**

> ¿Cómo debería haber pensado el jugador en esta posición?

**Bloques principales:**

| Bloque | Contenido |
|--------|-----------|
| Entradas | PGN/FEN, Elo, reloj, análisis Stockfish previo, features ChessInsight, predicción ML |
| Arquitectura | Feature Engine → MultiPV → Critical Position Detector → Static/Dynamic → Candidate Classifier → Decision Failure → Explanation Planner → LLM verbalizer → Critic |
| Criticalidad | Score compuesto (amenazas, divergencia de candidatos, riesgo humano del modelo, etc.) — **no** solo `error_label` |
| Candidatas | MultiPV + checks/captures/profilaxis; tipos Forcing/Defensive/Dynamic/… |
| Secuencias | Suboptimal Sequence Detector (patrones tipo `PlanInconsistency`, `IgnoredThreat`, …) |
| Integración pedagógica | Listas de preguntas estilo Alvira; desequilibrios dinámicos estilo Beim |
| MVP | Fase 1: reglas + MultiPV + explicación **sin LLM**; Fase 3: LLM + validación |

**Alcance:** API REST, contratos C#, casos de prueba, criterios de aceptación AC-01…AC-10.

- Nota 1: Todos los contratos tienen que ser Python.

### 2.2 `07_1_complementary_functional_specification.md` (07.1)

**Tipo:** capa **cognitivo-pedagógica** sobre los resultados de 07-base.

**Pregunta ampliada:** además de la jugada, responde **9 preguntas** (qué exigía la posición, tipo de decisión, factores prioritarios, propósito de candidatas, qué se pasó por alto, tipo de error, secuencia vs jugada aislada, patrón longitudinal, ejercicio concreto).

**Módulos nuevos (respecto a 07-base):**

```text
Position Assessment Engine
Static-Dynamic Evaluator
Decision Requirement Classifier
Candidate Purpose Analyzer
Chess Error Diagnosis Engine
Cognitive Hypothesis Engine
Sequence Interpretation Engine
Player Pattern Engine
Pedagogical Recommendation Engine
Explanation Composer
```

**Principios reforzados:**

- Tipología `FACT | STRONG_INFERENCE | WEAK_INFERENCE | PLAYER_CONFIRMED`
- Abstención conservadora (“Cannot be determined with sufficient confidence”)
- LLM restringido en §16.5 (no inventar variantes, no atribuir pensamientos)
- Esquema SQL completo (`position_assessments`, `decision_diagnoses`, `cognitive_hypotheses`, …)
- UI de confirmación del jugador (§22.4) — alineado con HITL de 6.6
- Métrica clave: **Unsupported Explanation Rate < 5%**

**MVP 07.1 (§25):** 10 factores posicionales, 5 hipótesis cognitivas, 3 candidatas MultiPV, un ejercicio por diagnóstico.

---

## 3. Coherencia interna (07-base ↔ 07.1)

### 3.1 Fortalezas

| Aspecto | Evaluación |
|---------|------------|
| Relación declarada | 07.1 §1 cita explícitamente 07-base como prerequisito |
| Pipeline | 07-base termina en *Explanation Planner + LLM + Critic*; 07.1 detalla **qué** debe contener el plan y el diagnóstico **antes** del verbalizador |
| Hechos vs inferencias | Misma filosofía en §3.1 (07-base) y §4.1 (07.1), con tipología más formal en 07.1 |
| Stockfish | Rol consistente: evalúa, MultiPV, valida — no explica solo |
| Modelo ML | Ambos lo preservan como señal de riesgo/priorización, no como verdad pedagógica |
| Secuencias | 07-base §15 (Suboptimal Sequence Detector) y 07.1 §13 (Sequence Interpretation Engine) son **complementarios** (detección vs interpretación con plan jugado/requerido) |
| Validación humana | 07.1 §22.4 + §24 Fase 3 = mismo espíritu que 6.6 |

### 3.2 Solapamientos (no contradictorios, pero redundantes)

| Tema | 07-base | 07.1 | Nota |
|------|---------|------|------|
| Evaluación estática/dinámica | §8–9 | §8 Static-Dynamic Evaluator | Unificar un solo módulo en implementación |
| Clasificación de candidatas | §13 Candidate types | §10 Candidate Purpose Analyzer | 07.1 es más fino (catálogo de *purposes*) |
| Diagnóstico de error | §16+ Decision Failure | §11 Chess Error Diagnosis Engine | Taxonomías distintas; hay que mapear |
| Patrones jugador | Implícito en Phase 3 MVP | §14 Player Pattern Engine | 07.1 es más completo |
| MVP / fases | §23 MVP (3 fases) | §24 Implementation (5 fases) | **Reconciliar** en un único roadmap de implementación |

### 3.3 Lagunas internas

1. **07-base no referencia 07.1** — la dependencia es unidireccional; conviene añadir en 07-base un § “Extension: decision-process diagnosis (07.1)”.
   - Nota 2: OK, añadir esa referencia cruzada.
  
2. **Contratos duplicados** — 07-base usa interfaces C# al final; 07.1 usa Python dataclasses + SQL. Hay que elegir **capa canónica del curso** (Python en `docs/ai_chess_coach_course/`).
   - Nota 3: Repito Nota 1: Usar contratos Python.
- 
3. **Critical Position (07)** vs **Critical Move (6.5)** — no hay tabla de mapeo entre “posición crítica” (pre-jugada) y “momento crítico del alumno” (post-jugada con `error_label`).
   - Nota 4: Diseñar modelo de tablas acorde.
- 
4. **Profundidad Stockfish** — 07 exige MultiPV depth 15+ en runtime; el curso 6.5 **excluye** Stockfish en coaching time — hay que decidir si 7.0 es **offline batch** (aceptable) o online.
   - **Nota 5:** Reutilizar el criterio ya usado para `error_label` (features Stockfish precomputados en SQLite/parquet) y completar con **análisis batch** previo al coaching — no en vivo.
   - **Nota 5.1:** Ver análisis completo en [§9.1 — Dual-engine Stockfish + Leela Zero](#91-nota-51--análisis-dual-engine-stockfish--leela-zero).
  
---

## 4. Coherencia con specs 06*

### 4.1 Matriz de alineación

| Concepto | 6.5 (implementado) | 6.6 (diseño) | 07-base / 07.1 | Relación |
|----------|-------------------|--------------|----------------|----------|
| **Objetivo** | Informe V7 por partida | Auditar utilidad pedagógica | Diagnóstico de decisión + entrenamiento | 07 **implementa** la respuesta a 6.6 |
| **Selección de momentos** | `error_label` + RCA walkback | Revisión humana de casos | Criticality score + MultiPV + ML risk | **Cambio de criterio** — 07 más estratégico |
| **Diagnóstico** | DiagnosisBuilder (tags, board, SHAP phrases) | Validar `issue`/tema | Position Assessment + Error taxonomy + hypotheses | **Sustitución progresiva** del builder actual |
| **Secuencias** | RCA incident clustering | Secuencias en review pack | Suboptimal + Sequence Interpretation | **Objetivos similares**, métodos más ricos en 07 |
| **Candidatas** | No (solo `opponent_reply` táctico) | — | MultiPV + purpose analysis + comparación | **Gap grande en 6.5** — 07 lo cubre |
| **LLM** | Narra V7 desde JSON | No decide; humano valida | Solo Explanation Composer / verbalizer | **Convergencia** — 07 es más estricto |
| **Stockfish** | Explícitamente fuera de scope 6.5 | — | Core del análisis | **Tensión principal** con arquitectura 6.5 |
| **Leela Zero** | No contemplado | — | Análisis estratégico en posiciones críticas (Nota 5.1) | **Extensión** post-detector; comparador dual-engine |
| **Patrones longitudinales** | Phase B perfil (8 juegos) | MVP 100+ partidas | Player Pattern Engine (≥3 ocurrencias) | **Continuidad** con 6.6 §6.6.7 |
| **Validación** | `coaching_validation` (formato) | `coach_review` JSONL | PLAYER_CONFIRMED + métricas UER | **Complementarias** |
| **Idioma** | Español obligatorio | Español | Inglés en specs | Adaptar en capa de curso |

***Glosario:***

RCA = Root Cause Analysis (análisis de causa raíz).
Walkback = “retroceder” en la partida unas jugadas desde un error visible (el síntoma) para localizar el primer error del jugador que lo provocó.

### 4.2 Lo que 07 explica de las insatisfacciones con 6.5

Los resultados LLM de 6.5 (V7) pueden ser **sintácticamente válidos** y **pedagógicamente falsos** porque:

| Causa en 6.5 | Cómo lo aborda 07 |
|--------------|-------------------|
| Diagnóstico desde tags SQLite ruidosos | Amenazas/candidatas verificadas con Stockfish + reglas |
| Sin comparación de planes alternativos | Candidate Purpose Analyzer + comparación jugada vs top-3 |
| Sin “qué exigía la posición” | Decision Requirement Classifier + `position_character` |
| Evaluación solo táctica (SF) | Leela Zero en críticas + comparador SF/Lc0 (Nota 5.1, §9.1) |
| Errores tácticos genéricos (`tactical_oversight`) | Taxonomía fina (PROPHYLACTIC_ERROR, DYNAMIC_ERROR, …) |
| LLM rellena con texto persuasivo | LLM solo verbaliza; métrica Unsupported Explanation Rate |
| Una partida = lista de errores | Secuencias + patrón longitudinal + ejercicio tipado |

**Conclusión:** la insatisfacción con 6.5 no invalida el curso 0–6 (ML, SHAP, features); invalida usar **solo** el stack 6.5 como producto final.

### 4.3 Tensiones que hay que resolver explícitamente

#### A. Numeración del curso

- Roadmap actual: **Módulo 7 = RAG**, **6.5 = LLM coaching**.
- Nuevos docs: prefijo **07_** pero contenido = **motor de decisión**, no RAG.

**Propuesta de nomenclatura:**

| Módulo | Contenido |
|--------|-----------|
| 6.5 | LLM coaching (legacy / laboratorio) |
| 6.6 | Human validation & product reset |
| **7.0** | Critical positions + candidates (07-base MVP) |
| **7.1** | Decision-process diagnosis (07.1 MVP) |
| 7.2 (antes “7 RAG”) | RAG — solo tras gate 6.6 |

#### B. Stockfish en el curso

- 6.5: “no Stockfish at coaching time”.
- 07: Stockfish MultiPV **obligatorio** en el pipeline de diagnóstico.

**Resolución:** separar **batch analysis job** (Module 7.0, precalcula `critical_positions` + MultiPV en SQLite) de **coaching narrative** (puede seguir sin LLM en vivo). No contradice 6.5 si 7.0 es una **capa nueva offline**. Leela Zero entra en una **segunda pasada batch** solo sobre posiciones críticas (§9.1).

- Nota 6: Aplicar resolución sugerida separar **batch analysis job**

#### C. Taxonomías paralelas

| 6.5 V6 `diagnosis_type` | 07 `primary_decision_type` | 07 `primary_error` |
|-------------------------|----------------------------|---------------------|
| tactical | TACTICAL | TACTICAL_ERROR |
| opening | OPENING | OPENING_ERROR |
| positional | STRATEGIC / STATIC | STRATEGIC_ERROR / STATIC_ERROR |
| endgame | ENDGAME / TECHNICAL | ENDGAME_ERROR / TECHNICAL_ERROR |
| — | PROPHYLACTIC | PROPHYLACTIC_ERROR |
| — | DYNAMIC | DYNAMIC_ERROR |
| — | PRACTICAL | PRACTICAL_ERROR |

Hace falta un **mapping table** en implementación; no son incompatibles, pero duplicar confunde al LLM si se envían ambos sin merge.

#### D. Alcance producción vs curso

07-base incluye API REST, C#, UI mockups — el curso históricamente usa **notebooks + paquetes Python** en `docs/ai_chess_coach_course/`.

**Recomendación:** extraer de 07 un **MVP de curso** (3–5 notebooks) y dejar API/UI para módulo 12/capstone.

---

## 5. Evaluación de calidad de las specs 07

### 5.1 Fortalezas

- Principios de ingeniería sólidos (evidencia, confianza, abstención, no psicologizar).
- MVP acotados en ambos documentos.
- Golden tests y métricas pedagógicas (Coach Agreement Rate, UER).
- Alineación con literatura ajedrecística (Alvira, Beim) traducida a reglas.
- Esquema de datos pensado para HITL y ML supervisado posterior (Fase 4 solo con labels confirmados).

### 5.2 Riesgos / debilidades

| Riesgo | Detalle | Comentario |
|--------|---------|------------|
| **Complejidad** | ~30 módulos funcionales + 7 tablas SQL — muy por encima de lo 
implementable en un solo sprint | Nota 7: ver [06x_07x_roadmap_modules_and_tasks.md](./06x_07x_roadmap_modules_and_tasks.md) |
| **Reglas frágiles** | Muchas heurísticas IF/THEN; sin golden tests reales aún | - Nota 8: Agregar unit tests |
| **Coste compute** | MultiPV depth 15+ en todas las posiciones de N partidas | - Nota 9: se hará batch o solo a pedido de un conjuntos reducir de movidas |
| **Duplicación con features existentes** | `self_mobility`, `king_safety` en parquet vs `Position Assessment Engine` | - Nota 10: Sugerir unificaciones |
| **Idioma** | Specs en inglés; curso y V7 en español | Ok |
| **Gap engine integration** | El repo tiene features precomputados; MultiPV en vivo no está en el paquete `coaching/` actual | Nota 11: No en vivo; batch a demanda (Nota 9). Lc0 opcional fase 7.0d (§9.1) |

---

## 6. Propuesta de encaje en el curso

### 6.1 Qué conservar de 6.5

- Paquete `llm/` y patrón provider-agnostic.
- `coaching_validation` como capa de **formato**.
- Notebooks 6.5 como **contraste negativo** (experimento C en 6.6).
- `game_timeline`, `pgn_context`, splits por `game_id`.

### 6.2 Qué reemplazar o subordinar

- `DiagnosisBuilder` como fuente **primaria** de verdad → pasar a señal secundaria hasta validar tags.
- `lesson_synthesizer` + informe V7 como output principal → sustituir por **Explanation Composer** alimentado por 07.1 DTOs.
- Selección de momentos solo por `error_label` → **Critical Position Detector** + errores confirmados.

### 6.3 Roadmap de implementación sugerido (curso)

```text
[Fase 0 — ya hecho] 0–6.6 notebooks
[Fase 1 — 7.0a] Stockfish MultiPV wrapper + position extractor (1 posición manual)
[Fase 1 — 7.0b] Criticality scorer (3–5 reglas del MVP 07-base)
[Fase 1 — 7.0c] Candidate comparison vs jugada (sin LLM)
[Fase 1 — 7.0d] Leela Zero MultiPV solo en posiciones críticas + Engine Comparison (Nota 5.1)
[Fase 2 — 7.1a] Position Assessment (10 factores MVP) + decision_type
[Fase 2 — 7.1b] Chess Error Diagnosis + 2 hipótesis cognitivas
[Fase 2 — 7.1c] Explanation Composer + LLM (mismas reglas §16.5)
[Fase 3] Integrar 6.6 HITL → PLAYER_CONFIRMED en DB
[Fase 4] Player Pattern Engine (≥3 partidas)
[Fase 5] RAG (antiguo módulo 7) — solo si UER y coach agreement OK
```

### 6.4 Notebooks propuestos

| Notebook | Objetivo |
|----------|----------|
| `07_0_critical_position_lab.ipynb` | Una FEN/partida: MultiPV, criticality, candidatas — sin ML ni LLM |
| `07_1_decision_diagnosis.ipynb` | Pipeline 07.1 MVP en 1 posición crítica |
| `07_2_sequence_and_patterns.ipynb` | Secuencia subóptima + agregación en 3+ partidas |
| `07_3_explanation_and_hitl.ipynb` | Explanation Composer + plantilla `coach_review` / `PLAYER_CONFIRMED` |
| *(opcional)* `07_4_batch_game_analysis.ipynb` | Partida completa: todas las posiciones críticas |

Generador sugerido: `_gen_decision_diagnosis_nb.py` (mismo patrón que 6.5).

---

## 7. Conclusiones

1. **Las specs 07 responden directamente** a la crítica válida del stack 6.5: falta de candidatas, de “qué exigía la posición”, de verificación engine-backed y de separación evidencia/narrativa.

2. **07-base y 07.1 son coherentes entre sí**; 07.1 es la extensión natural que 6.6 pedía implícitamente (diagnóstico de jugador, no de JSON).

3. **No hay contradicción lógica con 6.6**; hay **sustitución de producto** respecto a 6.5 como MVP final.

4. **Sí hay conflictos operativos** con la arquitectura 6.5 (Stockfish, numeración módulo 7, taxonomías duplicadas) — resolubles con batch analysis + renumeración.

5. **Implementación recomendada:** MVP 7.0 en notebook **sin LLM**, reutilizando ML solo como `humanErrorRiskScore`; añadir LLM solo en Explanation Composer con métrica UER y gate 6.6.

6. **No avanzar a RAG/agentes** hasta tener golden tests + validación humana sobre el pipeline 07 — coherente con 6.6 §Expected Outcome y 07.1 §24 Fase 3.

7. **Nota 5.1 (Leela Zero):** aprobar como extensión **7.0d** — segundo motor solo en posiciones críticas, con comparador estructurado SF/Lc0 antes de activar el LLM en Explanation Composer (detalle en §9.1).

---

## 8. Acciones documentales sugeridas (siguiente paso)

| # | Acción |
|---|--------|
| 1 | Renombrar en roadmap: 7.0/7.1 (decision diagnosis) vs 7.2 (RAG) |
| 2 | Añadir en 07-base un § de referencia a 07.1 y a 6.6 |
| 3 | Crear `07_mapping_06_to_07_taxonomies.md` (tabla diagnosis_type ↔ decision_type ↔ error) |
| 4 | Definir MVP único fusionando §23 (07-base) y §25 (07.1) |
| 5 | Implementar `07_0_critical_position_lab.ipynb` como primer entregable del curso |
| 6 | Documentar extensión dual-engine en 07-base (§5.3 bis) y contrato `EngineComparisonResult` |
| 7 | Añadir `LC0_PATH` / weights a `.env.example` del curso cuando exista wrapper |

---

## 9. Notas de diseño — análisis ampliado

Esta sección desarrolla decisiones marcadas inline (Notas 1–11) y propuestas pendientes de spec.

### 9.1 Nota 5.1 — Análisis dual-engine (Stockfish + Leela Zero)

**Propuesta (Nota 5.1):** en batch, primer barrido con Stockfish sobre todas las jugadas (o reutilizar features existentes); cuando el **Critical Position Detector** esté operativo, ejecutar **Leela Zero (lc0)** solo sobre posiciones críticas para análisis estratégico; el módulo debe **comparar ambos análisis** y exponer el resultado estructurado.

#### 9.1.1 Por qué tiene sentido en el marco 07

Las specs 07 piden ir más allá del “mejor movimiento táctico” hacia **qué exigía la posición** (Static-Dynamic Evaluator, Decision Requirement Classifier, Candidate Purpose Analyzer). Stockfish es fuerte en:

- evaluación en centipeones y líneas forzadas;
- detección de errores (`error_label`, `score_diff`) — ya integrado en el curso 0–6;
- amenazas inmediatas y profundidad de cálculo.

Leela Zero aporta un perfil distinto (red neuronal, entrenamiento por self-play):

- prioriza **planes a largo plazo** y estructuras cerradas donde SF puede sobreponderar táctica local;
- expone **política de movimientos** (visit counts / WDL) útil cuando varias jugadas tienen eval similar pero **distinto carácter** (consolidar vs transformar);
- en posiciones con **compensación dinámica** (Beim §12 en 07-base), puede reforzar el diagnóstico “estático peor pero acción dinámica requerida” sin depender solo de heurísticas IF/THEN.

En el repo ya existen partidas de referencia **Stockfish vs Lc0** (Postman env `Chess_SHAP_Local`, juegos ELO alto), lo que encaja con validar el comparador dual-engine en posiciones de alta calidad estratégica antes de escalar a partidas de alumno.

#### 9.1.2 Coherencia con specs 07 y 06*

| Aspecto | Stockfish (paso 1) | Leela Zero (paso 2, solo críticas) | Coherencia |
|---------|-------------------|-------------------------------------|------------|
| Alcance | Todas las jugadas / features existentes | Subconjunto `critical == true` | Alineado con Nota 9 (batch acotado) |
| Rol en 07-base | §5.3 MultiPV Analyzer — fuente principal de candidatas | No mencionado en 07-base | **Extensión** de spec, no contradicción |
| `error_label` / severidad | Fuente de verdad actual (SQLite) | Complemento estratégico | 6.5 no se invalida; Lc0 no redefine blunder |
| Static-Dynamic (07.1 §8) | Reglas + eval cp | Señal de “plan preferido” cuando evals convergen | Refuerza evaluador estático/dinámico |
| `CandidateDivergence` (07-base §7.2) | Top MultiPV SF | Discrepancia SF top-1 vs Lc0 top-1 | Nuevo input de criticality |
| Explanation Composer | Evidencia FACT | Solo FACT si ambos motores coinciden; si no, `STRONG_INFERENCE` o abstención | Reduce UER (meta 07.1) |
| 6.5 DiagnosisBuilder | Tags + SHAP | Señal secundaria; no sustituye tags hasta validar | Subordinación coherente con §6.2 |

**Conclusión:** Nota 5.1 **cierra un gap** de las specs 07 (orientación estratégica) sin romper el pipeline 06* ni el principio “motor evalúa, LLM verbaliza”.

#### 9.1.3 Pipeline propuesto (batch, dos fases)

```text
PGN / timeline (course_data.sqlite)
    ↓
[Pasada A — Stockfish]  reutilizar score_diff + error_label existentes
                        o MultiPV batch depth 15+ si faltan candidatas
    ↓
Critical Position Detector (07-base §7)
    ↓
[Pasada B — Leela Zero]  MultiPV 3–5, solo FENs con criticality ≥ Relevant
    ↓
Engine Comparison Module
    ↓
Position Assessment / Static-Dynamic / Candidate Purpose (07.1)
    ↓
Explanation Composer → LLM (opcional)
```

**Regla de coste:** Lc0 **nunca** analiza la partida completa en MVP; solo posiciones que pasaron el detector (típicamente 4–12 por partida vs ~40–80 jugadas).

#### 9.1.4 Contrato sugerido — `EngineComparisonResult`

Contrato Python (coherente con Notas 1 y 3):

```python
@dataclass
class EngineCandidate:
    engine: Literal["stockfish", "lc0"]
    rank: int
    uci: str
    san: str
    eval_cp: float | None          # SF; normalizado desde WDL en Lc0
    wdl: tuple[float, float, float] | None  # Lc0
    visit_ratio: float | None      # Lc0 policy mass
    pv_san: list[str]

@dataclass
class EngineComparisonResult:
    fen: str
    move_number: int
    criticality_score: float
    stockfish_top: EngineCandidate
    lc0_top: EngineCandidate
    top_move_agreement: bool       # mismo UCI en rank 1
    eval_gap_cp: float             # |eval_sf - eval_lc0_normalizado|
    plan_divergence: bool          # distinto candidate_type / purpose
    strategic_signal: Literal[
        "AGREE_TACTICAL",
        "AGREE_STRATEGIC",
        "SF_TACTICAL_LC0_STRATEGIC",
        "SF_STRATEGIC_LC0_TACTICAL",
        "DISAGREE_EVAL",
        "INSUFFICIENT_NODES",
    ]
    confidence: Literal["FACT", "STRONG_INFERENCE", "WEAK_INFERENCE"]
    notes: list[str]               # evidencia verificable para Explanation Composer
```

**Uso pedagógico:**

| `strategic_signal` | Interpretación para el coach |
|--------------------|------------------------------|
| `AGREE_*` | “Ambos motores apuntan a la misma idea” → FACT en texto |
| `SF_TACTICAL_LC0_STRATEGIC` | “La jugada correcta táctica no es la que consolida el plan” → candidata dinámica / transformación |
| `DISAGREE_EVAL` | Abstención o pregunta al jugador (HITL 6.6); no afirmar plan único |

#### 9.1.5 Integración con módulos 07.1

| Módulo 07.1 | Input desde comparador dual |
|-------------|----------------------------|
| Static-Dynamic Evaluator | `plan_divergence` + evals → `requiresDynamicAction` |
| Decision Requirement Classifier | Discrepancia SF/Lc0 → `DYNAMIC` vs `STATIC` vs `TACTICAL` |
| Candidate Purpose Analyzer | Top-3 SF enriquecido con visit_ratio Lc0 por la misma UCI |
| Cognitive Hypothesis Engine | “Over-fitting táctico local” si jugador sigue SF-like move pero Lc0 prefiere plan largo — solo `WEAK_INFERENCE` |
| Explanation Composer | Solo incluir frases de plan si `confidence != WEAK_INFERENCE` o hay `PLAYER_CONFIRMED` |

#### 9.1.6 Riesgos y mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| **Coste compute** Lc0 >> SF en CPU | Solo posiciones críticas; cache por FEN; nodos fijos (p. ej. 800–1600) en lugar de depth 15+ |
| **Escalas distintas** (cp vs WDL) | Capa de normalización; nunca mezclar cp crudos en reglas sin conversión |
| **Desacuerdo ≠ error del alumno** | Comparador informa **divergencia de planes**, no culpa; severidad sigue viniendo de `error_label` (SF) |
| **Lc0 no instalado en curso** | Wrapper opcional; fallback a SF-only con flag `dual_engine_available: false` |
| **Specs 07-base solo citan SF** | Añadir §5.3 bis “Strategic Engine (Leela Zero)” y AC-11 “dual analysis on critical positions when configured” |
| **Golden tests** | Casos SF vs Lc0 conocidos (partidas engine-engine del repo) antes de partidas de alumno |

#### 9.1.7 Veredicto sobre Nota 5.1

| Criterio | Valoración |
|----------|------------|
| Coherencia con 07-base / 07.1 | **Alta** — refuerza static/dynamic y candidate purpose |
| Coherencia con 6.5 / 6.6 | **Alta** — batch offline; HITL cuando motores discrepan |
| Complejidad añadida | **Media** — un wrapper + comparador; no requiere reescribir 6.5 |
| Prioridad MVP | **Después de 7.0b** (detector crítico) y **antes de 7.1c** (LLM) |
| Recomendación | **Aprobar como Fase 7.0d**; no bloquear MVP 7.0a–c si Lc0 no está disponible |

#### 9.1.8 Dependencias de implementación (curso)

```text
docs/ai_chess_coach_course/
├── engines/
│   ├── stockfish_wrapper.py      # UCI MultiPV (7.0a)
│   ├── lc0_wrapper.py            # UCI + WDL (7.0d)
│   └── engine_comparison.py      # EngineComparisonResult (7.0d)
├── artifacts/module07/
│   └── engine_comparison/        # JSON por FEN crítica
└── .env.example                  # STOCKFISH_PATH, LC0_PATH, LC0_WEIGHTS
```

Variables de entorno sugeridas: `LC0_PATH`, `LC0_WEIGHTS` (red `.pb.gz`), `LC0_NODES` (default 800), `ENABLE_LC0_STRATEGIC=0|1`.

---

### 9.2 Resumen de notas inline (1–11)

| Nota | Decisión |
|------|----------|
| 1 | Contratos canónicos en **Python** (no C#) |
| 2 | Referencia cruzada 07-base → 07.1 |
| 3 | = Nota 1 |
| 4 | Diseñar modelo de tablas critical_position ↔ critical_move |
| 5 | Batch offline; reutilizar pipeline `error_label` |
| 5.1 | Dual-engine SF + Lc0 en críticas — ver §9.1 |
| 6 | Separar batch analysis job vs coaching narrative |
| 7 | Documento aparte: listado de módulos y tareas por sprint | **[06x_07x_roadmap_modules_and_tasks.md](./06x_07x_roadmap_modules_and_tasks.md)** |
| 8 | Unit tests + golden tests por módulo |
| 9 | Batch o subconjunto reducido de jugadas |
| 10 | Unificar features parquet con Position Assessment Engine |
| 11 | Sin análisis en vivo; bajo demanda / batch |

---

## Referencias cruzadas

| Documento | Rol después de este informe |
|-----------|----------------------------|
| [06_6_product_reset_human_validation.md](./06_6_product_reset_human_validation.md) | Gate y HITL — prerequisito cultural antes de escalar 07 |
| [6.5_llm_integration_architecture.md](./6.5_llm_integration_architecture.md) | Arquitectura legacy LLM; verbalizer reutilizable |
| [00-ai_enginner_course_roadmap.md](./00-ai_enginner_course_roadmap.md) | Actualizar tramo 7.x según §6.1 de este informe |
