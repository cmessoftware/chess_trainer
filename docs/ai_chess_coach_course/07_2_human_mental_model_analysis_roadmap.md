# Plan de implementación — ChessInsight Módulo 07

## Objetivo

Implementar y validar progresivamente el siguiente flujo:

PGN
→ posiciones críticas
→ jugadas candidatas
→ comparación con la jugada realizada
→ diagnóstico estructurado
→ validación humana
→ patrones longitudinales
→ explicación pedagógica

El código actual de analysis/mental_model/ se considera un prototipo descartable. Puede modificarse o reemplazarse por completo.

Principios

- Implementar una capacidad verificable por vez.
- Probar cada feature con partidas reales en formato PGN.
- Mantener separadas evidencia, inferencia y confirmación humana.
- No usar el LLM para decidir evaluaciones ajedrecísticas.
- No avanzar con UI, API, RAG o Lc0 hasta validar el núcleo.
- Usar contratos estructurados antes de generar explicaciones textuales.
- Agregar casos reales al golden dataset para evitar regresiones.

1. División del módulo


| Submódulo | Responsabilidad             | Entregable                                         |
| --------- | --------------------------- | -------------------------------------------------- |
| 07.0      | Infraestructura de análisis | PGN convertido en posiciones y análisis Stockfish  |
| 07.1      | Posiciones críticas         | Lista priorizada de posiciones críticas            |
| 07.2      | Jugadas candidatas          | MultiPV y clasificación de candidatas              |
| 07.3      | Evaluación de la decisión   | Comparación entre jugada real y candidatas         |
| 07.4      | Diagnóstico ajedrecístico   | Tipo de decisión y causa probable del error        |
| 07.5      | Secuencias subóptimas       | Agrupación de decisiones relacionadas              |
| 07.6      | Patrones del jugador        | Tendencias sobre múltiples partidas                |
| 07.7      | Validación humana           | Confirmación, corrección o rechazo del diagnóstico |
| 07.8      | Explicación pedagógica      | Informe determinista y verbalización mediante LLM  |


1. Catálogo de features

07.0 — PGN e infraestructura de análisis


| ID      | Feature                         | Entrada                       | Salida verificable                                   | Prueba con PGN real                                    | Prioridad |
| ------- | ------------------------------- | ----------------------------- | ---------------------------------------------------- | ------------------------------------------------------ | --------- |
| F07-001 | Importación de partida          | Archivo o texto PGN           | Partida normalizada con movimientos, FEN y metadatos | Reconstruir todas las posiciones de una partida propia | P0        |
| F07-002 | Selección del jugador           | PGN y username o color        | Movimientos atribuibles al jugador analizado         | Probar una partida con blancas y otra con negras       | P0        |
| F07-003 | Análisis Stockfish por posición | FEN                           | Evaluación antes y después de la jugada              | Comparar con una partida analizada en Lichess          | P0        |
| F07-004 | Normalización de evaluación     | Score del motor               | Evaluación desde la perspectiva del jugador          | Probar cambios de turno y posiciones de mate           | P0        |
| F07-005 | Pérdida de evaluación           | Evaluación previa y posterior | eval_loss o cp_loss                                  | Detectar una jugada conocida como error                | PO        |


