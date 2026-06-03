# Proposal: phase-01-core-engine-minimal-api-baseline

## Summary

Establecer una especificacion OpenSpec para Phase 1 (`core-engine + minimal api`) que documente:

- lo ya implementado (baseline real),
- las brechas pendientes,
- y el plan de cierre para `01-FEAT-1` a `01-FEAT-4`.

## Problem

El roadmap de Phase 1 define cuatro features en estado `Proposal/Pending`, pero el codigo ya contiene una parte relevante implementada (API base y endpoints PGN). Falta trazabilidad formal entre estado real y backlog pendiente.

## Scope

- Contratos API base existentes y contratos PGN requeridos.
- Estado de pipeline de analisis minimo para Phase 1.
- Validacion de entradas PGN para casos basicos y casos invalidos.
- Cobertura de pruebas para endpoints base.

## Out of Scope

- Evolucion de LLM reports avanzados.
- Optimizaciones de performance y persistencia distribuida de jobs.
- Refactor mayor de arquitectura fuera de Phase 1.

## Current Baseline (Observed)

- API FastAPI unificada en operacion con routers montados.
- Endpoints de upload/import PGN funcionales con validacion basica de extension.
- Contratos tipados existentes para juegos/analisis generales.
- Estado de jobs PGN en memoria (no persistente).

## Pending Gaps

- Contratos tipados dedicados para flujos PGN (request/response/status).
- Criterios de cierre para pipeline minimo de analisis de Phase 1.
- Validacion de contenido PGN mas robusta (no solo extension).
- Pruebas automatizadas orientadas al flujo base de PGN/API.

## Success Criteria

1. `01-FEAT-1` tiene contratos PGN/API base formalizados y versionables.
2. `01-FEAT-2` define pipeline minimo estable y verificable.
3. `01-FEAT-3` cubre validaciones de entrada invalidas y bordes.
4. `01-FEAT-4` agrega pruebas base automatizadas para endpoints clave.
