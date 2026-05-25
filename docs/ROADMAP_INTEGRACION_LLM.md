# ChessTrainer — Reporte LLM ajustado por ELO + Explicabilidad SHAP + Arquitectura (MVP → MCP + Agentes)

> Objetivo: que la salida del LLM sea **pedagógica y proporcional al nivel** (ej. ~1400 Chess.com),
> evitando análisis “de elite” y reduciendo respuestas genéricas/similares entre blancas y negras.

---

## 1) Problema observado

### 1.1 Desalineación entre *fine analysis* y público objetivo
Un análisis muy fino (típico 2400+ FIDE) **no siempre es útil** para un jugador ~1400–1600:
- El jugador intermedio bajo necesita **reglas simples + señales claras + 2–3 acciones concretas**.
- El jugador fuerte necesita **líneas forzadas, evaluación precisa, técnica de conversión**, etc.

### 1.2 Reportes “muy parecidos” para blancas y negras
Vimos un síntoma típico:
- El reporte para blancas y negras termina diciendo casi lo mismo (“control del centro”, “movilidad del rival”, “apertura”).
- Eso suele pasar cuando:
  1) el prompt no **ancla** con claridad *side-to-analyze*,
  2) el LLM no recibe **evidencia diferencial** por bando (ej. top errores/SHAP por color),
  3) el formato no obliga a **citar jugadas / momentos** concretos.

---

## 2) Conceptos breves: ¿Qué es SHAP y cómo leerlo?

### 2.1 Intuición
**SHAP** (Shapley Additive Explanations) es una técnica para explicar **por qué el modelo** predijo una clase (good / inaccuracy / mistake / blunder).

- Cada feature aporta “a favor” o “en contra” de una clase.
- SHAP asigna a cada feature un valor que aproxima su “contribución” a la predicción para ese caso.

### 2.2 Lectura práctica (sin matemática pesada)
- `shap_value > 0` para una clase: empuja la predicción hacia esa clase.
- `shap_value < 0`: empuja en contra (favorece otras clases).
- `|shap_value|` grande: **feature muy influyente**.
- Promedios `mean(|SHAP|)` por feature: “qué features explican más al modelo en general”.

### 2.3 Errores comunes de interpretación
- SHAP **no dice** “la jugada es mala porque el centro…”, sino:
  “para el modelo, con estos valores de features, *aumentó* la probabilidad de esta etiqueta”.
- Si tus features son “proxy” (ej. `opponent_mobility`), el reporte debe traducirlo a:
  “le diste opciones / no lo restringiste”, y **aterrizarlo en 1–2 decisiones**.

---

## 3) Gap clave: análisis temporal de apertura (ej. “mover la misma pieza 3 veces”)

Tu observación es correcta: si en movidas 8–10 el blanco movió la misma pieza repetidamente,
eso viola heurísticas típicas de apertura (en nivel 1400 suele ser un *inaccuracy* o *mistake* pedagógico).

### 3.1 Por qué hoy no aparece en SHAP
Con tu set de features (al menos el que se ve en el extracto):
- `move_number_global`, `self_mobility`, `opponent_mobility`, `branching_factor`, etc.
**no codifican explícitamente**:
- “misma pieza movida N veces en apertura”
- “desarrollo incompleto”
- “salidas repetidas de dama/torre temprano”
- “enroque tardío”
- “piezas menores sin desarrollar en move 10”

**Solución**: agregar features temporales de apertura (baratas y muy explicables).

### 3.2 Features recomendadas (muy útiles para 1200–1800)
**Apertura / temporal**
- `same_piece_moves_opening` (conteo de veces que se movió la misma pieza en los primeros 10–12 ply)
- `unique_pieces_developed_by_move10` (cuántas piezas menores salieron)
- `queen_moves_before_move10`
- `rooks_connected_by_moveN` (o booleano “torres conectadas antes de X”)
- `castled_by_move12` (boolean o move index)
- `center_pawns_moved` (e/d files avanzados al menos 1 paso)
- `minor_pieces_on_back_rank_by_move10`

**Pedagógicas / simples**
- `hung_piece_count` (piezas atacadas y no defendidas en 1 ply)
- `undefended_pieces` (conteo)
- `king_safety_simple` (pawns delante del rey, piezas cerca)

Con esto, el LLM puede decir:  
> “En apertura repetiste la misma pieza 3 veces: eso te atrasó el desarrollo y le regaló tiempos al rival.”

---

## 4) Ajuste de severidad por ELO (lo que pedís explícitamente)

Tu punto central:  
> una jugada que para 1600 es “inaccuracy”, para 2400 puede ser “blunder”.

### 4.1 Dos enfoques (se pueden combinar)

#### A) “Calibration” post-modelo (rápido)
Mantener el modelo actual (`error_label`) y luego aplicar una función de severidad por ELO:

- `severity = f(error_label, player_elo, phase, score_diff, material_swing)`
- Esto no cambia el modelo, cambia **cómo lo narrás** y cómo priorizás.

Ejemplo de regla:
- Si `player_elo >= 2300` y `score_diff` cae fuerte → subir 1 nivel (inaccuracy → mistake).
- Si `player_elo <= 1600` y no hay swing material y la caída es chica → bajar 1 nivel (mistake → inaccuracy) pero con foco pedagógico.

#### B) Modelo condicionado por ELO (más “purista”)
Entrenar/servir el modelo como:
- `P(error_label | features, elo_bucket)`
o entrenar modelos por bucket.

Vos ya hiciste ingeniería por rangos y balanceo: excelente.
Aun así, conviene que el LLM también reciba el `elo_bucket` y reglas narrativas.

### 4.2 Reglas narrativas por bucket (LLM Output Policy)
Definí un “policy” textual que el LLM debe obedecer.

Ejemplo (muy resumido):
- **1200–1600**: 3 bullets, 2 jugadas clave, 1 hábito.
- **1600–2000**: 3–5 bullets, 2 variantes cortas.
- **2000–2400**: foco en conversión, precisión, prophylaxis.
- **2400+**: líneas críticas, evaluación, técnica.

---

## 5) Por qué tus reportes quedan genéricos y similares

### 5.1 Causas típicas
1) Prompt sin “evidence pack” específico por bando  
2) Falta de “deltas” (qué cambió realmente en esos moves)
3) Features agregadas a nivel game, pero no “top moves” por color
4) El LLM rellena con principios universales (centro, desarrollo, iniciativa)

### 5.2 Fix: obligar al LLM a usar evidencias
En vez de pasar sólo “Top 5 features globales”, pasarle:
- Top N jugadas con error **del lado analizado**:
  - `move_number`
  - `error_label`
  - `top_shap_features_for_move` (3–5)
  - `fen_before` (si lo tenés) o al menos `pgn_segment`
  - `score_before/after` o `score_diff`
  - `material_balance_before/after`

Y un formato de salida que lo fuerce:
- “Cita al menos 3 jugadas concretas”
- “No repitas recomendaciones”
- “Separar *lo que hiciste bien* vs *lo que te costó la partida*”

---

## 6) Arquitectura propuesta: MVP LLM Report → MCP + Agentes

### 6.1 MVP (sin MCP, simple y robusto)
**Front (Web/Streamlit)** → **FastAPI** → **ReportService** → **DB**

**ReportService**:
1) carga `analysis_id`, `game_id`, `side_to_analyze`, `player_elo`
2) arma `evidence_pack` (JSON chico y específico)
3) aplica `elo_policy` (reglas narrativas)
4) llama al LLM (prompt fijo + evidence)
5) guarda `report_md` en DB

**Pros**
- rápido
- barato
- reproducible
- fácil de testear (snapshot tests del prompt)

**Contras**
- menos flexible para “preguntas libres”
- si faltan datos, el reporte puede quedar general

### 6.2 MCP como puente a backend (siguiente escalón)
Si el reporte “requiere datos del análisis SHAP”, MCP es una opción para que el agente/LLM:
- consulte herramientas (“tools”) controladas:
  - `get_shap_moves(analysis_id, side)`
  - `get_game_pgn(game_id)`
  - `get_positions(game_id, move_range)`
  - `get_feature_stats(analysis_id, side)`

**Idea**: LLM no recibe todo “hardcodeado”, sino que puede pedir lo que necesita.

**Pros**
- respuestas más específicas
- soporta preguntas libres del usuario (“¿por qué move 12 fue mistake?”)
- reduce prompts enormes (trae datos on-demand)

**Contras / riesgos**
- costo variable (más llamadas)
- latencia
- seguridad (hay que controlar herramientas, scopes, rate limits)
- observabilidad (log de tool calls, trazas)

### 6.3 Agentes IA (cuando realmente suma)
Agentes valen la pena si:
- hay múltiples pasos (detectar fases, agrupar patrones, generar plan semanal)
- hay branching (si el usuario pregunta X, traer Y)
- querés “modo coach” conversacional

Modelo recomendado:
- **Orchestrator Agent** (decide qué tools llamar)
- **Analysis Agent** (interpreta SHAP + heurísticas de apertura)
- **Coach Agent** (produce recomendaciones adaptadas por ELO)
- **Exporter Agent** (genera Study/Chapters/Markdown/PDF)

---

## 7) Hardcodear prompts vs generar prompts dinámicos vs chat libre

### 7.1 Hardcodeado (template fijo)
**Pros**
- reproducible
- más fácil de versionar (git)
- fácil A/B testing
- menos “drift”

**Contras**
- menos flexible
- puede quedar repetitivo

### 7.2 Dinámico (prompt builder)
Generás el prompt en tiempo real a partir de:
- ELO, side, fase, features dominantes, top blunders, etc.

**Pros**
- personalizado sin ser “agente complejo”
- minimiza tokens (solo lo relevante)

**Contras**
- más riesgo de bugs (prompt mal armado)
- requiere tests

### 7.3 Usuario pregunta libre (chat)
**Pros**
- UX excelente
- aprendizajes más profundos (“preguntas del momento”)

**Contras**
- si no usás tools/MCP, inventa contexto
- requiere guardrails fuertes:
  - “si no tengo datos, pregunto / pido fetch”
  - “no asumir color”
  - “citar jugadas”

**Recomendación práctica**:
- MVP: template fijo + evidence_pack
- V2: prompt builder + endpoints MCP
- V3: chat libre con tools + límites + cache

---

## 8) Roadmap (MVP → MCP → Agentes)

### Fase 0 — Bases (1–2 sprints)
- [ ] Definir `side_to_analyze` obligatorio (white|black)
- [ ] Evidence pack por lado:
  - top errores (N=5–10) del lado analizado
  - top SHAP por jugada
  - score/material delta si existe
- [ ] Output policy por ELO (1200–1600 / 1600–2000 / 2000+)
- [ ] Snapshot tests del prompt + golden outputs

### Fase 1 — MVP Report v1 (1 sprint)
- [ ] `POST /report/shap` → devuelve Markdown
- [ ] Guardar en DB: `report_md`, `prompt_version`, `model`, `tokens`, `cost`, `generated_at`
- [ ] UI: botón “Generar reporte” + selector “analizar blancas/negras”

### Fase 2 — Features temporales de apertura (2–3 sprints)
- [ ] Implementar features:
  - same_piece_moves_opening
  - developed_minors_by_move10
  - queen_moves_before_move10
  - castled_by_move12
- [ ] Re-entrenar o sumar al pipeline (y recalcular SHAP)
- [ ] Ajustar reporte: incluir “Reglas de apertura violadas” (1–2 líneas)

### Fase 3 — MCP mínimo (1–2 sprints)
- [ ] Tool: `get_shap_moves(analysis_id, side, top_k)`
- [ ] Tool: `get_game_segment(game_id, move_from, move_to)`
- [ ] Tool: `get_opening_heuristics(game_id, side)`
- [ ] Orchestración simple: el LLM pide datos si faltan

### Fase 4 — Agentes (2–4 sprints)
- [ ] Orchestrator + Coach Agent
- [ ] “Modo entrenador”:
  - plan semanal (táctica / apertura / finales)
  - ejercicios sugeridos
- [ ] Integración con Studies (Lichess-like):
  - capítulos automáticos por error_label

---

## 9) Prompt recomendado (plantilla para Copilot/VSCode)

### 9.1 Prompt template (mínimo, anti-genericidad)
**Reglas de salida**:
- debe diferenciar blanco/negro
- debe mencionar 3 jugadas concretas
- debe dar 3 acciones concretas para ELO ~1400

```text
Sos un coach de ajedrez para nivel {player_elo} (Chess.com).
Analizá SOLO al lado: {side_to_analyze}. No hables del otro lado salvo para explicar su amenaza.

Tenés un evidence_pack con:
- errores del lado analizado (move_number, error_label)
- top SHAP features por jugada
- señales de apertura (si existen)

Tareas:
1) Resumen (máx 5 líneas) enfocado al nivel {player_elo}
2) 3 momentos concretos (move #, qué pasó, por qué fue un error para este ELO, y qué hábito lo evita)
3) Regla(s) de apertura si hay repetición de piezas / desarrollo tardío (mencionarlo explícitamente)
4) 3 acciones de entrenamiento para 7 días (táctica/apertura/final), bien simples

Restricciones:
- No uses frases genéricas (“controla el centro”) sin aterrizarlas a una jugada del evidence_pack
- Si falta evidencia para una afirmación, decilo (“no tengo FEN/PGN del tramo”) y proponé qué dato pedirías
---

## 10) Status de Implementación (Actualizado: 2026-03-01)

### ✅ **Fase 0-1: MVP Report v1 — COMPLETADO**

**Implementado:**
- ✅ `side_to_analyze` obligatorio (white|black) - implementado como `player_color`
- ✅ Evidence pack por lado con top errores del lado analizado
- ✅ Output policy por ELO (1200-1600 / 1600-2000 / 2000+)
- ✅ Competitive Context Engine: resultado, error_ratio comparativo, momento crítico
- ✅ Pattern Synthesis Layer: 5 patrones detectados con evidencia específica
- ✅ `POST /analysis/llm/report` endpoint funcional
- ✅ Integración con GPT-4 (AsyncOpenAI)
- ✅ Guardar metadata: tokens, cost, model, generated_at
- ✅ Postman collection para testing

**Características implementadas (Secciones 1-5):**

#### Sección 4: Ajuste de severidad por ELO
- ✅ `_calibrate_severity_by_elo()`: Calibración post-modelo de error_label según ELO
- ✅ Matriz de severidad pedagógica (novice/intermediate/advanced)
- ✅ Tono narrativo adaptado por nivel

#### Sección 4.2: Output policy por bucket
- ✅ `_get_elo_output_policy()`: Reglas de formato según ELO
  - Novice (< 1600): 3 bullets, 2 jugadas clave, 300 palabras
  - Intermediate (1600-2000): 5 bullets, 4 jugadas clave, 450 palabras
  - Advanced (2000+): 6 bullets, 6 jugadas clave, 600 palabras

#### Sección 5: Fix para genericidad
- ✅ `_get_top_error_moves()`: Evidence pack move-by-move con SHAP específico
- ✅ Top 8 jugadas críticas ordenadas por severidad * impacto SHAP
- ✅ Cada move incluye: move_number, error_label, top_shap_features, shap_impact
- ✅ Prompt obligatorio: Citar movimientos del evidence pack
- ✅ Competitive Context: Diferenciación win/loss/draw

**Métricas actuales:**
- Tokens promedio: ~900 (optimizado desde ~1415)
- Costo por reporte: ~.027 USD (reducido 36%)
- Latencia: 2-3 segundos
- Player color filtering: ✅ Funcional
- Winner vs loser differentiation: ✅ Implementado

**Código implementado:**
- `src/api/services/llm_analysis_service.py` (910 líneas)
- `src/api/routers/analysis.py`: Endpoints LLM
- `Chess_LLM_Pedagogical_Reports.postman_collection.json`: Testing

**Documentación:**
- `docs/MCP_TOOLS_SPECIFICATION.md`: Especificación completa de Fase 3

---

### 📋 **Fase 2: Features temporales de apertura — ESPECIFICADO, NO IMPLEMENTADO**

**Requiere:**
- Features de apertura (Sección 3): same_piece_moves_opening, developed_minors_by_move10, etc.
- Modificar `src/scripts/generate_features_with_tactics.py`
- Re-entrenar modelo ML con nuevas features

**Estimación:** 2-3 sprints

---

### 🔜 **Fase 3: MCP mínimo — ESPECIFICADO**

**Documentación completa:** `docs/MCP_TOOLS_SPECIFICATION.md`

**Tools especificados:**
1. `get_shap_moves(analysis_id, side, top_k)`
2. `get_game_segment(game_id, move_from, move_to)`
3. `get_competitive_context(game_id, player_color)`
4. `get_feature_stats(analysis_id, side)`
5. `get_position_analysis(fen, depth)`

**Estimación:** 2-3 sprints

---

_Última actualización: 2026-03-01 (Fase 1 completada, Fase 2-3 especificadas)_
