# Especificación de MCP Tools para ChessTrainer LLM Analysis

> **Status:** Preparado para Fase 3 (Sección 6.2 del roadmap)  
> **Objetivo:** Definir tools/herramientas controladas para que el LLM/Agente consulte datos on-demand

---

## Contexto

En Fase 1-2 (MVP actual), el LLM recibe todo el contexto pre-procesado en el prompt:
- Evidence pack (top error moves)
- Patrones sintetizados
- Contexto competitivo
- SHAP summary

**Ventajas MVP:**
- Rápido y reproducible
- Barato (un solo llamado al LLM)
- Fácil de testear

**Limitaciones MVP:**
- Prompt puede crecer demasiado con partidas largas
- No soporta preguntas libres del usuario ("¿Por qué la jugada #12 fue mistake?")
- No puede profundizar dinámicamente en fases específicas

---

## Arquitectura MCP

**MCP (Model Context Protocol)** permite que el LLM/Agente:
1. Reciba un prompt inicial más pequeño
2. Llame a "tools" para obtener datos específicos cuando los necesite
3. Tome decisiones sobre qué información traer

**Workflow con MCP:**
```
Usuario: "¿Por qué perdí esta partida?"
    ↓
Orchestrator Agent: Decide qué tools llamar
    ↓
Tool 1: get_competitive_context(game_id, player_color) → resultado, error_ratios
Tool 2: get_top_error_moves(analysis_id, top_n=5) → movimientos críticos
Tool 3: get_shap_moves(analysis_id, move_number=12) → detalles de jugada específica
    ↓
Agent: Sintetiza respuesta con datos obtenidos
    ↓
GPT-4: Genera reporte final
```

---

## Tools Especificados (Fase 3)

### 1. `get_shap_moves`
**Descripción:** Obtiene valores SHAP de movimientos específicos del análisis

**Parámetros:**
```python
{
    "analysis_id": int,          # ID del análisis (requerido)
    "side": str,                 # "white" | "black" (requerido)
    "top_k": int = 10            # Número de movimientos a retornar (opcional)
}
```

**Retorna:**
```json
{
    "moves": [
        {
            "move_number": 12,
            "error_label": "mistake",
            "shap_features": [
                {"feature": "opponent_mobility", "shap_value": 0.45}
            ]
        }
    ]
}
```

**Implementación actual:** Ya implementado como `_get_top_error_moves()` interno  
**Para MCP:** Exponer como API endpoint `/tools/shap_moves`

---

### 2. `get_game_segment`
**Descripción:** Obtiene secuencia de movimientos (PGN/FEN) de un tramo de la partida

**Parámetros:**
```python
{
    "game_id": str,              # ID del juego (requerido)
    "move_from": int,            # Jugada inicial (requerido)
    "move_to": int               # Jugada final (requerido)
}
```

**Retorna:**
```json
{
    "game_id": "cmess1315_vs_Th3Hound",
    "pgn_segment": "10. d4 Nf6 11. Nc3 Bg7 12. Be3",
    "fen_before": "rnbqk2r/pp2bppp/4pn2/2p5/2BP4/2N5/PP2PPPP/R1BQK2R w KQkq - 0 10",
    "fen_after": "rnbqk2r/pp2bppp/4pn2/2p5/2BP4/2N1B3/PP2PPPP/R2QK2R b KQkq - 0 12"
}
```

**Implementación requerida:**
- Query a tabla `Games` (campo `pgn`)
- Parsear PGN con `python-chess`
- Extraer FEN de posiciones específicas

**Para MCP:** Endpoint `/tools/game_segment`

---

### 3. `get_opening_heuristics`
**Descripción:** Analiza fase de apertura (primeros 12-15 movimientos) según heurísticas pedagógicas

**Parámetros:**
```python
{
    "game_id": str,              # ID del juego (requerido)
    "side": str                  # "white" | "black" (requerido)
}
```

**Retorna:**
```json
{
    "same_piece_moves_count": 3,
    "unique_pieces_developed": 2,
    "queen_moved_before_move10": true,
    "castled_by_move12": false,
    "center_pawns_advanced": ["e4"],
    "violated_heuristics": [
        "Moviste la misma pieza 3 veces en apertura",
        "No enrocaste antes de jugada 12"
    ]
}
```

**Implementación requerida:**
- Features temporales de apertura (Sección 3 del roadmap)
- Requiere agregar campos a tabla `Features` o calcular on-the-fly
- Lógica de detección de repeticiones de pieza

**Para MCP:** Endpoint `/tools/opening_heuristics`

**Nota:** Esta feature requiere feature engineering adicional (Fase 2 del roadmap)

---

### 4. `get_competitive_context`
**Descripción:** Obtiene contexto competitivo de la partida (resultado, comparación)

**Parámetros:**
```python
{
    "game_id": str,              # ID del juego (requerido)
    "player_color": str          # "white" | "black" (requerido)
}
```

**Retorna:**
```json
{
    "result": "win",
    "player_error_ratio": 0.18,
    "opponent_error_ratio": 0.27,
    "error_ratio_delta": -0.09,
    "critical_move": 16,
    "phase": "middlegame"
}
```

**Implementación actual:** Ya implementado como `_get_competitive_context()` interno  
**Para MCP:** Endpoint `/tools/competitive_context`

---

### 5. `get_feature_stats`
**Descripción:** Obtiene estadísticas agregadas de features del análisis

**Parámetros:**
```python
{
    "analysis_id": int,          # ID del análisis (requerido)
    "side": str                  # "white" | "black" (requerido)
}
```

**Retorna:**
```json
{
    "total_moves": 67,
    "blunder_count": 2,
    "mistake_count": 5,
    "inaccuracy_count": 12,
    "average_centipawn_loss": 34.5,
    "top_features": [
        {"feature": "opponent_mobility", "importance": 2.34}
    ]
}
```

**Implementación actual:** Ya implementado como `_get_shap_summary()` interno  
**Para MCP:** Endpoint `/tools/feature_stats`

---

### 6. `get_position_analysis`
**Descripción:** Analiza una posición específica (FEN) con Stockfish

**Parámetros:**
```python
{
    "fen": str,                  # Posición FEN (requerido)
    "depth": int = 15            # Profundidad de análisis (opcional)
}
```

**Retorna:**
```json
{
    "evaluation": 0.45,
    "best_move": "Nf3",
    "best_line": ["Nf3", "Nc6", "d4"],
    "threats": ["c5", "Qa5+"],
    "weaknesses": ["square_d5", "undefended_pawn_b7"]
}
```

**Implementación requerida:**
- Integración con Stockfish (ya disponible en `src/ml/stockfish_evaluator.py`)
- Wrapper para análisis rápido de posición

**Para MCP:** Endpoint `/tools/position_analysis`

---

## Seguridad y Rate Limiting

Para evitar abuso de tools en production:

1. **Autenticación:** Todos los tools requieren JWT token válido
2. **Rate Limiting:**
   - Máximo 10 tool calls por request de LLM
   - Timeout: 30 segundos por tool call
3. **Scopes:**
   - Usuario solo puede consultar sus propios análisis
   - Admin puede consultar cualquier análisis
4. **Logging:**
   - Registrar cada tool call: `user_id`, `tool_name`, `params`, `timestamp`, `duration_ms`
5. **Cache:**
   - Cachear resultados de tools por 5 minutos (mismos parámetros)

---

## Implementación Técnica (Fase 3)

### Estructura de código

```
src/api/
├── routers/
│   └── tools.py              # Endpoints de MCP tools
├── services/
│   ├── tool_service.py       # Lógica de tools
│   └── mcp_orchestrator.py  # Orchestrator que decide qué tools llamar
└── schemas/
    └── tool_schemas.py       # Pydantic schemas para tools
```

### Endpoint base
```python
# src/api/routers/tools.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/tools", tags=["MCP Tools"])

@router.post("/shap_moves")
async def tool_get_shap_moves(
    request: GetShapMovesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """MCP Tool: Get SHAP values for specific moves"""
    # Validar que user tenga acceso al analysis_id
    # Llamar a lógica de tool
    # Retornar resultado
    pass
```

### Integración con LLM

Opción A: **Function Calling de OpenAI**
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_shap_moves",
            "description": "Get SHAP values for moves in analysis",
            "parameters": {
                "type": "object",
                "properties": {
                    "analysis_id": {"type": "integer"},
                    "side": {"type": "string", "enum": ["white", "black"]},
                    "top_k": {"type": "integer", "default": 10}
                },
                "required": ["analysis_id", "side"]
            }
        }
    }
]

response = await client.chat.completions.create(
    model="gpt-4",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)
```

Opción B: **LangChain Tools**
```python
from langchain.tools import Tool

shap_tool = Tool(
    name="get_shap_moves",
    func=lambda **kwargs: tool_service.get_shap_moves(**kwargs),
    description="Get SHAP values for specific moves"
)
```

---

## Roadmap de Implementación (Fase 3)

**Sprint 1: Infraestructura**
- [ ] Crear endpoints `/tools/*` en FastAPI
- [ ] Implementar autenticación y rate limiting
- [ ] Setup de logging para tool calls

**Sprint 2: Tools básicos**
- [ ] Implementar `get_shap_moves` (refactor de método existente)
- [ ] Implementar `get_competitive_context` (refactor de método existente)
- [ ] Implementar `get_feature_stats` (refactor de método existente)
- [ ] Tests unitarios

**Sprint 3: Tools avanzados**
- [ ] Implementar `get_game_segment` (requiere parseo PGN)
- [ ] Implementar `get_position_analysis` (integración Stockfish)
- [ ] Tests de integración

**Sprint 4: Orchestrator**
- [ ] Implementar `mcp_orchestrator.py`
- [ ] Integración con OpenAI Function Calling
- [ ] Workflow: LLM → decide tools → ejecuta → sintetiza
- [ ] Tests end-to-end

**Sprint 5: Features de apertura (opcional)**
- [ ] Implementar `get_opening_heuristics`
- [ ] Requiere feature engineering (Sección 3 del roadmap)
- [ ] Recalcular features en DB

---

## Métricas de Éxito (Fase 3)

1. **Latencia:** Reporte completo en < 5 segundos (con tool calls)
2. **Costo:** Reducir prompt tokens en 40% (datos on-demand vs full context)
3. **Precisión:** Reports mantienen o mejoran calidad vs MVP
4. **Flexibilidad:** Soportar preguntas libres del usuario
5. **Observabilidad:** 100% de tool calls loggeados

---

## Comparación: MVP vs MCP

| Aspecto               | MVP (Fase 1-2)    | MCP (Fase 3)             |
| --------------------- | ----------------- | ------------------------ |
| **Prompt tokens**     | ~900              | ~400 (60% reducción)     |
| **Latencia**          | 2-3s              | 3-5s (múltiples calls)   |
| **Costo por reporte** | $0.027            | $0.020 (estimated)       |
| **Flexibilidad**      | Fijo              | Adaptativo               |
| **Preguntas libres**  | ❌                 | ✅                        |
| **Complejidad**       | Baja              | Media                    |
| **Observabilidad**    | Prompt + response | Trace completo con tools |

---

## Referencias

- **Roadmap principal:** `ROADMAP_INTEGRACION_LLM.md` (Sección 6.2)
- **OpenAI Function Calling:** https://platform.openai.com/docs/guides/function-calling
- **Model Context Protocol:** https://spec.modelcontextprotocol.io/
- **LangChain Tools:** https://python.langchain.com/docs/modules/agents/tools/

---

_Última actualización: 2026-03-01 (Fase 2 completada, Fase 3 especificada)_
