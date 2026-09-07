# Prompt para Cursor — ChessInsight Módulo 08

## Modelo de complejidad y calidad práctica de decisiones

Actuá como líder técnico y desarrollador senior de Python especializado en arquitectura modular, análisis de ajedrez, motores UCI, modelos explicables y pruebas automatizadas.

Debés diseñar e implementar el **Módulo 08 de ChessInsight: Modelo de complejidad y calidad práctica de decisiones**.

Este módulo se construye por encima del Módulo 07. No reemplaza el análisis de posiciones críticas, candidatas ni secuencias subóptimas. Consume sus diagnósticos estructurados y los transforma en conceptos prácticos que luego puedan explicarse a un jugador mediante reglas deterministas y, opcionalmente, un LLM.

---

## 1. Forma de trabajo obligatoria

Antes de modificar código:

1. Inspeccioná la estructura actual del repositorio.
2. Localizá el Módulo 07, sus contratos, servicios, modelos, notebooks y pruebas.
3. Identificá qué datos produce realmente y cuáles todavía no existen.
4. Revisá las convenciones del proyecto: nombres, tipado, serialización, logging, configuración y tests.
5. Creá o actualizá una lista de tareas con estados:
   - `pending`
   - `in_progress`
   - `completed`
   - `blocked`
6. Presentá un plan breve antes de implementar.
7. Implementá en incrementos pequeños y verificables.
8. Ejecutá las pruebas relevantes después de cada incremento.

No inventes rutas, clases ni contratos. Adaptá el diseño propuesto a la arquitectura real del repositorio. No reescribas componentes funcionales del Módulo 07 salvo que sea imprescindible para exponer un contrato estable y retrocompatible.

---

## 2. Objetivo del módulo

Convertir evidencia ajedrecística producida por el Módulo 07 en un perfil estructurado de la decisión que permita responder preguntas como:

- ¿La posición exigía una jugada única?
- ¿Cuántas candidatas eran razonables?
- ¿La jugada elegida era robusta frente a las mejores defensas?
- ¿La variante requería varias jugadas únicas consecutivas?
- ¿La evaluación era estable o sensible a mayor profundidad?
- ¿La posición tenía alta complejidad de cálculo?
- ¿El error surgió por omitir una defensa, elegir una variante frágil o evaluar mal la posición final?
- ¿Qué recomendación concreta puede extraerse para el entrenamiento?

El resultado no debe limitarse a repetir la pérdida de evaluación de Stockfish.

Ejemplo del cambio buscado:

```text
Salida insuficiente:
18...b5 pierde 1,4 peones.

Salida esperada:
18...b5 abrió la columna c cuando las piezas blancas estaban mejor preparadas
para ocuparla. La decisión era frágil porque una respuesta precisa del rival
cambiaba la evaluación. Antes de realizar una ruptura de flanco, había que
comparar quién se beneficiaría de las líneas abiertas.
```

---

## 3. Posición dentro de la arquitectura

Flujo esperado:

```text
PGN
  -> reconstrucción de posiciones
  -> Módulo 07: posiciones críticas
  -> Módulo 07: MultiPV y candidatas
  -> Módulo 07: comparación con la jugada real
  -> Módulo 07: diagnóstico estructurado
  -> Módulo 08: métricas de decisión
  -> Módulo 08: reglas heurísticas
  -> Módulo 08: hechos explicativos estructurados
  -> explicación pedagógica determinista o mediante LLM
  -> validación humana opcional
```

Separar estrictamente:

1. **Evidencia:** evaluaciones, variantes, respuestas y features verificables.
2. **Métricas:** medidas derivadas de esa evidencia.
3. **Inferencias:** reglas explícitas y trazables.
4. **Narrativa:** explicación para el usuario.
5. **Confirmación humana:** información subjetiva que el sistema no puede observar.

El LLM no debe decidir si una jugada es correcta ni inventar causas a partir de una FEN.

---

## 4. Alcance del MVP

Implementar primero métricas deterministas derivables de los datos disponibles:

1. **Best move gap**
   - Diferencia de evaluación entre la mejor candidata y la segunda.
   - Debe respetar la perspectiva del jugador que mueve.

2. **Acceptable candidate count**
   - Cantidad de candidatas dentro de un umbral configurable respecto de la mejor.
   - No fijar el umbral dentro de la lógica de dominio.

3. **Only-move indicator**
   - Indicar si una única jugada conserva la evaluación dentro del umbral aceptable.
   - Guardar también la evidencia numérica; no devolver solamente un booleano.

4. **Critical reply count**
   - Cantidad de respuestas del rival que deben analizarse por ser tácticamente relevantes o mantener una evaluación competitiva.

5. **Continuation fragility**
   - Cantidad o proporción de jugadas únicas necesarias en la continuación principal.
   - Diferenciar fragilidad inmediata de fragilidad acumulada.

6. **Robustness**
   - Medir cuánto se conserva el resultado esperado de una candidata frente a las mejores respuestas del rival.
   - No confundir robustez con evaluación absoluta.

7. **Evaluation stability**
   - Variación de la evaluación y del ranking de candidatas entre profundidades o iteraciones, cuando estos datos existan.
   - Si no existen, devolver `UNKNOWN`; no simular estabilidad.

8. **Decision complexity profile**
   - Clasificación inicial `LOW`, `MEDIUM`, `HIGH` basada en reglas configurables y explicables.
   - Conservar las métricas componentes para evitar una caja negra.

9. **Diagnostic confidence**
   - Confianza del sistema en su propio diagnóstico según cobertura, estabilidad y disponibilidad de evidencia.
   - No denominarla ni presentarla como confianza subjetiva del jugador.

---

## 5. Fuera del alcance inicial

No implementar todavía como valores probabilísticos definitivos:

- probabilidad de error humano;
- dificultad calibrada por Elo;
- confianza subjetiva del jugador;
- coste cognitivo personalizado;
- entropía presentada como probabilidad calibrada;
- predicción del movimiento del rival;
- evaluación psicológica del jugador;
- generación libre de explicaciones desde una FEN.

Dejar puntos de extensión para estas capacidades, pero no introducir precisión ficticia.

---

## 6. Contratos de dominio sugeridos

Adaptar los nombres al estilo real del repositorio. Usar modelos tipados y serializables.

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AssessmentLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class MetricEvidence:
    code: str
    description: str
    values: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DecisionMetrics:
    best_move_gap_cp: int | None
    acceptable_candidate_count: int | None
    only_move: bool | None
    critical_reply_count: int | None
    continuation_fragility: float | None
    robustness: float | None
    evaluation_stability: float | None
    evidence: tuple[MetricEvidence, ...] = ()


@dataclass(frozen=True)
class PracticalDecisionAssessment:
    complexity: AssessmentLevel
    fragility: AssessmentLevel
    robustness: AssessmentLevel
    diagnostic_confidence: AssessmentLevel
    primary_reason_code: str | None
    secondary_reason_codes: tuple[str, ...] = ()
    training_recommendation_codes: tuple[str, ...] = ()
    evidence: tuple[MetricEvidence, ...] = ()
```

Esto es una referencia, no una orden de crear exactamente estas clases. Preferir los contratos ya utilizados por el proyecto, como Pydantic, dataclasses u otra solución existente.

Todos los campos no calculables deben representarse explícitamente mediante `None`, `UNKNOWN` o `NEEDS_REVIEW`, según las convenciones existentes. Nunca completar datos faltantes mediante suposiciones.

---

## 7. Taxonomía inicial de razones

Definir códigos estables separados del texto mostrado al usuario. Como mínimo contemplar:

```text
ONLY_MOVE_REQUIRED
BEST_MOVE_NOT_CONSIDERED
CRITICAL_REPLY_OMITTED
HIGH_REPLY_BRANCHING
FRAGILE_CONTINUATION
LOW_ROBUSTNESS
UNSTABLE_EVALUATION
PREMATURE_SIMPLIFICATION
UNNECESSARY_COMPLEXITY
FAILED_FINAL_POSITION_EVALUATION
TACTICAL_RESOURCE_MISSED
OPPONENT_THREAT_MISREAD
INSUFFICIENT_EVIDENCE
NEEDS_HUMAN_REVIEW
```

No todos podrán determinarse en el MVP. Implementar solamente los respaldados por evidencia disponible y mantener el resto como extensión explícita.

---

## 8. Motor de reglas

Las inferencias deben surgir de reglas auditables. Evitar condicionales dispersos por servicios y notebooks.

Ejemplos conceptuales:

```text
Si acceptable_candidate_count == 1
y best_move_gap supera el umbral configurado
entonces ONLY_MOVE_REQUIRED.

Si critical_reply_count es alto
y robustness es baja
entonces HIGH_REPLY_BRANCHING + LOW_ROBUSTNESS.

Si la jugada real conserva ventaja solamente mediante varias jugadas únicas
entonces FRAGILE_CONTINUATION.

Si faltan evaluaciones a distintas profundidades
entonces evaluation_stability = UNKNOWN.
```

Requisitos:

- umbrales configurables;
- reglas unitariamente testeables;
- resultado determinista;
- códigos estables;
- evidencia adjunta;
- sin dependencias directas con UI o LLM;
- registro de versión de configuración o reglas cuando corresponda.

---

## 9. Capa explicativa

Implementar primero un renderizador determinista basado en plantillas y códigos.

Ejemplo:

```python
explanation = explanation_renderer.render(
    assessment=assessment,
    player_level="1600-1799",
    language="es",
)
```

La salida debe diferenciar:

1. **Qué ocurrió.**
2. **Por qué fue difícil.**
3. **Qué proceso de decisión falló.**
4. **Qué regla práctica conviene entrenar.**

Ejemplo:

```text
La posición exigía precisión porque una sola candidata conservaba la ventaja.
La jugada realizada resolvía la amenaza visible, pero omitía una respuesta
intermedia del rival. El problema principal no fue la profundidad de cálculo,
sino la cobertura incompleta de sus defensas. Entrenamiento recomendado:
después de elegir una candidata, revisar los jaques, capturas y amenazas del rival.
```

Una integración posterior con LLM debe recibir exclusivamente:

- diagnóstico estructurado;
- evidencia permitida;
- variante principal verificada;
- nivel del jugador;
- idioma y extensión solicitada.

Debe prohibirse al LLM:

- alterar evaluaciones;
- afirmar motivos no presentes en la evidencia;
- presentar inferencias como hechos;
- inventar candidatas consideradas por el jugador;
- atribuir estados psicológicos;
- sustituir `UNKNOWN` por una explicación plausible.

---

## 10. Diferenciar confianza del diagnóstico y confianza del jugador

Mantener contratos separados:

```json
{
  "diagnostic_confidence": "HIGH",
  "estimated_decision_complexity": "HIGH",
  "player_confidence": null
}
```

`diagnostic_confidence` puede derivarse de:

- cobertura de candidatas;
- cobertura de respuestas;
- estabilidad entre profundidades;
- consistencia de evaluaciones;
- disponibilidad de variantes completas;
- ausencia de errores del motor o del parser.

`player_confidence` solo puede conocerse mediante entrada humana, think-aloud, formulario posterior o datos equivalentes. No inferirlo del tiempo utilizado ni de la jugada elegida.

---

## 11. Configuración

Centralizar al menos:

```yaml
module_08:
  acceptable_candidate_loss_cp: 50
  only_move_gap_cp: 100
  critical_reply_threshold_cp: 75
  fragility_max_plies: 8
  complexity:
    medium_candidate_count: 3
    high_candidate_count: 5
    medium_critical_reply_count: 2
    high_critical_reply_count: 4
```

Los valores son iniciales y deben validarse. No tratarlos como verdades ajedrecísticas universales. Registrar la configuración usada en cada análisis cuando el diseño existente lo permita.

Considerar correctamente:

- scores en centipawns;
- mate scores;
- perspectiva del jugador que mueve;
- normalización de evaluaciones;
- posiciones sin suficientes líneas MultiPV;
- finales con tablebases, si ya están soportadas;
- motores o configuraciones diferentes.

---

## 12. Pruebas requeridas

### Unitarias

- normalización desde la perspectiva del jugador;
- cálculo del best move gap;
- conteo de candidatas aceptables;
- detección de jugada única;
- conteo de respuestas críticas;
- cálculo de fragilidad;
- cálculo de robustez;
- estabilidad conocida y desconocida;
- clasificación de complejidad;
- generación de códigos de razón;
- propagación correcta de `UNKNOWN`.

### Contratos

- serialización y deserialización;
- compatibilidad con salidas reales del Módulo 07;
- campos faltantes y datos parciales;
- compatibilidad retroactiva cuando sea necesaria.

### Golden tests

Crear un conjunto pequeño de posiciones verificadas manualmente que incluya:

1. una jugada única;
2. varias candidatas equivalentes;
3. sacrificio atractivo pero frágil;
4. simplificación robusta;
5. alta ramificación defensiva;
6. evaluación inestable;
7. evidencia insuficiente;
8. una partida PGN real completa.

Cada caso debe conservar:

- FEN;
- jugada real;
- candidatas;
- evaluaciones;
- respuestas críticas;
- resultado esperado del Módulo 08;
- justificación humana breve;
- versión del motor y parámetros relevantes, si aplica.

No hacer que todos los golden tests dependan de ejecutar Stockfish. Preferir fixtures estables generados y revisados previamente; mantener por separado las pruebas de integración reales con el motor.

---

## 13. Observabilidad y trazabilidad

Cada resultado debe poder responder:

- ¿Qué datos del Módulo 07 se utilizaron?
- ¿Qué métricas se calcularon?
- ¿Qué regla produjo cada código?
- ¿Qué configuración y versión de reglas se aplicó?
- ¿Qué datos faltaron?
- ¿Por qué el sistema se abstuvo?

Evitar logging excesivo de variantes completas si contiene datos voluminosos. Usar identificadores de análisis, posición y regla.

---

## 14. Restricciones de diseño

- No duplicar el análisis UCI del Módulo 07.
- No acoplar dominio con Streamlit, notebooks o una futura API.
- No introducir un framework nuevo sin necesidad demostrada.
- No usar un LLM como fuente de verdad ajedrecística.
- No convertir heurísticas iniciales en probabilidades aparentes.
- No ocultar métricas componentes detrás de una clasificación única.
- No tratar centipawns como escala lineal universal de probabilidad de victoria.
- No inferir intenciones o emociones del jugador.
- No mezclar perspectiva de blancas con perspectiva del jugador que mueve.
- No modificar código ajeno al alcance sin justificarlo.

---

## 15. Plan de implementación esperado

### Fase 0 — Descubrimiento

- inspeccionar repositorio;
- mapear contratos del Módulo 07;
- identificar brechas;
- proponer ubicación del Módulo 08;
- documentar decisiones.

### Fase 1 — Contratos

- definir entradas y salidas;
- soportar evidencia parcial;
- serialización;
- pruebas de contrato.

### Fase 2 — Métricas deterministas

- best move gap;
- candidatas aceptables;
- jugada única;
- respuestas críticas;
- pruebas unitarias.

### Fase 3 — Robustez, fragilidad y estabilidad

- implementar solamente con evidencia disponible;
- propagar `UNKNOWN` cuando falten datos;
- agregar fixtures específicos.

### Fase 4 — Motor de reglas

- clasificación de complejidad;
- códigos de razón;
- recomendaciones codificadas;
- trazabilidad de reglas.

### Fase 5 — Explicación determinista

- plantillas en español;
- separación entre hechos e inferencias;
- salida breve y didáctica;
- pruebas golden del texto o de su estructura estable.

### Fase 6 — Integración vertical

- ejecutar Módulo 07 -> Módulo 08 con PGN real;
- generar review pack;
- validar resultados manualmente;
- documentar limitaciones.

### Fase posterior — LLM

- definir prompt y esquema de salida;
- restringirlo a evidencia estructurada;
- incorporar critic automático;
- comparar explicación determinista contra explicación LLM;
- mantener fallback sin LLM.

---

## 16. Criterios de aceptación del MVP

El MVP se considera terminado cuando:

- consume una salida real o fixture contractual del Módulo 07;
- calcula las métricas básicas sin repetir análisis del motor;
- distingue jugada única, múltiples candidatas y evidencia insuficiente;
- produce un perfil de complejidad trazable;
- diferencia confianza del diagnóstico de confianza del jugador;
- genera códigos de razón estables;
- produce una explicación determinista en español;
- procesa al menos una partida PGN real de extremo a extremo;
- posee pruebas unitarias, contractuales, golden y de integración relevantes;
- no inventa información cuando faltan datos;
- documenta configuración, limitaciones y puntos de extensión.

---

## 17. Entregables

1. Plan de tareas actualizado con estados.
2. Documento breve de arquitectura y decisiones.
3. Contratos de entrada y salida.
4. Implementación del Módulo 08.
5. Configuración de umbrales.
6. Motor de reglas trazable.
7. Renderizador explicativo determinista.
8. Tests unitarios, contractuales, golden y de integración.
9. Ejemplo ejecutable con un PGN real.
10. Resumen final con:
    - archivos modificados;
    - decisiones tomadas;
    - pruebas ejecutadas;
    - resultados;
    - limitaciones;
    - deuda técnica;
    - siguiente incremento recomendado.

---

## 18. Instrucción final

No implementes todo de una sola vez. Comenzá por inspeccionar el repositorio y presentar:

1. el mapa de integración con el Módulo 07;
2. los datos disponibles y faltantes;
3. el diseño mínimo propuesto;
4. el plan de tareas por fases;
5. los riesgos técnicos detectados.

Después avanzá con el primer incremento vertical verificable, manteniendo la lista de tareas actualizada.
