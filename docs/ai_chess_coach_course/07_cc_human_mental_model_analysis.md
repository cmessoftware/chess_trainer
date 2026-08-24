# Análisis — Modelo mental humano (1600 rapid) vs specs 07*

> **Alcance de este documento:** análisis de coherencia de los HTML en `07_cc_detection_algoritms/` frente a 07*.  
> **Nota:** la implementación Python en `analysis/mental_model/` se añadió como borrador ejecutable *después* del análisis; la **especificación canónica humana** sigue siendo el HTML. Para probar: notebook [`07_0_mental_model_lab.ipynb`](./07_0_mental_model_lab.ipynb).
> **Artefactos fuente:** [07_cc_detection_algoritms/](./07_cc_detection_algoritms/)  
> **Specs:** [07_criticals_position_and_candidate_moves_analysis.md](./07_criticals_position_and_candidate_moves_analysis.md) · [07_1_complementary_functional_specification.md](./07_1_complementary_functional_specification.md)  
> **Roadmap curso:** [06x_07x_roadmap_modules_and_tasks.md](./06x_07x_roadmap_modules_and_tasks.md)  
> **Implementación parcial:** `analysis/mental_model/` (Módulo 7.0 — capa humana prioritaria)

---

## 1. Resumen ejecutivo

Los diagramas HTML definen un **proceso de decisión para humanos** (~1600 rapid chess.com), no un motor. Encajan con el espíritu de 07* (“¿cómo debería haber pensado el jugador?”) y **complementan** la spec 07-base, que está orientada a infraestructura (Stockfish MultiPV, scores compuestos, API).

**Decisión de prioridad:**

| Capa | Rol | Prioridad |
|------|-----|-----------|
| **Modelo mental 1600** (tus algoritmos) | Qué pensar, en qué orden, cuánto tiempo | **Primaria pedagógica** |
| **Verificación 07-base** | Stockfish MultiPV, features, ML risk | **Primaria técnica** |
| **07.1** | Diagnóstico, abstención, HITL, Explanation Composer | **Capa de producto** |
| **LLM** | Verbalizar plan estructurado | **Solo narrativa** |

Tus algoritmos **no reemplazan** Stockfish; definen el **árbol de decisión** que el producto debe enseñar y simular. La implementación programática valida disparadores con tablero/features y reserva MultiPV para candidatas y comparación.

---

## 2. Inventario de los algoritmos HTML

### 2.1 Posiciones críticas (`algoritmo_posiciones_criticas_ajedrez.html`)

Flujo en 4 fases:

```text
[Fase 1 — ¿Es crítica?]
  A rival mueve → B ¿cambió algo importante?
    No  → C modo rápido → C1 ¿jugada natural segura? → Sí → Z JUGAR
    Sí  → D modo crítico → E disparadores (E1–E11) → F pausa temporal

[Fase 2 — Actualizar posición]
  G → G1 amenaza real / G2 qué cambió / G3 atacado-indefenso / G4 líneas

[Fase 3 — Candidatas y cálculo]
  H generar (H1–H6) → I 2–3 candidatas → J material gratis?
    → M–O calcular (candidata → respuesta rival → mi respuesta, loop táctico)
    → Q–R comparar → T elegir sólida O S anti-blunder

[Fase 4 — Anti-blunder]
  S1 dama/torre en prise → S2 jaque contra mí → S3 captura obvia → S4 pierdo defensor → Z
```

**Disparadores E1–E11 (nivel amateur explícito):**

| ID | Disparador humano |
|----|-------------------|
| E1 | Material aparentemente gratis / en prise |
| E2 | Jaque, captura o amenaza directa |
| E3 | Jugada inesperada del rival |
| E4 | Avance de peón con tempo sobre pieza |
| E5 | Se abre/cierra columna, diagonal o fila |
| E6 | Cambio importante de estructura de peones |
| E7 | Ataque al rey / enroques opuestos |
| E8 | Pieza atrapada, sobrecargada o sin defensor |
| E9 | Jugada irreversible (avance, sacrificio, cambio) |
| E10 | Varias candidatas razonables |
| E11 | Evaluación intuitiva: tranquilo ↔ táctico |

**Pausa F:** 5 / 10 / 30 s según ritmo — **específico para rapid 1600**, ausente en 07-base.

### 2.2 Jugadas candidatas (`algoritmo_jugadas_candidatas_chessinsight.html`)

Flujo más compacto (entrada: posición ya crítica):

```text
A crítica → B actualizar modelo → C qué quiere el rival
→ D generar (D1 forzantes … D5 posicionales)
→ E reducir a 2–3 → F ordenar (forzante → activa → sólida)
→ G calcular (C1, respuesta rival, continuación)
→ H ¿línea forzada? → I evaluar (rey, material, actividad, estructura, iniciativa/práctica)
→ J comparar → K elegir + anti-blunder
```

---

## 3. Coherencia con 07-base y 07.1

### 3.1 Alineaciones fuertes

| Tu algoritmo | Spec 07 | Relación |
|--------------|---------|----------|
| G1–G4 (preguntas posición) | 07-base §11 Alvira | Misma intención |
| H1–H6 / D1–D5 | 07-base §13 Candidate types | Subconjunto pedagógico más simple |
| I1–I5 evaluación | 07.1 Position Assessment (10 factores) | 5 factores MVP alineados |
| S1–S4 anti-blunder | 07.1 abstención + validación | Crítico para 1600 |
| E10 varias candidatas | `CandidateDivergence` | Directo |
| F tiempo de reflexión | 07.1 Elo + time control | Falta en 07-base; tú lo tienes |
| C / C1 modo rápido | — | **Aporte nuevo** — evita sobre-análisis |

### 3.2 Gaps del modelo humano (cubiertos por 07*, no duplicar)

| Gap | Quién lo cubre |
|-----|----------------|
| Variantes exactas y eval cp | Stockfish MultiPV (07-base §5.3) |
| Score numérico de criticality | 07-base §7.3 |
| Static vs dynamic formal | 07.1 §8 Static-Dynamic Evaluator |
| Secuencias subóptimas multi-jugada | 07-base §15 + 07.1 §13 |
| ML `humanErrorRiskScore` | Modelo 04/05 |
| Confianza FACT / INFERENCE | 07.1 §4.1 |
| Lc0 estratégico | Informe coherencia §9.1 |

### 3.3 Tensiones y resolución

| Tension | Resolución propuesta |
|---------|---------------------|
| 07-base lista 12 `CriticalityReason` en inglés; tú tienes E1–E11 en español | Tabla de mapeo en `analysis/mental_model/mapping_07.py` |
| 07-base asume MultiPV antes del diagnóstico; tú generas candidatas mentalmente | Pipeline: **disparadores humanos → activar MultiPV → clasificar PV en D1–D5** |
| 07 MVP solo 5 detectores | **Ampliar MVP a E1–E11** mapeados, priorizando los detectables sin motor |
| Specs en inglés, algoritmo en español | Capa curso/API en español; enums internos bilingües |

### 3.4 Veredicto de coherencia

| Dimensión | Valoración |
|-----------|------------|
| Coherencia conceptual con 07* | **Alta** |
| ¿Contradice 07-base? | **No** — la refina hacia jugador amateur |
| ¿Priorizable sobre reglas genéricas 07 MVP? | **Sí**, como **capa pedagógica canónica** |
| ¿Suficiente solo para producto? | **No** — requiere anclaje Stockfish + HITL |

---

## 4. Mapeo E1–E11 → CriticalityReason (07-base)

| Humano | 07-base | Detección programática (MVP) |
|--------|---------|------------------------------|
| E1 | TacticalThreat + material | piezas en prise (python-chess) |
| E2 | TacticalThreat / ForcedSequence | jaques, capturas legales |
| E3 | EvaluationInstability | \|Δ score_diff\| > umbral o sorpresa SAN |
| E4 | TacticalThreat | peón ataca pieza con tempo |
| E5 | StructuralTransformation | apertura/cierre de línea (peón/torre) |
| E6 | StructuralTransformation / PawnBreakAvailable | cambio estructura peones |
| E7 | KingSafetyChange | features king_safety / ataque al rey |
| E8 | TacticalThreat | pin, pieza sin defensor (detectors 6.5) |
| E9 | IrreversiblePawnMove / MaterialTransformation | peón avanza, captura mayor |
| E10 | CandidateDivergence | MultiPV top-3 distinto plan (motor) |
| E11 | EvaluationInstability | \|score_diff\| + forcing count |

**Modo rápido (C1):** si `triggers == []` y `|Δeval| < umbral_1600` → `Routine`, sugerir jugada natural (no activar batch Stockfish).

---

## 5. Mapeo candidatas H/D → 07-base §13

| Humano | 07-base type | Orden F (prioridad cálculo) |
|--------|--------------|----------------------------|
| H1 / D1 Forzantes (jaques, capturas) | Forcing | 1 |
| H2 / D2 Capturas / amenazas | Tactical | 2 |
| H3 / D3 Activas / ruptura | Dynamic | 3 |
| H4 / D4 Defensa / profiláctica | Defensive / Prophylactic | 4 |
| H5 Actividad / iniciativa | Dynamic / Improving | 3 |
| H6 / D5 Posicional | Positional / Consolidating | 5 |

Regla **F:** forzante → activa → sólida — implementar como sort key post-MultiPV.

---

## 6. Arquitectura objetivo (curso → web)

```text
                    ┌─────────────────────────────────────┐
                    │  Web UI (M12) / Notebook 7.0        │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │  FastAPI POST /api/analysis/position  │
                    └─────────────────┬───────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         │                            │                            │
         ▼                            ▼                            ▼
┌─────────────────┐      ┌──────────────────────┐      ┌─────────────────┐
│ mental_model    │      │ engines/ (SF MultiPV) │      │ ML risk (04/05) │
│ (PRIORIDAD)     │      │ verificación          │      │ priorización    │
│ E1-E11, H/D, S  │      │ candidatas + eval     │      │                 │
└────────┬────────┘      └──────────┬───────────┘      └────────┬────────┘
         │                            │                            │
         └────────────────────────────┼────────────────────────────┘
                                      ▼
                    ┌─────────────────────────────────────┐
                    │  PostgreSQL: critical_positions,      │
                    │  decision_traces, coach_review        │
                    └─────────────────┬───────────────────┘
                                      ▼
                    ┌─────────────────────────────────────┐
                    │  Explanation Composer + LLM (07.1)    │
                    └─────────────────────────────────────┘
```

**PostgreSQL (futuro):** persistir traza del árbol mental (`node_id`, `triggered`, `notes`) + resultado verificado — alimenta HITL y ML supervisado.

---

## 7. Implementación parcial en el curso (hecho / planificado)

### 7.0-human — Capa mental 1600 (prioritaria sobre 7.0b genérico)

| ID | Entregable | Estado |
|----|------------|--------|
| 7.0-H01 | `analysis/mental_model/models.py` — enums E1–E11, D1–D5, S1–S4 | ✅ |
| 7.0-H02 | `critical_triggers.py` — reglas tablero + features | ✅ MVP |
| 7.0-H03 | `anti_blunder.py` — chequeos S1–S4 | ✅ |
| 7.0-H04 | `candidate_taxonomy.py` — clasificar UCI en D1–D5 | ✅ |
| 7.0-H05 | `flow.py` — `assess_decision_point()` | ✅ |
| 7.0-H06 | `mapping_07.py` — mapa a CriticalityReason | ✅ |
| 7.0-H07 | Tests `test_mental_model_1600.py` | ✅ |
| 7.0-H08 | Notebook `07_0_mental_model_lab.ipynb` | ⬜ siguiente |
| 7.0-H09 | Integrar con Stockfish wrapper (7.0-T01) | ⬜ |

### Uso en código

```python
from analysis.mental_model.flow import assess_decision_point

result = assess_decision_point(
    fen="...",
    last_move_uci="e2e4",
    time_control="rapid",  # 10+0 → pausa 10s sugerida
    player_elo=1600,
    score_diff_before=-20,
    score_diff_after=80,
)
# result.mode: "fast" | "critical"
# result.triggers: [HumanTrigger(E2, ...), ...]
# result.thinking_plan: pasos G, H, S para UI/LLM
```

---

## 8. Roadmap revisado — prioridad modelo humano

Insertar **antes** de 7.0-T08 (criticality scorer genérico):

```text
7.0-H (human)  mental_model E1-E11 + anti-blunder + fast path
7.0-T08        criticalityScore = human triggers + 07 weights + ML
7.0-T09        detectores 07 MVP validados contra E1-E11
7.0-T15        candidatas: MultiPV clasificadas D1-D5 + orden F
```

Los 5 detectores genéricos del MVP 07-base pasan a ser **validación backend**, no la UX pedagógica.

---

## 9. Aplicación Web + FastAPI + PostgreSQL + LLM

| Componente | Función con modelo humano |
|------------|---------------------------|
| **React / Streamlit** | Renderizar árbol interactivo (HTML existente → componente); marcar nodos = traza HITL |
| **FastAPI** | `POST /positions/{id}/assess` → JSON `DecisionAssessment` |
| **PostgreSQL** | `mental_traces(jsonb)`, `critical_positions`, enlazar con `features` |
| **LLM** | Input: `thinking_plan` + MultiPV + `PLAYER_CONFIRMED`; output: texto estilo coach 1600 |
| **Batch** | Solo posiciones `mode=critical` → Stockfish depth 15+ |

Endpoints sugeridos:

```http
POST /api/v1/positions/assess     # FEN + context → mental model + triggers
POST /api/v1/positions/candidates # activa MultiPV si critical
POST /api/v1/games/{id}/trace     # partida completa batch
POST /api/v1/explanations/compose # 07.1 + LLM
```

---

## 10. Próximos pasos recomendados

1. Validar E1–E11 con **10 posiciones reales** tuyas (rapid 1600) — marcar en HTML, exportar JSON, comparar con `assess_decision_point()`.
2. Notebook `07_0_mental_model_lab.ipynb`: una FEN → triggers → (cuando exista) MultiPV → comparación jugada.
3. Actualizar §7 Critical Position Detector en 07-base con referencia a este modelo como **fuente pedagógica primaria**.
4. Gate 6.6: usar traza mental en review pack (“¿el coach enseñó este árbol?”).

---

## Referencias

| Artefacto | Ruta |
|-----------|------|
| Diagrama posiciones críticas | [algoritmo_posiciones_criticas_ajedrez.html](./07_cc_detection_algoritms/algoritmo_posiciones_criticas_ajedrez.html) |
| Diagrama candidatas | [algoritmo_jugadas_candidatas_chessinsight.html](./07_cc_detection_algoritms/algoritmo_jugadas_candidatas_chessinsight.html) |
| Código capa humana | [analysis/mental_model/](./analysis/mental_model/) |
