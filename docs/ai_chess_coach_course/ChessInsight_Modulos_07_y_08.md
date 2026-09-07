# ChessInsight — definición de los módulos 07 y 08

## Planteo

1. El objetivo de los módulos 07 y 08 es advertir al jugador cuándo debe detenerse y calcular. La detección de errores en las jugadas ya fue implementada mediante machine learning.
2. Aclarar qué significa la diferencia mínima entre candidatas MultiPV y si se refiere a la jugada con mejor ranking según Stockfish.
3. Considerar los sacrificios y rupturas como puntos de quiebre: analizar candidatas estratégicamente mediante Leela Zero y/o variantes que busquen compensación posicional decisiva. Las ventajas puramente posicionales a largo plazo son poco frecuentes en el nivel objetivo.
4. Precisar qué significa evaluación cognitiva frente a evaluación objetiva, táctica y estratégica.
5. Determinar si, una vez implementado el módulo 07, sus resultados ya pueden considerarse validados. Agregar un resumen funcional del módulo 08.

## 1. Objetivo de los módulos 07 y 08

El clasificador ML ya cubre:

```text
Jugada realizada → good / inaccuracy / mistake / blunder
```

Los módulos 07 y 08 deben resolver otro problema:

```text
Posición antes de jugar
→ ¿debo detenerme?
→ ¿por qué?
→ ¿qué tipo de cálculo requiere?
→ ¿qué candidatas merecen análisis?
```

| Módulo | Función                                                                                                                       |
| ------ | ----------------------------------------------------------------------------------------------------------------------------- |
| 07     | Detectar señales ajedrecísticas concretas: amenazas, transformación, irreversibilidad, única jugada, complejidad y candidatas |
| 08     | Combinar esas señales mediante modelos matemáticos para estimar dificultad, incertidumbre, riesgo y necesidad de cálculo      |

`EVALUATION_DROP` no debe ser el detector principal de criticidad, porque aparece después del error. Sirve para validar retrospectivamente si la advertencia previa era relevante.

## 2. Diferencia mínima entre candidatas MultiPV

Se refiere a la diferencia de evaluación entre la candidata número 1 y la número 2 de Stockfish, no simplemente al ranking.

Ejemplo:

| Candidata | Evaluación |
| --------- | ---------: |
| 1. `Qf3`  |      +0,40 |
| 2. `Re1`  |      −1,20 |
| 3. `h3`   |      −1,45 |

La diferencia entre la primera y la segunda es:

```text
0,40 − (−1,20) = 1,60 peones = 160 cp
```

El código actual considera `ONLY_MOVE` cuando:

```text
gap(mejor, segunda) ≥ 150 cp
```

Pero esa condición sola no alcanza. La definición estable debería exigir:

```text
gran diferencia entre primera y segunda
+ estabilidad en varias profundidades
+ alternativas claramente insuficientes
```

Siempre existe una jugada con ranking 1, pero no siempre existe una única jugada necesaria.

Ejemplo contrario:

| Candidata | Evaluación |
| --------- | ---------: |
| 1. `Qf3`  |      +0,40 |
| 2. `Re1`  |      +0,18 |

Stockfish prefiere `Qf3`, pero ambas mantienen una posición razonable. No es una situación de única jugada.

## 3. Sacrificios y decisiones estratégicas

El criterio se alinea con el objetivo del producto:

```text
sacrificio o ruptura irreversible
→ punto de quiebre
→ detenerse
→ generar candidatas
→ analizar compensación táctica y estratégica
```

La responsabilidad puede dividirse así:

| Capa                  | Análisis                                                              |
| --------------------- | --------------------------------------------------------------------- |
| Stockfish             | Corrección táctica y evaluación objetiva                              |
| Leela Zero            | Compensación posicional, iniciativa y presión a largo plazo           |
| Features estratégicas | Rey, actividad, coordinación, espacio, estructura e iniciativa        |
| Módulo 07             | Detectar que la decisión es irreversible y merece cálculo             |
| Módulo 08             | Medir riesgo, incertidumbre, complejidad y robustez de las candidatas |

Un sacrificio que Stockfish evalúa negativamente puede clasificarse como:

```text
ObjectivelyUnsound
+ PracticalCompensation
+ HighDecisionComplexity
```

No se niega el error objetivo, pero se registra que existían compensación práctica, dificultad defensiva o presión prolongada.

A nivel aproximado de 1600, la compensación completamente posicional y decisiva a largo plazo será poco frecuente. Conviene activar el análisis profundo Stockfish/Lc0 solamente cuando existan señales previas:

- Sacrificio material.
- Ruptura de peones.
- Rey expuesto.
- Iniciativa persistente.
- Variantes con evaluaciones divergentes.
- Jugada irreversible.
- Diferencia importante entre evaluación material y evaluación del motor.

## 4. Evaluación cognitiva

No evalúa si la jugada fue buena. Intenta reconstruir cómo tomó la decisión el jugador.

| Resultado ajedrecístico                   | Hipótesis cognitiva          |
| ----------------------------------------- | ---------------------------- |
| No vio una amenaza directa                | `MISSED_THREAT`              |
| Consideró una sola jugada                 | `SINGLE_CANDIDATE`           |
| Calculó una variante demasiado corta      | `PREMATURE_CALCULATION_STOP` |
| No reconsideró tras una jugada inesperada | `FAILURE_TO_REASSESS`        |
| Sacrificó sin verificar compensación      | `UNJUSTIFIED_SACRIFICE`      |

Un nombre más preciso sería:

```text
Evaluación del proceso de decisión
```

No puede deducirse como hecho solamente mediante Stockfish. Requiere datos del jugador:

- Qué candidatas consideró.
- Qué amenaza percibió.
- Hasta dónde calculó.
- Qué evaluación subjetiva tenía.
- Cuánta confianza tenía.
- Cuánto tiempo utilizó.

El sistema puede generar una hipótesis, pero el jugador debe confirmarla o corregirla. Un entrenador fuerte valida el contenido ajedrecístico; el propio jugador valida qué pensó realmente.

## 5. Implementación y validación del módulo 07

Implementar código no implica obtener resultados validados.

| Nivel                       | Significado                                               |
| --------------------------- | --------------------------------------------------------- |
| Implementado                | Existe código ejecutable                                  |
| Testeado                    | Pasa pruebas automatizadas                                |
| Validado técnicamente       | Produce resultados reproducibles y estables               |
| Validado ajedrecísticamente | Las posiciones y candidatas coinciden con revisión humana |
| Validado cognitivamente     | El jugador confirma la hipótesis sobre su decisión        |
| Validado como producto      | La advertencia ayuda a reconocer cuándo detenerse         |

El módulo 07 completo incluye `07.7 Human validation` y `F07-038 Golden dataset`. Por tanto:

- Si “implementado” significa solamente que el código está escrito, no está validado.
- Si se completa toda la especificación, incluidos HITL, casos dorados y criterios de aceptación, sí produce un conjunto inicial validado.
- Actualmente el P0 está implementado parcialmente, pero no validado: faltan partidas completas, CI, casos dorados y revisión humana.

## 6. Resumen funcional del módulo 08

El módulo 08 recibe las evidencias del módulo 07 y las transforma en una recomendación práctica de pensamiento.

| Funcionalidad          | Resultado esperado                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------- |
| Complejidad            | Cuántas candidatas razonables existen y cuánto cálculo requieren                      |
| Incertidumbre          | Cuán estable es la evaluación entre motores, profundidades y variantes                |
| Riesgo                 | Consecuencia de equivocarse y reversibilidad de la decisión                           |
| Entropía de candidatas | Grado de dispersión entre opciones aparentemente viables                              |
| Robustez               | Si una candidata conserva su valor ante distintas respuestas                          |
| Consenso de motores    | Coincidencia o divergencia entre Stockfish y Lc0                                      |
| Navaja de Ockham       | Preferir el plan más simple cuando varias alternativas son objetivamente equivalentes |
| Valor práctico         | Dificultad defensiva, iniciativa y presión humana                                     |
| Ajuste al jugador      | Umbrales según Elo, tiempo disponible y patrones personales                           |
| Recomendación          | `seguir rápido`, `verificar`, `detenerse`, `calcular profundamente`                   |
| Presupuesto de cálculo | Qué candidatas analizar y hasta qué profundidad humana                                |
| Explicación            | Motivo concreto de la advertencia, sin lenguaje matemático innecesario                |

Flujo previsto:

```text
Módulo 07
señales + candidatas + variantes + evaluaciones
        ↓
Módulo 08
complejidad + incertidumbre + riesgo + robustez
        ↓
Advertencia al jugador
“Detenete: decisión irreversible, tres candidatas viables,
rey expuesto y alta divergencia entre variantes”
```

El módulo 08 no debe reemplazar Stockfish, Lc0 ni las reglas ajedrecísticas. Debe convertir sus evidencias en una política de pensamiento humano.

## 7. Generaciónd e ejemplos para analizar.

La mejor solución es combinar un conjunto pequeño de partidas realmente comentadas por expertos con datasets abiertos para validación masiva. No usaría las evaluaciones de Stockfish como sustituto del comentario humano: representan capas distintas.

Fuentes recomendadas
Fuente	Qué aporta	Formato/acceso	Uso recomendado
Tus libros anotados: Chernev, Kasparov, Mi sistema	Explicaciones humanas, planes, amenazas y candidatas rechazadas	Carga manual selectiva	Dataset dorado estratégico
ChessBase Mega Database	Más de 100.000 partidas anotadas, muchas por maestros y grandes maestros	Comercial; exportación PGN/CBH	Fuente más práctica a escala
Estudios públicos de Lichess	Comentarios y variantes creados por jugadores o entrenadores	PGN exportable	Casos adicionales, previa curación
Lichess Broadcasts	Partidas recientes de torneos de élite	PGN abierto	Selección de posiciones modernas
Lichess Evaluations	Varias líneas y evaluaciones profundas por posición	JSONL, CC0	Complemento objetivo y generación de candidatas
Lichess Puzzles	Posiciones tácticas, solución, dificultad y temas	CSV, CC0	Validación del pipeline táctico
PGN Mentor	Grandes colecciones de partidas magistrales	PGN gratuito	Universo de partidas, pero generalmente sin comentarios expertos

ChessBase anuncia más de 113.000 partidas anotadas en Mega Database; es probablemente la opción más directa si aceptás una fuente comercial. Conviene usar sus comentarios para investigación interna, no redistribuirlos dentro del producto. ChessBase Mega Database

Los estudios de Lichess pueden exportarse como PGN conservando comentarios y variantes. No obstante, que un estudio sea público no significa automáticamente que sus textos puedan redistribuirse: para publicar el dataset necesitarías permiso o limitarte a datos derivados y referencias. API oficial de estudios de Lichess

Los datasets propios de Lichess sí están publicados bajo CC0. Incluyen evaluaciones con varias variantes y millones de puzzles, pero no comentarios humanos equivalentes a los de un entrenador. Lichess Open Database

Estrategia concreta para ChessInsight

Crearía dos conjuntos separados:

1. expert_gold

Entre 30 y 100 posiciones extraídas de partidas comentadas por expertos. Sirve para validar si el módulo 07 reconoce correctamente cuándo había que detenerse y calcular.

Composición inicial sugerida:

| Categoría                                | Casos | Fuente posible                        |
| ---------------------------------------- | ----- | ------------------------------------- |
| Táctica o amenaza inmediata              | 10    | Chernev, Kasparov                     |
| Decisión estratégica                     | 10    | Mi sistema, partidas posicionales     |
| Única defensa o jugada                   | 10    | Partidas anotadas modernas            |
| Transformación irreversible o sacrificio | 10    | Kasparov, ChessBase, estudios curados |

Para cada posición guardaría:

``` json
{
  "fen": "...",
  "game_id": "...",
  "ply": 37,
  "critical_before_move": true,
  "stop_reason": [
    "immediate_threat",
    "irreversible_decision"
  ],
  "expert_candidates": ["Nf5", "h4", "Rfd1"],
  "expert_preferred": "Nf5",
  "rejected_candidates": [
    {
      "move": "h4",
      "reason": "debilita el rey sin generar ataque suficiente"
    }
  ],
  "expert_explanation_summary": "...",
  "source": {
    "author": "...",
    "title": "...",
    "page": 123
  },
  "rights": "private_research",
  "review_status": "confirmed"
}
```

Conviene resumir la explicación con tus palabras y conservar autor, libro y página, en vez de copiar párrafos completos.

2. engine_scale

Miles de posiciones provenientes de Lichess para comprobar estabilidad técnica:

MultiPV y diferencia entre candidatas.
Coincidencia entre Stockfish y Leela.
Única jugada.
Estabilidad por profundidad o nodos.
Motivos tácticos.
Dificultad y deduplicación.

Este conjunto valida el motor y el pipeline, pero no demuestra por sí mismo que un humano debía reconocer la posición como crítica.

Cómo extraer candidatas del PGN

En una partida anotada, el parser debe distinguir:

La jugada principal.
Las variantes entre paréntesis: candidatas analizadas.
Los comentarios {...}.
Símbolos !, ?, !?, ?! y NAG.
Comentario antes de la jugada: señal preventiva.
Comentario después de la jugada: evaluación retrospectiva.

Una posición merece revisión como posible caso dorado cuando aparece alguno de estos indicadores:

Dos o más variantes alternativas.
“La posición crítica”, “había que calcular”, “única jugada”.
“La amenaza es…”, “era necesario…”, “mejor era…”.
Sacrificio, ruptura de peones o cambio estructural irreversible.
Elección entre planes distintos, aunque la evaluación inmediata sea parecida.

El flujo quedaría:

PGN anotado
→ comentarios y variantes
→ posiciones candidatas
→ revisión manual
→ Stockfish + Leela
→ separación experto/motor
→ expert_gold.jsonl
Punto importante de validación

Si el experto recomienda una candidata y Stockfish o Leela prefiere otra, no hay que sobrescribir ninguna. Guardá las tres perspectivas:

Capa	Pregunta
Experto	¿Qué debía comprender y calcular el jugador?
Stockfish	¿Cuál es el resultado objetivo de las variantes?
Leela	¿Qué compensación y ventaja posicional de largo plazo aparece?

Así, el módulo 07 se valida contra el reconocimiento humano de la decisión crítica, mientras Stockfish y Leela validan las consecuencias. Ese desacuerdo puede ser uno de los casos más valiosos para el módulo 08.