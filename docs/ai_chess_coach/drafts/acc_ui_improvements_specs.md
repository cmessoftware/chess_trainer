# ChessInsight — Especificación de renovación de GUI

> **Plan de implementación (IDs, ramas, tests, incoherencias):** [`../roadmap/12-acc-ui-renewal-implementation-plan.md`](../roadmap/12-acc-ui-renewal-implementation-plan.md).  
> **Inventario actual (U00-001):** [`acc_ui_current_architecture.md`](acc_ui_current_architecture.md).  
> Este draft es el brief de arquitectura; el plan es la autoridad para implementar.

## 1. Objetivo

Actualizar la interfaz web de ChessInsight reutilizando la aplicación existente basada en React + Vite, pero sustituyendo completamente la capa ajedrecística frontend actual.

La nueva GUI debe eliminar:

* Chess.js
* react-chessboard
* chessboard.js
* wrappers propios sobre esos componentes
* lógica custom de tablero
* lógica custom de movimiento legal
* lógica custom de drag & drop
* lógica custom de resaltado y anotaciones
* cualquier otra librería de tablero que duplique funciones disponibles en Chessground

El frontend debe estandarizarse sobre:

```text
React
Vite
TypeScript
Chessground
chessops
```

Chessground debe ser el único componente de visualización e interacción del tablero.

chessops debe ser la librería principal para reglas, posiciones, movimientos y operaciones ajedrecísticas frontend.

---

# 2. Principio arquitectónico

Arquitectura objetivo:

```text
React + Vite + TypeScript
        │
        ├── Chessground
        ├── chessops
        ├── Move Tree propio
        ├── componentes ChessInsight
        │
        ▼
      FastAPI
        │
        ├── Stockfish
        ├── Lc0
        ├── ML / XGBoost
        ├── Pattern Engine
        ├── RAG / LLM
        └── PostgreSQL
```

No mantener capas heredadas de ajedrez por compatibilidad.

La migración debe terminar con una única arquitectura consistente.

---

# 3. Migración obligatoria

Eliminar completamente del proyecto frontend cualquier uso de:

```text
chess.js
react-chessboard
chessboard.js
```

También eliminar:

* adapters específicos para esas librerías;
* helpers duplicados;
* wrappers históricos;
* validadores de movimiento propios;
* código custom de coordenadas;
* generación manual de movimientos legales;
* sincronización manual de piezas;
* lógica propia de promociones si chessops puede resolverla;
* cualquier board component alternativo.

Buscar específicamente en:

```text
package.json
package-lock.json
pnpm-lock.yaml
yarn.lock
src/
tests/
```

y eliminar dependencias y código muerto.

Al finalizar la migración no debe quedar ninguna referencia a estas librerías.

---

# 4. Chessground

Usar Chessground para todo el comportamiento visual del tablero.

Debe proporcionar como mínimo:

* renderizado del tablero;
* drag & drop;
* click-to-move;
* orientación;
* flip board;
* animaciones;
* último movimiento;
* posibles destinos;
* resaltado de casillas;
* premoves si se requieren posteriormente;
* flechas;
* círculos;
* anotaciones;
* selección de piezas;
* estados de movimiento;
* soporte para posiciones arbitrarias;
* integración con temas de piezas y tablero.

La experiencia debe acercarse a la interacción de Lichess.

No copiar Lichess completo.

Sí reutilizar Chessground correctamente.

---

# 5. chessops

Usar chessops como fuente principal de lógica ajedrecística frontend.

Responsabilidades:

* parseo y generación de FEN;
* estado de posición;
* side to move;
* castling rights;
* en passant;
* generación de movimientos;
* validación de legalidad;
* SAN;
* UCI;
* promociones;
* variantes;
* operaciones sobre posiciones;
* transformación entre movimientos y representación del board.

No implementar manualmente estas funciones si chessops ya las proporciona.

---

# 6. Separación de responsabilidades

Arquitectura:

```text
Chessground
     │
     ▼
ChessBoardAdapter
     │
     ▼
ChessGameController
     │
     ├── chessops
     ├── MoveTree
     ├── PGN
     └── FEN
```

Chessground debe desconocer:

* FastAPI;
* Stockfish;
* ML;
* Lc0;
* Criticality;
* RAG;
* reglas de negocio de ChessInsight.

---

# 7. ChessBoardAdapter

Crear un adapter específico para encapsular Chessground.

Ejemplo conceptual:

```typescript
interface ChessBoardAdapter {
    setPosition(fen: string): void;

    setOrientation(
        orientation: "white" | "black"
    ): void;

    setLastMove(
        move?: {
            from: string;
            to: string;
        }
    ): void;

    setDests(
        dests: Map<string, string[]>
    ): void;

    setMovable(enabled: boolean): void;

    setAnnotations(
        annotations: BoardAnnotation[]
    ): void;

    clearAnnotations(): void;

    flip(): void;
}
```

Ningún otro componente debe llamar directamente a APIs internas de Chessground.

---

# 8. ChessGameController

La lógica de posición debe centralizarse.

Ejemplo conceptual:

```typescript
interface ChessGameController {
    loadFen(fen: string): void;

    loadPgn(pgn: string): void;

    getFen(): string;

    getCurrentPosition(): ChessPosition;

    makeMove(move: UciMove): MoveResult;

    getLegalMoves(): UciMove[];

    goToMove(moveId: string): void;

    previous(): void;

    next(): void;

    first(): void;

    last(): void;
}
```

Internamente debe utilizar chessops.

No usar Chess.js como capa intermedia.

---

# 9. Layout principal

Desktop:

```text
┌────────────────────────────────────────────────────────────────┐
│ ChessInsight                                    User / Settings│
├──────────────────────────────┬─────────────────────────────────┤
│                              │ POSITION ANALYSIS               │
│                              │                                 │
│                              │ Criticality     HIGH            │
│         CHESSGROUND          │ STOP            CALCULATE       │
│                              │ Probability     87 %             │
│                              │                                 │
│                              │ Signals                         │
│                              │ • King exposure                 │
│                              │ • Loose piece                   │
│                              │ • Tactical contact              │
├──────────────────────────────┼─────────────────────────────────┤
│ Evaluation                   │ Candidate moves                 │
│ SF +0.74                     │                                 │
│ Lc0 +0.42                    │ 1. Bxh7+                        │
│                              │ 2. Ne5                          │
│                              │ 3. Qc2                          │
├──────────────────────────────┴─────────────────────────────────┤
│ |<      <      >      >|        Flip          Analyze         │
├────────────────────────────────────────────────────────────────┤
│ Moves / Variations / Calculation / Explanation / Engine       │
└────────────────────────────────────────────────────────────────┘
```

---

# 10. Features similares a Lichess

La experiencia del tablero debe intentar reproducir las capacidades funcionales principales de análisis de Lichess.

No copiar su apariencia pixel por pixel.

Implementar:

## Navegación de partida

* click en jugada;
* flecha izquierda;
* flecha derecha;
* Home;
* End;
* botones first/previous/next/last.

## Movimiento de piezas

* drag & drop;
* click origen + click destino;
* legal move destinations;
* promociones;
* bloqueo de movimientos ilegales.

## Última jugada

Resaltar:

```text
from
to
```

## Selección

Mostrar claramente:

```text
selected square
legal destinations
```

## Anotaciones

Soportar:

* arrows;
* circles;
* square highlighting.

Como mínimo preparar compatibilidad conceptual con:

```text
right-click annotations
```

similar al flujo de análisis de Lichess.

---

# 11. Flechas y círculos

Definir anotaciones semánticas.

```typescript
interface BoardAnnotation {
    type:
        | "arrow"
        | "circle"
        | "square";

    from?: string;

    to?: string;

    square?: string;

    semanticType?:
        | "candidate"
        | "threat"
        | "critical"
        | "strategic"
        | "engine"
        | "user";
}
```

ChessInsight debe decidir significado.

Chessground debe decidir representación.

---

# 12. Movimiento candidato

Cuando el usuario seleccione:

```text
Candidate: Bxh7+
```

el board debe mostrar:

```text
Bc4 → h7
```

como flecha.

No modificar todavía la posición principal.

El usuario debe poder:

```text
Preview
Calculate
Play
```

según el modo de uso.

---

# 13. Árbol de variantes

No utilizar una lista lineal simple.

Crear árbol real.

```typescript
interface MoveNode {
    id: string;

    parentId?: string;

    san: string;

    uci: string;

    fenBefore: string;

    fenAfter: string;

    ply: number;

    children: MoveNode[];

    isMainLine: boolean;

    comment?: string;

    nags?: number[];
}
```

Debe soportar:

```text
1. e4 e5
2. Nf3 Nc6
3. Bb5 a6
   (3... Nf6
       4. O-O Nxe4
       (4... Be7))
4. Ba4
```

---

# 14. Comportamiento de variantes similar a Lichess

Cuando el usuario retrocede y hace otro movimiento:

```text
main line:
20. Re1
```

retrocede a 19...

y juega:

```text
20. Qc2
```

la aplicación debe crear automáticamente:

```text
20. Re1
(20. Qc2)
```

No reemplazar automáticamente la línea principal.

Después debe poder existir una acción:

```text
Promote to main line
```

---

# 15. Promoción de variante

Implementar:

```text
Promote variation
```

Una variante secundaria debe poder convertirse en principal.

Debe reorganizar:

```text
parent.children
```

sin destruir las demás variantes.

---

# 16. Eliminación de variante

Implementar:

```text
Delete variation
```

La eliminación debe afectar únicamente:

```text
selected node
+
descendants
```

No borrar otros hermanos.

---

# 17. PGN

El sistema debe poder:

* importar PGN;
* interpretar variantes;
* interpretar comentarios;
* interpretar NAGs cuando sea posible;
* exportar PGN preservando variantes.

No convertir todo el PGN en una secuencia lineal.

---

# 18. FEN

Debe soportar:

* cargar FEN;
* copiar FEN;
* reiniciar desde FEN;
* crear análisis desde una posición arbitraria.

La posición inicial de una sesión no tiene por qué ser:

```text
startpos
```

---

# 19. Evaluation Bar

Agregar barra vertical de evaluación.

Debe funcionar de forma equivalente conceptualmente a las interfaces modernas de análisis.

API conceptual:

```typescript
interface EngineEvaluation {
    type:
        | "cp"
        | "mate";

    value: number;

    depth?: number;
}
```

La representación visual debe normalizar scores altos.

---

# 20. Panel de motores

La GUI debe poder representar:

```text
Stockfish
depth 18
+0.74

1. Bxh7+ Kxh7
2. Ng5+ Kg8
3. Qh5
```

Las variantes de motor deben mostrarse en un panel independiente.

No introducir movimientos de engine directamente en la partida sin acción explícita.

---

# 21. MultiPV

Preparar soporte para:

```text
MultiPV = 3
```

Ejemplo:

```text
1. Bxh7+    +1.34
2. Ne5      +0.82
3. Qc2      +0.51
```

Estas líneas pueden alimentar:

```text
Candidate Moves
```

pero ChessInsight puede reordenarlas posteriormente con sus propios modelos.

---

# 22. Modo Analysis

Debe permitir interacción similar a Lichess Analysis Board:

```text
play move
→ generate variation
→ navigate
→ add alternate move
→ create branch
→ promote
→ delete
```

Este modo es distinto de reproducción de una partida.

---

# 23. Modo Read Only

Para análisis terminado:

```text
board movable = false
```

pero debe mantenerse:

* navegación;
* annotations;
* engine arrows;
* candidates;
* explanations.

---

# 24. Modo Calculation

Preparar un modo especializado:

```text
CALCULATION
```

En este modo:

```text
Board position stays frozen.
```

El usuario introduce movimientos en una variante mental.

Ejemplo:

```text
Displayed board:

initial position
```

mientras la lista muestra:

```text
1. Bxh7+ Kxh7
2. Ng5+ Kg8
3. Qh5
```

Chessground no debe cambiar visualmente la posición.

---

# 25. Calculation Tree

Separar:

```text
GameTree
```

de:

```text
CalculationTree
```

Nunca mezclar automáticamente una línea calculada con la partida real.

---

# 26. Position Preview

Al pasar el mouse sobre una jugada o variante se puede implementar posteriormente:

```text
temporary preview
```

La arquitectura debe permitirlo sin modificar:

```text
currentGameNode
```

---

# 27. Current position

Debe existir una única fuente de verdad:

```typescript
currentMoveId
```

o equivalente.

La FEN actual debe derivarse del nodo seleccionado.

Evitar mantener simultáneamente:

```text
currentFen
currentMove
boardPosition
gameIndex
selectedPly
```

como estados independientes si pueden quedar inconsistentes.

---

# 28. Store

Separar como mínimo:

```text
Game state
Analysis state
UI state
Engine state
```

Ejemplo:

```typescript
interface ChessInsightState {
    game: GameState;

    analysis: AnalysisState;

    engine: EngineState;

    ui: UiState;
}
```

---

# 29. No duplicar estado de Chessground

Chessground debe considerarse:

```text
rendering layer
```

No debe ser:

```text
source of truth
```

El estado verdadero vive en:

```text
ChessGameController
+
chessops
+
MoveTree
```

---

# 30. Position Analysis

Modelo:

```typescript
interface PositionAnalysis {
    fen: string;

    criticalityScore?: number;

    shouldStop: boolean;

    stopLevel:
        | "none"
        | "consider"
        | "calculate"
        | "critical";

    errorProbability?: number;

    tacticalSignals: AnalysisSignal[];

    strategicSignals: AnalysisSignal[];

    candidates: CandidateMove[];

    engineEvaluation?: EngineEvaluation;

    explanation?: string;
}
```

---

# 31. STOP

Visualización prominente:

```text
NORMAL
CONSIDER
CALCULATE
CRITICAL
```

No basar la representación exclusivamente en color.

Debe existir texto explícito.

---

# 32. Candidate Moves

Ejemplo:

```text
CANDIDATES

1. Bxh7+     +1.32
   forcing

2. Ne5       +0.84
   positional

3. Qc2       +0.51
   prophylactic
```

Al seleccionar una candidata:

```text
draw arrow
highlight origin
highlight destination
```

---

# 33. Criticality signals

Separar:

```text
TACTICAL

STRATEGIC
```

No mezclar todo en una explicación generada por LLM.

La estructura debe venir del backend.

---

# 34. Decision Process

Panel:

```text
Situation

Threat

Worst piece

Plan

Candidates

Calculation
```

El objetivo es representar explícitamente el proceso de decisión.

---

# 35. Backend

Mantener FastAPI existente.

No mover al navegador:

* ML;
* Lc0;
* RAG;
* explicaciones;
* criticality;
* clasificación de errores;
* lógica pesada de análisis.

Frontend:

```text
presentation
interaction
chess position management
```

Backend:

```text
analysis
models
engines
explanations
storage
```

---

# 36. Diseño visual

Objetivo:

```text
professional chess workstation
```

Inspiración funcional:

```text
Lichess Analysis
ChessBase
Fritz
IDE
```

Evitar apariencia:

```text
generic SaaS dashboard
```

Priorizar:

```text
board
notation
variations
analysis
candidates
```

---

# 37. Desktop first

El producto está orientado principalmente a análisis serio.

Priorizar desktop.

Layout esperado:

```text
BOARD               ANALYSIS
BOARD               ANALYSIS

MOVES / VARIATIONS / ENGINE
```

Mobile puede simplificarse.

---

# 38. Tema oscuro

Dark mode obligatorio.

No hardcodear colores en componentes.

Usar tokens.

---

# 39. Dependencias prohibidas después de la migración

Al completar la migración no debe existir:

```text
chess.js
react-chessboard
chessboard.js
```

ni otra librería alternativa de board salvo justificación técnica explícita.

También eliminar código custom reemplazado por:

```text
Chessground
chessops
```

---

# 40. Auditoría inicial obligatoria

Antes de modificar código:

1. inspeccionar `package.json`;
2. identificar todas las dependencias de ajedrez;
3. localizar todos los imports de:

   * chess.js;
   * react-chessboard;
   * chessboard.js;
4. identificar wrappers;
5. localizar lógica custom relacionada;
6. identificar el estado actual de partida;
7. identificar cómo se carga PGN;
8. identificar cómo se calcula FEN;
9. identificar navegación;
10. identificar comunicación con backend.

Generar un informe corto de:

```text
CURRENT ARCHITECTURE

DEPENDENCIES TO REMOVE

CUSTOM CODE TO REMOVE

COMPONENTS TO REPLACE

COMPONENTS TO KEEP
```

---

# 41. Estrategia de migración

No mantener dos sistemas de tablero ejecutándose en paralelo más allá de una transición mínima.

Objetivo:

```text
OLD
Chess.js
+
react-chessboard
+
custom code
```

→

```text
NEW
chessops
+
Chessground
+
MoveTree
```

---

# 42. Fase 1 — modelo ajedrecístico

Antes del cambio visual:

crear:

```text
ChessGameController
MoveTree
ChessPosition
```

usando chessops.

Agregar pruebas.

---

# 43. Fase 2 — Chessground

Sustituir completamente el board actual.

Validar:

* FEN;
* orientation;
* legal moves;
* drag;
* click-to-move;
* promotions;
* last move;
* highlights.

---

# 44. Fase 3 — eliminar sistema anterior

Eliminar:

```text
Chess.js
react-chessboard
chessboard.js
```

y código custom obsoleto.

Ejecutar:

```text
npm build
npm test
```

y búsquedas de texto para confirmar que no quedan referencias.

---

# 45. Fase 4 — Variations

Implementar árbol de variantes similar al comportamiento de Lichess.

Incluye:

```text
create
navigate
promote
delete
```

---

# 46. Fase 5 — Analysis UI

Integrar:

```text
criticality
STOP
candidate moves
signals
evaluation
decision process
```

---

# 47. Fase 6 — Engine interaction

Agregar:

```text
evaluation bar
MultiPV
engine lines
engine arrows
```

---

# 48. Fase 7 — Calculation Training

Implementar:

```text
frozen board
calculation tree
comparison against engine
```

---

# 49. Criterios de aceptación

La migración se considera terminada cuando:

* Chessground es el único board renderer;
* chessops es la fuente principal de reglas frontend;
* Chess.js fue eliminado;
* react-chessboard fue eliminado;
* chessboard.js fue eliminado;
* no quedan board implementations custom redundantes;
* PGN funciona;
* FEN funciona;
* movimientos legales funcionan;
* promociones funcionan;
* variantes funcionan;
* navegación funciona;
* annotations funcionan;
* flip board funciona;
* backend existente sigue funcionando;
* build y tests pasan.

---

# 50. Restricción de implementación para Cursor

No hacer un simple reemplazo visual.

La tarea consiste en migrar la arquitectura ajedrecística frontend.

No conservar código antiguo simplemente para reducir cambios.

Eliminar explícitamente las dependencias y abstracciones reemplazadas.

No implementar nuevamente funcionalidades que Chessground o chessops ya proporcionan.

No hacer una reescritura del backend.

No introducir un segundo framework frontend.

No usar múltiples librerías de tablero simultáneamente.

---

# 51. Primer trabajo solicitado

Realizar primero:

```text
AUDIT + MIGRATION PLAN
```

y después implementar:

```text
chessops
+
ChessGameController
+
Chessground
```

hasta poder cargar y navegar una partida completa.

Después eliminar completamente:

```text
Chess.js
react-chessboard
chessboard.js
custom board code
```

antes de avanzar con nuevas features.

---

# 52. Resultado esperado

La capa frontend debe quedar conceptualmente:

```text
                    ChessInsight
                         │
                 React application
                         │
        ┌────────────────┴────────────────┐
        │                                 │
   Chessground                        UI Panels
        │                                 │
        ▼                                 │
 ChessBoardAdapter                        │
        │                                 │
        └─────────────┬───────────────────┘
                      ▼
             ChessGameController
                      │
              ┌───────┴───────┐
              │               │
           chessops        MoveTree
              │               │
              └───────┬───────┘
                      ▼
                 FastAPI API
                      │
       ┌──────────────┼──────────────┐
       │              │              │
   Stockfish         ML             Lc0
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                ChessInsight
```

El frontend debe comportarse como una herramienta moderna de análisis de ajedrez, con una ergonomía cercana a Lichess, mientras que la diferenciación funcional permanece en el análisis cognitivo de ChessInsight.
